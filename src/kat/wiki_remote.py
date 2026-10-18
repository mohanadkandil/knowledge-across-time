"""Organizer-provided, revision-pinned Wikipedia BM25 API.

This is the sanctioned shared HF snapshot index, not a byte-identical Kaggle
mirror. Full paginated UTF-8 text is checksum-verified before caching. The API
exposes flattened text, so original section/reference structure is not invented.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

from .util import load_json, now, write_json

DEFAULT_BASE_URL = "https://port8000-rks0xavparpzq59.tunnel.applications.uk-south2.nebius.cloud"
DATASET = "wikimedia/structured-wikipedia"
REVISION = "417c267bb457fa645c22eb3b5c77764963194c70"


class WikipediaServiceError(RuntimeError):
    pass


class WikipediaProtocolError(WikipediaServiceError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WikipediaProtocolError(message)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class RemoteWikiCorpus:
    def __init__(self, root: Path, base_url: str = DEFAULT_BASE_URL, *, client: httpx.Client | None = None,
                 timeout: float = 25, retries: int = 2):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        if not self.base_url.startswith(("https://", "http://")):
            raise ValueError("Wikipedia API base URL must be HTTP(S)")
        self.client = client or httpx.Client(timeout=timeout, follow_redirects=False,
                                           limits=httpx.Limits(max_connections=3, max_keepalive_connections=3))
        self._owned = client is None
        self.retries = retries
        self._verified_at = 0.0
        self._corpus: dict[str, Any] | None = None

    def close(self) -> None:
        if self._owned:
            self.client.close()

    def _request(self, method: str, path: str, *, payload=None, params=None) -> dict:
        for attempt in range(self.retries + 1):
            try:
                with self.client.stream(method, self.base_url + path, json=payload, params=params,
                                        headers={"Accept": "application/json"}) as response:
                    if response.status_code in {429, 503}:
                        if attempt >= self.retries:
                            raise WikipediaServiceError(f"Shared Wikipedia service busy (HTTP {response.status_code})")
                        delay = 0.5 * (attempt + 1)
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                try:
                                    delay = max(0., (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds())
                                except (ValueError, TypeError):
                                    pass
                        if not math.isfinite(delay) or delay > 30:
                            raise WikipediaServiceError("Retry-After exceeds bounded wait; retry later")
                        time.sleep(max(0., delay))
                        continue
                    if response.status_code != 200:
                        raise WikipediaServiceError(f"Shared Wikipedia service returned HTTP {response.status_code}")
                    blocks, size = [], 0
                    for block in response.iter_bytes():
                        size += len(block)
                        if size > 4 * 1024 * 1024:
                            raise WikipediaProtocolError("Wikipedia response exceeded the 4 MiB limit")
                        blocks.append(block)
                    result = json.loads(b"".join(blocks))
                    _require(isinstance(result, dict) and "error" not in result, "Wikipedia response is not a successful object")
                    return result
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= self.retries:
                    raise WikipediaServiceError("Shared Wikipedia connection failed or timed out") from None
                time.sleep(0.25 * (attempt + 1))
            except (json.JSONDecodeError, UnicodeError):
                raise WikipediaProtocolError("Wikipedia response is not valid JSON") from None
        raise WikipediaServiceError("Wikipedia retry budget exhausted")

    def _verify(self) -> dict:
        if self._corpus is not None and time.monotonic() - self._verified_at < 60:
            return self._corpus
        ready = self._request("GET", "/ready")
        _require(ready.get("status") == "ready" and ready.get("production") is True,
                 "Shared Wikipedia index is not production-ready")
        corpus = self._request("GET", "/v1/corpus")
        _require(corpus.get("dataset") == DATASET and corpus.get("dataset_revision") == REVISION,
                 "Shared Wikipedia dataset/revision differs from organizer contract")
        proof = corpus.get("verification", {})
        expected = {"production": True, "raw_rows": 7_597_149, "canonical_articles": 7_182_883,
                    "source_shards": 86, "fts_indexed_rows": 7_182_883, "fts_unindexed_rows": 0}
        _require(all(proof.get(k) == value for k, value in expected.items()), "Shared Wikipedia coverage proof differs")
        _require(ready.get("dataset_revision") == REVISION, "Readiness snapshot differs")
        _require(corpus.get("license", {}).get("spdx") == "CC-BY-SA-4.0", "Shared Wikipedia license missing")
        self._corpus, self._verified_at = corpus, time.monotonic()
        write_json(self.root / "shared-corpus.json", {"retrieved_at": now(), "service_url": self.base_url,
                                                       "ready": ready, "corpus": corpus})
        return corpus

    @staticmethod
    def _source(row: dict) -> dict:
        _require(isinstance(row, dict), "Wikipedia article/hit is not an object")
        _require(isinstance(row.get("page_id"), str) and re.fullmatch(r"[0-9]{1,20}", row["page_id"]) is not None,
                 "Wikipedia page ID invalid")
        _require(isinstance(row.get("revision_id"), str) and row["revision_id"].isdigit(), "Wikipedia revision ID invalid")
        _require(isinstance(row.get("title"), str) and bool(row["title"].strip()), "Wikipedia title missing")
        _require(isinstance(row.get("url"), str) and row["url"].startswith("https://"), "Wikipedia source URL missing")
        provenance = row.get("provenance")
        _require(isinstance(provenance, dict), "Wikipedia source provenance missing")
        _require(provenance.get("dataset") == DATASET and provenance.get("dataset_revision") == REVISION,
                 "Wikipedia source dataset/revision differs")
        _require(isinstance(provenance.get("text_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", provenance["text_sha256"]) is not None,
                 "Wikipedia complete-text checksum missing")
        _require(_integer(provenance.get("source_row_idx")) and provenance["source_row_idx"] >= 0,
                 "Wikipedia source row invalid")
        _require(all(isinstance(provenance.get(k), str) and provenance[k] for k in ("source_key", "extraction", "revision_url")),
                 "Wikipedia source coordinates/extraction missing")
        _require(row.get("license", {}).get("spdx") == "CC-BY-SA-4.0", "Wikipedia article license missing")
        return provenance

    def search(self, query: str, limit: int = 10) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        if len(query) > 512 or len(query.split()) > 64 or not _integer(limit) or not 1 <= limit <= 100:
            raise ValueError("Search accepts 1–512 characters, at most64 words, and limit1–100")
        self._verify()
        result = self._request("POST", "/v1/search", payload={"query": query, "top_k": limit, "excerpt_chars": 1000})
        hits = result.get("hits")
        _require(result.get("corpus_revision") == REVISION and result.get("retrieval") == "lexical_bm25",
                 "Wikipedia search corpus/method differs")
        _require(isinstance(hits, list) and result.get("count") == len(hits) and len(hits) <= limit,
                 "Wikipedia search result count invalid")
        candidates, seen = [], set()
        for hit in hits:
            provenance = self._source(hit)
            _require(hit["page_id"] not in seen, "Wikipedia search repeated a page ID")
            seen.add(hit["page_id"])
            _require(isinstance(hit.get("excerpt"), str) and len(hit["excerpt"]) <= 1000, "Wikipedia excerpt invalid")
            _require(_integer(hit.get("excerpt_offset")) and hit["excerpt_offset"] >= 0, "Wikipedia excerpt offset invalid")
            score = hit.get("bm25_score")
            _require(isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score), "Wikipedia BM25 score invalid")
            candidates.append({"article_id": int(hit["page_id"]), "api_page_id": hit["page_id"],
                               "name": hit["title"], "url": hit["url"], "revision_id": int(hit["revision_id"]),
                               "shard": provenance.get("source_shard") or provenance["source_key"],
                               "row_index": provenance["source_row_idx"], "excerpt": hit["excerpt"],
                               "excerpt_offset": hit["excerpt_offset"], "bm25_score": score,
                               "retrieval": "organizer_shared_lexical_bm25", "provenance": provenance})
        write_json(self.root / "searches" / (hashlib.sha256(query.encode()).hexdigest() + ".json"),
                   {"query": query, "retrieved_at": now(), "service_url": self.base_url, "response": result})
        return candidates

    def fetch(self, candidate: dict) -> dict:
        self._verify()
        page_id = str(candidate.get("api_page_id", candidate.get("article_id", "")))
        if re.fullmatch(r"[0-9]{1,20}", page_id) is None:
            raise ValueError("A numeric Wikipedia page ID from search is required")
        expected_revision = str(candidate["revision_id"]) if candidate.get("revision_id") is not None else None
        cache = self.root / "articles" / f"{page_id}-{expected_revision or 'unknown'}.json"
        cached = load_json(cache)
        if cached:
            text = cached["article"]["text"]
            _require(cached["provenance"].get("dataset_revision") == REVISION
                     and hashlib.sha256(text.encode()).hexdigest() == cached["provenance"].get("text_sha256"), "Cached Wikipedia source checksum/revision differs")
            _require(str(cached["article"]["identifier"]) == page_id and
                     (expected_revision is None or str(cached["article"]["version"]["identifier"]) == expected_revision),
                     "Cached Wikipedia identity/revision differs")
            expected_hash = candidate.get("provenance", {}).get("text_sha256")
            _require(expected_hash is None or cached["provenance"]["text_sha256"] == expected_hash,
                     "Cached Wikipedia checksum differs from search hit")
            return cached
        offset, pieces, identity, total, pages = 0, [], None, None, []
        while True:
            row = self._request("GET", f"/v1/articles/{page_id}", params={"offset": offset, "max_chars": 20000})
            source = self._source(row)
            expected_hash = candidate.get("provenance", {}).get("text_sha256")
            _require(expected_hash is None or source["text_sha256"] == expected_hash,
                     "Wikipedia article checksum differs from search hit")
            _require(row["page_id"] == page_id and (expected_revision is None or row["revision_id"] == expected_revision),
                     "Wikipedia fetched article/revision differs from candidate")
            text = row.get("text")
            _require(isinstance(text, str) and row.get("offset") == offset and row.get("returned_chars") == len(text)
                     and len(text) <= 20000, "Wikipedia article pagination length/offset differs")
            _require(_integer(row.get("total_chars")) and offset + len(text) <= row["total_chars"] <= 5_000_000,
                     "Wikipedia article total length invalid or beyond5M-character client cap")
            current = (row["page_id"], row["revision_id"], row["title"], row["url"], source["text_sha256"], source["source_key"], source["source_row_idx"])
            if identity is None:
                identity, total = current, row["total_chars"]
            _require(current == identity and total == row["total_chars"], "Wikipedia source changed during pagination")
            pieces.append(text)
            end = offset + len(text)
            expected_next = end if end < total else None
            _require(row.get("next_offset") == expected_next and (expected_next is None or end > offset),
                     "Wikipedia continuation offset invalid")
            pages.append({"offset": offset, "returned_chars": len(text), "next_offset": row["next_offset"]})
            if expected_next is None:
                break
            offset = expected_next
        complete_text = "".join(pieces)
        _require(hashlib.sha256(complete_text.encode("utf-8")).hexdigest() == source["text_sha256"],
                 "Complete Wikipedia UTF-8 text checksum differs")
        provenance = {**source, "service_url": self.base_url, "access_mode": "organizer_shared_api",
                      "page_id": page_id, "revision_id": row["revision_id"], "retrieved_at": now(),
                      "pagination": pages, "text_checksum_verified": True,
                      "structured_fields_available": False,
                      "limitation": "Shared API exposes flattened article text; original structured sections and reference records are unavailable."}
        article = {"identifier": int(page_id), "version": {"identifier": int(row["revision_id"])},
                   "name": row["title"], "url": row["url"], "text": complete_text, "license": row["license"]}
        result = {"article": article, "sections": [{"path": f"shared_text[0:{len(complete_text)}]", "headings": [],
                  "text": complete_text, "citations": [], "links": [], "table_references": []}],
                  "references": [], "provenance": provenance}
        write_json(cache, result)
        return result

    def stats(self) -> dict:
        try:
            corpus = self._verify()
            proof = corpus["verification"]
            return {"mode": "organizer_shared_api", "service_url": self.base_url, "ready": True,
                    "dataset": DATASET, "dataset_revision": REVISION, "retrieval": "lexical_bm25",
                    "articles_indexed": proof["canonical_articles"], "raw_rows": proof["raw_rows"],
                    "expected_english_shards": proof["source_shards"], "shards": {"complete": proof["source_shards"], "pending": 0},
                    "catalog_complete": True, "verification": proof, "license": corpus["license"],
                    "note": "Shared lexical source index. Team semantic embeddings, reranking and LanceDB evidence are separate."}
        except WikipediaServiceError as error:
            return {"mode": "organizer_shared_api", "service_url": self.base_url, "ready": False,
                    "dataset": DATASET, "dataset_revision": REVISION, "catalog_complete": False,
                    "error": str(error), "note": "No local/current-Wikipedia fallback was used."}

    def build_catalog(self, **_) -> dict:
        """Compatibility: verify the provided index rather than rebuild millions of titles."""
        self._verify()
        return self.stats()
