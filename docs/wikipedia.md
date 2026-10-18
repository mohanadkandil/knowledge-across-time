# Wikipedia source access

## Default: organizer-provided shared API

The latest participant briefing explicitly supplies a shared pre-indexed Wikipedia API, so teams do not need to build the title index. `kat.wiki_remote.RemoteWikiCorpus` is the default integration adapter. It exposes `search`, `fetch`, `stats`, and a compatibility `build_catalog` that verifies the shared index instead of rebuilding it. The source is `wikimedia/structured-wikipedia` at revision `417c267bb457fa645c22eb3b5c77764963194c70`, canonicalized to the latest numeric revision per page ID. Actual `/ready` and `/v1/corpus` probes reported all7,182,883 canonical articles indexed, from7,597,149 raw rows and86 English source shards.

The adapter records the supplied dataset/revision/source coordinates, follows Unicode-character pagination to completion and checks the complete UTF-8 text SHA256 before caching. It validates readiness, source/revision identity and pagination; honors bounded retries for429/503; and supplies no local/live-Wikipedia fallback on error. Cached provenance includes the public service URL, retrieval time, all page offsets, article/revision URLs and license.

```python
from pathlib import Path
from kat.wiki_remote import RemoteWikiCorpus
wiki = RemoteWikiCorpus(Path("data/wiki-remote"))
candidates = wiki.search("static electricity charge surface imbalance", limit=20)
evidence = wiki.fetch(candidates[0])  # candidate selection still needs semantic review
```

This API supplies **flattened text**, not original structured citation objects or original section boundaries. Its `sections` result is one explicitly identified flattened-text part; `references` and inline citation objects are empty. Team passage chunking and article/revision provenance remain available. Do not describe those missing fields as recovered. Chemical subscripts can be lost in the service extraction; retain exact text and flag missing notation.

See the [official API contract](https://github.com/andandandand/nemotron-agentic-ai-challenge/blob/main/docs/wikipedia-api.md). Live fetches of Capacitance, Static electricity, Carbonic acid, Condensation and Cloud physics passed complete-text checksums; their identities are recorded in [evaluation.md](evaluation.md). Lexical candidates still require the mandated semantic embedding and reranking stages. Single-noun searches can omit the desired article from a small candidate pool; the agent should test query expansion and abstain on weak coverage.

## Optional fallback: exact Kaggle version5 range access

The independent implementation below remains available for reproducibility or offline fallback chosen explicitly by configuration. **It is not required by the updated organizer briefing and is not silently mixed with the shared service.** The Kaggle distribution has different shard boundaries; byte identity with the shared HF source has not been established.

`kat.wiki.WikiCorpus` indexes the required **Kaggle `wikimedia-foundation/wikipedia-structured-contents`, version 5**. It does not replace it with live Wikipedia or the Hugging Face distribution. Those distributions have different shard layouts; exact equivalence has not been established.

## Use

Dependencies: Python 3.12, `httpx`, `pyarrow`; SQLite with FTS5 (included in the tested Python distribution).

```python
from pathlib import Path
from kat.wiki import WikiCorpus

wiki = WikiCorpus(Path("data/wiki"))
wiki.build_catalog(workers=3)  # resumable; identity columns only
matches = wiki.search("Chocolate", limit=10)
if matches:
    evidence = wiki.fetch(matches[0])
    print(evidence["provenance"])
    print(evidence["sections"])
```

`build_catalog(manifest_url=MANIFEST_URL, workers=3, shard_limit=None)` downloads the pinned public file listing, then reads only article title, identifier and URL columns through HTTP ranges. `shard_limit` supports a smoke test; partial indexes are explicitly partial. It commits one complete shard at a time, so rerunning skips completed shards and retries failed ones. Concurrent calls to `search` can use the growing committed index. Run one catalog builder per corpus directory.

`search(query, limit=10)` prioritizes case-insensitive exact titles, then uses safely quoted SQLite FTS tokens. Each candidate contains `article_id`, `name`, `url`, `shard`, `row_index` and `revision_id` (null until fetched). Search returns only indexed rows. Zero hits in a partial index do not establish absence from the corpus. Search scores concern titles, not semantic article similarity; the required Nemotron embedding and reranking stages sit above this discovery catalog.

`fetch(candidate)` fetches only its Parquet row group, verifies the row's article identifier, and caches the extracted article. The result includes:

- `article`: original full row, including dates, version metadata, source section JSON and tables.
- `sections`: recursively flattened section/paragraph values, retaining original source paths, heading ancestry, citation objects, links and table references.
- `references`: original reference records; reference `metadata` can itself be JSON-encoded.
- `provenance`: exact dataset/version/file/row, article/revision IDs, retrieval time, canonical extracted-row SHA256, bytes transferred and the public version-pinned download URL.

`stats()` and `catalog-status.json` expose indexed article counts, committed range bytes and pending/complete/failed shard counts. SQLite's `shards` table stores per-shard errors, sizes, completion timestamps and the digest of its extracted identity rows. The digests describe extracted data, **not full-shard file hashes**. `shard_sha256` is deliberately null because range reading cannot verify a whole-file SHA256 without reading the whole file.

## Download discipline

The range reader refuses HTTP200 before reading its body; requires exact HTTP206 and matching Content-Range total/start/end; checks Content-Length when supplied; counts received bytes; enforces a per-reader transfer ceiling; and retries transient failures a bounded number of times. Signed redirect URLs remain only in process memory. Catalog reads are limited to 32MiB per shard; full-row-group fetches to 256MiB. Very large/atypical articles or schemas can therefore fail explicitly instead of causing unbounded transfers.

Version5's actual manifest contains 265 English data shards, 103 French shards and two schema files, totaling 47,712,539,429 bytes. Its card states a May13 2026 extraction date and different shard counts. The code uses the actual pinned manifest; it does not assume the card's row counts are verified. Indexing identity columns across all English shards should transfer a small fraction of the full corpus, but real byte counts and runtime depend on Parquet metadata and networking. The public API worked without a Kaggle key in the tested requests. Network access/range behavior can change; a failed shard remains visible and retryable.

## Reproducibility and limitations

The cached manifest preserves retrieval provenance. The committed title digest, original source JSON, article/revision IDs and extracted-row hash allow the selected subset to be reviewed without downloading all Wikipedia. Preserve `manifest-v5.json`, `wikipedia.sqlite3` and the selected `articles/*.json` with a release; avoid treating the mutable live article URL as the exact historical snapshot.

An English title catalog is not the final 100-page match set. The pipeline still needs to generate multiple candidates, retrieve their actual passages, use the required embeddings/reranker, justify matches and surface uncertain/missing counterparts. References and credibility scores are evidence fields, not automatic truth labels; many fields can be null. Article text is CC BY-SA4.0; linked media can have different licenses. Show article title, project, link, license and clear notices for generated summaries.

Tests in `tests/test_wiki.py` cover refusal of a server ignoring Range, byte positions and malformed range headers, deeply nested citation paths, a resumable two-row corpus, exact row-group fetch, identity mismatch rejection, and cache reuse. These tests do not constitute a complete live-corpus retrieval benchmark.


## Live integration verification, 18 October 2026

The actual version5 title catalog found and the new `fetch()` path retrieved these full article rows from Kaggle (not HF/current Wikipedia):

- **Pneumatics**: article 195891, revision 1338706752, `enwiki/data/enwiki_namespace_0_00027.parquet` row 2437; 62 flattened parts and 9 reference records. Extracted-row SHA256 `d67254de7d3eab6e30957d151ce030f591f2ff8b7ceee6a38f34424ce8161411`.
- **Heat**: article 19593167, revision 1333417689, `enwiki/data/enwiki_namespace_0_00028.parquet` row 5832; 175 flattened parts and 99 reference records. Extracted-row SHA256 `553d240ea11686bb491a16cfb2588a51261a8162ba26c756dcb4a24eccdbecff`.
- **Optics**: article 22483, revision 1337176690, `enwiki/data/enwiki_namespace_0_00024.parquet` row 19476; 121 flattened parts and 135 reference records. Extracted-row SHA256 `c187da7b1b062eae8fe4da6bac2f22f3061d6e2c1840f4201e76729554e83247`.

These verify exact modern-source access through the implementation. They do not by themselves validate a historical match or an experimental claim. Selected cache locations and provenance are listed in `data/wiki/verified-targets.json`. The complete title catalog continues in the background and remains explicitly partial until every shard succeeds.
