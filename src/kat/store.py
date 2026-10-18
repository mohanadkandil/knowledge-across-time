"""Local source registry, LanceDB vectors and immutable run evidence."""
import json
import math
import re
import sqlite3
from pathlib import Path

import lancedb
import pyarrow as pa

from .util import digest, load_json, now, write_json


class Store:
    def __init__(self, root: Path):
        self.root = root; root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "sources.sqlite3"
        with self.connection() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,kind TEXT NOT NULL,page_id TEXT,title TEXT,text TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(id UNINDEXED,title,text);
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);""")

    def connection(self):
        db = sqlite3.connect(self.db_path, timeout=60); db.row_factory = sqlite3.Row
        return db

    def put_sources(self, sources: list[dict]):
        with self.connection() as db:
            for source in sources:
                db.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)", (source["id"],source["kind"],source.get("page_id"),source.get("title",""),source["text"],json.dumps(source)))
                db.execute("DELETE FROM source_fts WHERE id=?", (source["id"],))
                db.execute("INSERT INTO source_fts VALUES(?,?,?)", (source["id"],source.get("title",""),source["text"]))

    def source(self, source_id: str) -> dict:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM sources WHERE id=?", (source_id,)).fetchone()
        if row is None:
            raise KeyError("Unknown source ID")
        return json.loads(row[0])

    def page_sources(self, page_id: str) -> list[dict]:
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM sources WHERE page_id=? ORDER BY id", (page_id,))]

    def sources(self, limit=1000) -> list[dict]:
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM sources ORDER BY id LIMIT ?", (limit,))]

    def indexed(self, fingerprint: str) -> bool:
        with self.connection() as db:
            return db.execute("SELECT 1 FROM meta WHERE key=?", ("indexed:"+fingerprint,)).fetchone() is not None

    def mark_indexed(self, fingerprint: str):
        # Called only after every LanceDB upsert in the batch succeeds.
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("indexed:"+fingerprint,now()))

    def delete_page_sources(self, page_id: str):
        with self.connection() as db:
            ids=[r[0] for r in db.execute("SELECT id FROM sources WHERE page_id=?", (page_id,))]
            for source_id in ids:
                db.execute("DELETE FROM source_fts WHERE id=?", (source_id,))
            db.execute("DELETE FROM sources WHERE page_id=?", (page_id,))
            # Invalidating completion markers is conservative and cheap; vectors for
            # other pages remain, but cannot incorrectly certify a removed source.
            db.execute("DELETE FROM meta WHERE key LIKE 'indexed:%'")
        connection=lancedb.connect(self.root/"lance")
        if ids and "evidence" in connection.table_names():
            connection.open_table("evidence").delete("id IN ("+",".join("'"+s.replace("'","''")+"'" for s in ids)+")")

    def vector_upsert(self, sources: list[dict], vectors: list[list[float]], model: str):
        if not sources or len(sources) != len(vectors):
            raise ValueError("Each source must have one embedding")
        dim = len(vectors[0])
        if not dim or not model or any(len(v)!=dim or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in v) for v in vectors):
            raise ValueError("Embedding vectors must be finite, nonempty and have matching dimensions and a model identity")
        identity = json.dumps({"model": model, "dimensions": dim}, sort_keys=True)
        with self.connection() as db:
            old = db.execute("SELECT value FROM meta WHERE key='embedding_identity'").fetchone()
            if old and old[0] != identity:
                raise ValueError("Embedding model/dimensions changed; use a new data directory or explicitly rebuild the index")
            db.execute("INSERT OR IGNORE INTO meta VALUES('embedding_identity',?)", (identity,))
        records = [{"id": s["id"], "kind": s["kind"], "text": s["text"], "vector": v} for s,v in zip(sources,vectors)]
        connection = lancedb.connect(self.root / "lance")
        if "evidence" not in connection.table_names():
            schema = pa.schema([pa.field("id",pa.string()),pa.field("kind",pa.string()),pa.field("text",pa.string()),pa.field("vector",pa.list_(pa.float32(),dim))])
            connection.create_table("evidence", data=records, schema=schema)
        else:
            table = connection.open_table("evidence")
            table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(records)

    def vector_search(self, vector: list[float], model: str, limit=20, kind: str | None=None, source_ids: list[str] | None=None):
        if source_ids == []:
            return []
        with self.connection() as db:
            old = db.execute("SELECT value FROM meta WHERE key='embedding_identity'").fetchone()
        if not old:
            raise ValueError("LanceDB has no evidence vectors; parse and index sources first")
        if json.loads(old[0]) != {"model": model,"dimensions": len(vector)}:
            raise ValueError("Query embedding identity does not match the evidence index")
        table = lancedb.connect(self.root / "lance").open_table("evidence")
        query = table.search(vector).distance_type("cosine")
        if kind:
            if kind not in {"britannica","wikipedia"}:
                raise ValueError("Unknown source kind")
            query = query.where(f"kind = '{kind}'")
        if source_ids is not None:
            terms=",".join("'"+source_id.replace("'","''")+"'" for source_id in source_ids)
            condition="id IN ("+terms+")"
            if kind:condition=f"kind = '{kind}' AND "+condition
            query=query.where(condition,prefilter=True)
        return [{**self.source(r["id"]), "distance": r.get("_distance")} for r in query.limit(limit).to_list()]

    def stats(self):
        with self.connection() as db:
            return {"sources":dict(db.execute("SELECT kind,count(*) FROM sources GROUP BY kind").fetchall()),
                    "embedding_identity": json.loads(row[0]) if (row:=db.execute("SELECT value FROM meta WHERE key='embedding_identity'").fetchone()) else None}

    def save_run(self, run: dict):
        self._validate_run_id(run["run_id"])
        write_json(self.root / "runs" / run["run_id"] / "run.json", run)

    @staticmethod
    def _validate_run_id(run_id: str):
        if not isinstance(run_id,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,120}",run_id):
            raise ValueError("Invalid run ID")

    @staticmethod
    def _reviewable(run: dict):
        result=run.get("result") or {}
        return (run.get("kind")=="question" and run.get("execution")=="live_models" and run.get("status")=="complete"
                and result.get("framework")=="hermes" and result.get("completed") is True
                and bool(str(result.get("answer","")).strip()) and not result.get("error") and not run.get("error"))

    def runs(self):
        return sorted([load_json(p) for p in (self.root / "runs").glob("*/run.json")], key=lambda r:r.get("created_at",""), reverse=True)

    def review(self, run_id: str, outcome: str, rationale: str, expected: str, category: str, reviewer: str):
        self._validate_run_id(run_id)
        path = self.root / "runs" / run_id / "run.json"
        run = load_json(path)
        if not run:
            raise KeyError("Run does not exist")
        if not self._reviewable(run):
            raise ValueError("Only a completed live Hermes question with an answer can be counted as an agent success/failure case; infrastructure errors and comparison-only runs are excluded")
        if outcome not in {"success","failure"} or not rationale.strip() or not expected.strip() or not reviewer.strip():
            raise ValueError("Outcome, human rationale, expected behavior and reviewer are required")
        if outcome == "failure" and not category.strip():
            raise ValueError("Failure category is required")
        review = {"outcome":outcome,"rationale":rationale,"expected_behavior":expected,"category":category,"reviewer":reviewer,"reviewed_at":now(),
                  "run_sha256":digest(json.dumps(run,sort_keys=True,ensure_ascii=False,default=str))}
        write_json(path.parent / "review.json", review)
        return review

    def cases(self):
        rows = []
        for run in self.runs():
            review = load_json(self.root / "runs" / run["run_id"] / "review.json")
            run_hash=digest(json.dumps(run,sort_keys=True,ensure_ascii=False,default=str))
            if review and self._reviewable(run) and review.get("run_sha256")==run_hash:
                rows.append({"run_id":run["run_id"],"question":run.get("question"),"page_id":run.get("page_id"),"review":review})
        return {"cases":rows,"successes":sum(r["review"]["outcome"]=="success" for r in rows),"failures":sum(r["review"]["outcome"]=="failure" for r in rows)}
