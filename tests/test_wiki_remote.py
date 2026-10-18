"""Offline organizer API contract tests; no model or live evaluation outcomes."""
import hashlib
import json

import httpx
import pytest

from kat.wiki_remote import DATASET, REVISION, RemoteWikiCorpus, WikipediaProtocolError, WikipediaServiceError


TEXT = "Charge π changes. The example is synthetic, not a source quotation."
PROVENANCE = {"dataset": DATASET, "dataset_revision": REVISION, "dataset_url": "https://huggingface.co/datasets/wikimedia/structured-wikipedia",
              "source_key": "enwiki/source:7", "source_row_idx": 7, "source_shard": "enwiki/data/example.parquet",
              "text_sha256": hashlib.sha256(TEXT.encode()).hexdigest(), "extraction": "fixture-flat-text",
              "revision_url": "https://en.wikipedia.org/w/index.php?oldid=20"}
LICENSE = {"spdx": "CC-BY-SA-4.0", "attribution": "Wikipedia contributors"}
BASE = {"page_id": "10", "revision_id": "20", "title": "Synthetic fixture", "url": "https://en.wikipedia.org/wiki/Fixture",
        "provenance": PROVENANCE, "license": LICENSE}
PROOF = {"production": True, "raw_rows": 7597149, "canonical_articles": 7182883, "source_shards": 86,
         "fts_indexed_rows": 7182883, "fts_unindexed_rows": 0}


def client_for(tmp_path, *, transform=None, busy=0):
    seen = []
    counter = {"busy": busy}

    def handler(request):
        seen.append(request)
        path = request.url.path
        if path == "/ready":
            result = {"status": "ready", "production": True, "dataset_revision": REVISION}
        elif path == "/v1/corpus":
            result = {"dataset": DATASET, "dataset_revision": REVISION, "verification": PROOF, "license": LICENSE}
        elif path == "/v1/search":
            if counter["busy"]:
                counter["busy"] -= 1
                return httpx.Response(429, headers={"Retry-After": "0"})
            body = json.loads(request.content)
            assert request.headers.get("Authorization") is None
            assert body == {"query": "charge", "top_k": 2, "excerpt_chars": 1000}
            result = {"query": body["query"], "retrieval": "lexical_bm25", "corpus_revision": REVISION, "count": 1,
                      "hits": [{**BASE, "rank": 1, "bm25_score": 4.5, "excerpt": TEXT[:12], "excerpt_offset": 0, "total_chars": len(TEXT)}]}
        elif path == "/v1/articles/10":
            offset = int(request.url.params["offset"])
            # Deliberately small Unicode-character pages, independently of byte length.
            chunk = TEXT[offset:offset+13]
            end = offset + len(chunk)
            result = {**BASE, "text": chunk, "offset": offset, "returned_chars": len(chunk), "total_chars": len(TEXT),
                      "next_offset": end if end < len(TEXT) else None}
        else:
            return httpx.Response(404)
        if transform:
            result = transform(path, result)
        return httpx.Response(200, json=result)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return RemoteWikiCorpus(tmp_path, "https://fake.invalid", client=http, retries=1), seen


def test_shared_corpus_search_paginated_unicode_checksum_and_cache(tmp_path):
    wiki, requests = client_for(tmp_path)
    assert wiki.stats()["catalog_complete"] is True
    candidates = wiki.search("charge", limit=2)
    assert candidates[0]["article_id"] == 10 and candidates[0]["revision_id"] == 20
    result = wiki.fetch(candidates[0])
    assert result["article"]["text"] == TEXT
    assert result["provenance"]["text_checksum_verified"] is True
    assert result["provenance"]["access_mode"] == "organizer_shared_api"
    assert len(result["provenance"]["pagination"]) > 1
    assert result["references"] == [] and result["sections"][0]["citations"] == []
    assert result["provenance"]["structured_fields_available"] is False
    before = len(requests)
    assert wiki.fetch(candidates[0])["article"]["text"] == TEXT
    assert len(requests) == before


@pytest.mark.parametrize("failure", ["checksum", "offset", "revision", "next_offset"])
def test_inconsistent_article_pages_cannot_be_cached(tmp_path, failure):
    def transform(path, result):
        if not path.startswith("/v1/articles/"):
            return result
        if failure == "checksum":
            result["text"] = "X" + result["text"][1:]
        elif failure == "offset":
            result["offset"] += 1
        elif failure == "revision":
            result["revision_id"] = "21"
        elif failure == "next_offset":
            result["next_offset"] = 0
        return result
    wiki, _ = client_for(tmp_path, transform=transform)
    with pytest.raises(WikipediaProtocolError):
        wiki.fetch(wiki.search("charge", limit=2)[0])
    assert not list((tmp_path / "articles").glob("*.json"))


def test_shared_index_refuses_incomplete_or_different_snapshot(tmp_path):
    def transform(path, result):
        if path == "/v1/corpus":
            result = {**result, "verification": {**PROOF, "fts_unindexed_rows": 1}}
        return result
    wiki, _ = client_for(tmp_path, transform=transform)
    assert wiki.stats()["ready"] is False
    with pytest.raises(WikipediaProtocolError):
        wiki.search("charge", limit=2)


def test_busy_readonly_service_has_bounded_retry_and_honors_retry_after(tmp_path):
    wiki, requests = client_for(tmp_path, busy=1)
    assert wiki.search("charge", limit=2)
    assert sum(request.url.path == "/v1/search" for request in requests) == 2
    failing, requests = client_for(tmp_path / "failed", busy=5)
    with pytest.raises(WikipediaServiceError, match="busy"):
        failing.search("charge", limit=2)
    assert sum(request.url.path == "/v1/search" for request in requests) == 2
