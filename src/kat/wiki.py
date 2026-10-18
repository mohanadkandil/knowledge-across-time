"""Version-pinned Kaggle Wikipedia lookup using bounded HTTP range reads.

Only article identity columns are indexed. Full article content is fetched from the
matching row group on demand. No Hugging Face/current-Wikipedia substitutions.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import pyarrow.parquet as pq

DATASET = "wikimedia-foundation/wikipedia-structured-contents"
VERSION = 5
API = "https://www.kaggle.com/api/v1/datasets"
MANIFEST_URL = f"{API}/list/{DATASET}?datasetVersionNumber={VERSION}&pageSize=200"
IDENTITY_COLUMNS = ["name", "identifier", "url"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=_json_default, separators=(",", ":")).encode()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_canonical(value))
    temporary.replace(path)


class RangeReadError(OSError):
    """The origin did not honor the exact, bounded byte-range contract."""


class HTTPRangeFile(io.RawIOBase):
    """Seekable, independently owned HTTP client for PyArrow.

    The response is checked before consuming its body. HTTP 200 is refused even
    if it advertises a small body: a server ignoring Range must never cause a
    whole Wikipedia shard to be downloaded accidentally.
    """

    def __init__(self, url: str, size: int, *, timeout: float = 20.0,
                 retries: int = 2, max_bytes: int = 32 * 1024 * 1024,
                 client: Any = None):
        super().__init__()
        self.source_url = url
        self.size = int(size)
        if self.size <= 0:
            raise ValueError("A positive manifest file size is required")
        self._pos = 0
        self.bytes_read = 0
        self.request_count = 0
        self.max_bytes = max_bytes
        self.retries = retries
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None
        self._resolved_url: str | None = None
        self.origin_etag: str | None = None
        self.origin_hashes: str | None = None
        self._footer_cache: tuple[int, bytes] | None = None

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        pos = offset if whence == io.SEEK_SET else self._pos + offset if whence == io.SEEK_CUR else self.size + offset if whence == io.SEEK_END else None
        if pos is None or pos < 0:
            raise ValueError("Invalid seek")
        self._pos = pos
        return pos

    def _range(self, start: int, end: int) -> bytes:
        length = end - start + 1
        if self.bytes_read + length > self.max_bytes:
            raise RangeReadError(f"Range budget exceeded ({self.max_bytes} bytes)")
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                url = self._resolved_url or self.source_url
                with self._client.stream("GET", url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}) as response:
                    self.request_count += 1
                    if response.status_code in (401, 403) and self._resolved_url:
                        # Expired signed redirect: obtain a fresh one from Kaggle.
                        self._resolved_url = None
                        raise RangeReadError("Signed download URL expired")
                    if response.status_code != 206:
                        raise RangeReadError(f"Range request requires HTTP 206; got {response.status_code}")
                    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                    if not match or tuple(map(int, match.groups())) != (start, end, self.size):
                        raise RangeReadError("Content-Range does not match requested range and manifest size")
                    etag = response.headers.get("ETag")
                    if self.origin_etag and etag and self.origin_etag != etag:
                        raise RangeReadError("Origin ETag changed during range reading")
                    if etag:
                        self.origin_etag = etag
                    self.origin_hashes = response.headers.get("x-goog-hash") or self.origin_hashes
                    declared = response.headers.get("Content-Length")
                    if declared is not None and int(declared) != length:
                        raise RangeReadError("Unexpected range Content-Length")
                    chunks, received = [], 0
                    for chunk in response.iter_raw():
                        received += len(chunk)
                        self.bytes_read += len(chunk)
                        if received > length or self.bytes_read > self.max_bytes:
                            raise RangeReadError("Server exceeded requested byte range")
                        chunks.append(chunk)
                    if received != length:
                        raise RangeReadError("Truncated range response")
                    # Keep signed URLs only in process memory, never provenance/logs.
                    self._resolved_url = str(response.url)
                    return b"".join(chunks)
            except (httpx.HTTPError, RangeReadError, ValueError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.25 * (attempt + 1))
        # Exception text from HTTP clients may contain signed URLs; sanitize it.
        raise RangeReadError(f"Unable to fetch byte range {start}-{end}: {type(last_error).__name__}") from None

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("I/O operation on closed range file")
        remaining = max(0, self.size - self._pos)
        size = remaining if size is None or size < 0 else min(size, remaining)
        if size == 0:
            return b""
        start, end = self._pos, self._pos + size - 1
        cached = self._footer_cache
        if cached and start >= cached[0] and end < cached[0] + len(cached[1]):
            data = cached[1][start-cached[0]:end-cached[0]+1]
        else:
            chunks = []
            for pos in range(start, end + 1, 8 * 1024 * 1024):
                chunks.append(self._range(pos, min(end, pos + 8 * 1024 * 1024 - 1)))
            data = b"".join(chunks)
            if end == self.size - 1 and len(data) <= 2 * 1024 * 1024:
                self._footer_cache = (start, data)
        self._pos += len(data)
        return data

    def readinto(self, buffer: Any) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def close(self) -> None:
        if not self.closed and self._owns_client:
            self._client.close()
        super().close()


def flatten_sections(sections: Any) -> list[dict[str, Any]]:
    """Flatten recursive parts while retaining citation objects and source paths."""
    if isinstance(sections, str):
        sections = json.loads(sections) if sections else []
    output: list[dict[str, Any]] = []

    def visit(node: Any, path: str, headings: list[str]) -> None:
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]", headings)
        elif isinstance(node, dict):
            name = node.get("name")
            next_headings = headings + [str(name)] if name else headings
            value = node.get("value")
            values = node.get("values")
            text_parts = []
            if isinstance(value, str):
                text_parts.append(value)
            if isinstance(values, list):
                text_parts.extend(str(v) for v in values if isinstance(v, (str, int, float)))
            if text_parts:
                output.append({"path": path, "headings": next_headings,
                               "type": node.get("type"), "text": "\n".join(text_parts),
                               "citations": node.get("citations") or [],
                               "links": node.get("links") or [],
                               "table_references": node.get("table_references") or []})
            if "has_parts" in node:
                visit(node["has_parts"], path + ".has_parts", next_headings)
    visit(sections, "sections", [])
    return output


class WikiCorpus:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "wikipedia.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=60)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=60000")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS shards(
                    path TEXT PRIMARY KEY, size INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                    rows INTEGER, bytes_read INTEGER, title_digest TEXT, scanned_at TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS articles(
                    id INTEGER PRIMARY KEY, article_id INTEGER NOT NULL, name TEXT NOT NULL, url TEXT,
                    shard TEXT NOT NULL, row_index INTEGER NOT NULL, revision_id INTEGER,
                    UNIQUE(shard, row_index));
                CREATE INDEX IF NOT EXISTS articles_title ON articles(name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS articles_identifier ON articles(article_id);
                CREATE VIRTUAL TABLE IF NOT EXISTS article_fts USING fts5(name, content='articles', content_rowid='id');
                CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
                    INSERT INTO article_fts(rowid,name) VALUES(new.id,new.name); END;
                CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
                    INSERT INTO article_fts(article_fts,rowid,name) VALUES('delete',old.id,old.name); END;
                CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
                    INSERT INTO article_fts(article_fts,rowid,name) VALUES('delete',old.id,old.name);
                    INSERT INTO article_fts(rowid,name) VALUES(new.id,new.name); END;
            """)
            expected = f"{DATASET}@{VERSION}"
            row = db.execute("SELECT value FROM metadata WHERE key='dataset'").fetchone()
            if row and row[0] != expected:
                raise ValueError("Corpus directory belongs to a different dataset version")
            db.execute("INSERT OR IGNORE INTO metadata VALUES('dataset', ?)", (expected,))

    @staticmethod
    def _download_url(path: str) -> str:
        return f"{API}/download/{DATASET}/{quote(path, safe='')}?datasetVersionNumber={VERSION}&raw=true"

    def _manifest(self, url: str) -> list[dict[str, Any]]:
        if "datasetVersionNumber=5" not in url:
            raise ValueError("Manifest URL must explicitly pin datasetVersionNumber=5")
        cache = self.root / "manifest-v5.json"
        if cache.exists():
            payload = json.loads(cache.read_text())
            return payload["files"] if isinstance(payload, dict) else payload
        files = []
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            base = url
            while url:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
                files.extend(payload.get("datasetFiles", []))
                token = payload.get("nextPageToken") or payload.get("nextPageTokenNullable")
                url = base + "&pageToken=" + quote(token, safe="") if token else None
        _write_json(cache, {"dataset": DATASET, "version": VERSION, "retrieved_at": _now(),
                            "manifest_url": base, "files": files})
        return files

    def _scan(self, entry: dict[str, Any]) -> tuple[list[tuple[Any, ...]], dict[str, Any]]:
        path, size = entry["name"], int(entry["totalBytes"])
        with HTTPRangeFile(self._download_url(path), size) as remote:
            parquet = pq.ParquetFile(remote)
            identities = parquet.read(columns=IDENTITY_COLUMNS).to_pylist()
            rows = [(int(row["identifier"]), row["name"], row.get("url"), path, index)
                    for index, row in enumerate(identities) if row.get("identifier") is not None and row.get("name")]
            stats = {"rows": len(identities), "bytes_read": remote.bytes_read,
                     "title_digest": hashlib.sha256(_canonical(identities)).hexdigest(), "scanned_at": _now()}
        return rows, stats

    def build_catalog(self, manifest_url: str = MANIFEST_URL, workers: int = 3,
                      shard_limit: int | None = None) -> dict[str, Any]:
        """Resume title/ID/URL indexing; each completed shard commits atomically.

        Failed shards remain retryable. If interrupted, pending futures may finish
        networking, but only committed status='complete' shards are skipped later.
        """
        if not 1 <= workers <= 8:
            raise ValueError("Use 1–8 workers; three is the recommended default")
        entries = [e for e in self._manifest(manifest_url)
                   if e.get("name", "").startswith("enwiki/data/") and e["name"].endswith(".parquet")]
        expected_shards = len(entries)
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO metadata VALUES('expected_english_shards', ?)", (str(expected_shards),))
        if shard_limit is not None:
            if shard_limit < 0:
                raise ValueError("shard_limit must be nonnegative")
            entries = entries[:shard_limit]
        with self._connect() as db:
            for e in entries:
                db.execute("INSERT OR IGNORE INTO shards(path,size) VALUES(?,?)", (e["name"], int(e["totalBytes"])))
                old = db.execute("SELECT size FROM shards WHERE path=?", (e["name"],)).fetchone()
                if old[0] != int(e["totalBytes"]):
                    raise ValueError("Pinned manifest size changed; use a new corpus directory")
            complete = {r[0] for r in db.execute("SELECT path FROM shards WHERE status='complete'")}
        pending = [e for e in entries if e["name"] not in complete]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._scan, entry): entry for entry in pending}
            for future in as_completed(futures):
                entry = futures[future]
                try:
                    rows, stats = future.result()
                    with self._connect() as db:
                        db.execute("DELETE FROM articles WHERE shard=?", (entry["name"],))
                        db.executemany("INSERT INTO articles(article_id,name,url,shard,row_index) VALUES(?,?,?,?,?)", rows)
                        db.execute("UPDATE shards SET status='complete',rows=?,bytes_read=?,title_digest=?,scanned_at=?,error=NULL WHERE path=?",
                                   (stats["rows"], stats["bytes_read"], stats["title_digest"], stats["scanned_at"], entry["name"]))
                except Exception as exc:
                    with self._connect() as db:
                        db.execute("UPDATE shards SET status='failed',error=?,scanned_at=? WHERE path=?",
                                   (f"{type(exc).__name__}: {exc}"[:300], _now(), entry["name"]))
                # Live status survives crashes; do not wait for all files to finish.
                _write_json(self.root / "catalog-status.json", self.stats())
        return self.stats()

    def stats(self) -> dict[str, Any]:
        with self._connect() as db:
            groups = {row[0]: row[1] for row in db.execute("SELECT status,count(*) FROM shards GROUP BY status")}
            total = db.execute("SELECT count(*) FROM articles").fetchone()[0]
            transferred = db.execute("SELECT coalesce(sum(bytes_read),0) FROM shards WHERE status='complete'").fetchone()[0]
            row = db.execute("SELECT value FROM metadata WHERE key='expected_english_shards'").fetchone()
            expected = int(row[0]) if row else None
        if expected is None and (self.root / "manifest-v5.json").exists():
            payload = json.loads((self.root / "manifest-v5.json").read_text())
            files = payload.get("files", []) if isinstance(payload, dict) else payload
            expected = sum(e.get("name", "").startswith("enwiki/data/") and e["name"].endswith(".parquet") for e in files)
        return {"dataset": DATASET, "version": VERSION, "articles_indexed": total,
                "shards": groups, "expected_english_shards": expected,
                "catalog_complete": bool(expected) and groups.get("complete", 0) == expected and not groups.get("failed", 0),
                "committed_range_bytes": transferred, "updated_at": _now()}

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query = query.strip()
        if not query or limit <= 0:
            return []
        limit = min(limit, 100)
        fields = "article_id,name,url,shard,row_index,revision_id"
        with self._connect() as db:
            exact = db.execute(f"SELECT {fields} FROM articles WHERE name=? COLLATE NOCASE ORDER BY article_id LIMIT ?", (query, limit)).fetchall()
            result = [dict(row) for row in exact]
            tokens = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
            if tokens and len(result) < limit:
                match = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)
                found = db.execute(f"SELECT {','.join('a.'+f for f in fields.split(','))} FROM article_fts f JOIN articles a ON a.id=f.rowid WHERE article_fts MATCH ? ORDER BY bm25(article_fts) LIMIT ?", (match, limit * 2)).fetchall()
                seen = {(r["shard"], r["row_index"]) for r in result}
                for row in found:
                    candidate = dict(row)
                    key = (candidate["shard"], candidate["row_index"])
                    if key not in seen:
                        result.append(candidate)
                        seen.add(key)
                    if len(result) >= limit:
                        break
        return result

    def fetch(self, candidate: dict[str, Any]) -> dict[str, Any]:
        path, index = str(candidate["shard"]), int(candidate["row_index"])
        if not re.fullmatch(r"enwiki/data/enwiki_namespace_0_\d+\.parquet", path) or index < 0:
            raise ValueError("Invalid exact-corpus candidate")
        key = hashlib.sha256(f"{VERSION}:{path}:{index}".encode()).hexdigest()
        cached = self.root / "articles" / f"{key}.json"
        if cached.exists():
            result = json.loads(cached.read_text())
            if candidate.get("article_id") is not None and int(result["article"]["identifier"]) != int(candidate["article_id"]):
                raise ValueError("Cached article does not match candidate identity")
            return result
        with self._connect() as db:
            entry = db.execute("SELECT size FROM shards WHERE path=?", (path,)).fetchone()
        if entry is None:
            files = self._manifest(MANIFEST_URL)
            item = next((e for e in files if e.get("name") == path), None)
            if item is None:
                raise ValueError("Candidate shard is not in the pinned manifest")
            size = int(item["totalBytes"])
        else:
            size = int(entry[0])
        with HTTPRangeFile(self._download_url(path), size, max_bytes=256 * 1024 * 1024) as remote:
            parquet = pq.ParquetFile(remote)
            if index >= parquet.metadata.num_rows:
                raise ValueError("Candidate row outside shard")
            offset = 0
            article = None
            for group in range(parquet.metadata.num_row_groups):
                count = parquet.metadata.row_group(group).num_rows
                if offset <= index < offset + count:
                    article = parquet.read_row_group(group).slice(index-offset, 1).to_pylist()[0]
                    # Keep cache hits and first fetches JSON-compatible and identical.
                    article = json.loads(_canonical(article))
                    break
                offset += count
            if article is None:
                raise ValueError("Article row unavailable")
            if candidate.get("article_id") is not None and int(article["identifier"]) != int(candidate["article_id"]):
                raise ValueError("Fetched article does not match candidate identity")
            provenance = {"dataset": DATASET, "dataset_version": VERSION, "source_file": path,
                          "source_file_bytes": size, "row_index": index, "article_id": article["identifier"],
                          "revision_id": (article.get("version") or {}).get("identifier"),
                          "retrieved_at": _now(), "download_url": self._download_url(path),
                          "article_sha256": hashlib.sha256(_canonical(article)).hexdigest(),
                          "shard_sha256": None, "origin_etag": getattr(remote, "origin_etag", None),
                          "origin_hashes": getattr(remote, "origin_hashes", None), "range_bytes": remote.bytes_read}
        result = {"article": article, "sections": flatten_sections(article.get("sections")),
                  "references": article.get("references") or [], "provenance": provenance}
        _write_json(cached, result)
        with self._connect() as db:
            db.execute("UPDATE articles SET revision_id=? WHERE shard=? AND row_index=?", (provenance["revision_id"], path, index))
        return result
