"""Behavior checks: bounded ranges, resumable indexing, evidence-preserving fetch."""
import io
import json

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kat.wiki import HTTPRangeFile, RangeReadError, WikiCorpus, flatten_sections


def test_range_reader_rejects_full_body_before_read():
    consumed = []

    class Dangerous(httpx.SyncByteStream):
        def __iter__(self):
            consumed.append(True)
            yield b"a whole giant shard"

    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Dangerous())))
    with HTTPRangeFile("https://test.invalid/file", 100, client=client, retries=0) as file:
        with pytest.raises(RangeReadError):
            file.read(8)
    assert consumed == []
    client.close()


def test_range_reader_exact_positions_and_mismatched_origin():
    data = b"0123456789"

    def handler(request):
        start, end = map(int, request.headers["Range"][6:].split("-"))
        return httpx.Response(206, headers={"Content-Range": f"bytes {start}-{end}/{len(data)}"}, stream=httpx.ByteStream(data[start:end+1]))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with HTTPRangeFile("https://test.invalid/file", len(data), client=client, retries=0) as file:
        file.seek(-3, io.SEEK_END)
        assert file.read(3) == b"789"
        file.seek(1)
        assert file.read(4) == b"1234"
        assert file.bytes_read == 7
    wrong = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(206, headers={"Content-Range": "bytes 0-2/99"}, content=b"012")))
    with HTTPRangeFile("https://test.invalid/file", 10, client=wrong, retries=0) as file:
        with pytest.raises(RangeReadError):
            file.read(3)
    client.close()
    wrong.close()


def test_recursive_sections_preserve_reference_paths():
    source = [{"name": "History", "has_parts": [{"type": "section", "name": "Experiment", "has_parts": [{"type": "paragraph", "value": "The measured charge changed.", "citations": [{"identifier": "ref-9"}]}]}]}]
    rows = flatten_sections(json.dumps(source))
    assert rows[0]["headings"] == ["History", "Experiment"]
    assert rows[0]["path"] == "sections[0].has_parts[0].has_parts[0]"
    assert rows[0]["citations"][0]["identifier"] == "ref-9"


def test_catalog_resumes_and_fetches_exact_row_group(tmp_path, monkeypatch):
    source = tmp_path / "test.parquet"
    pq.write_table(pa.Table.from_pylist([
        {"name": "Cloud", "identifier": 10, "url": "https://en.wikipedia.org/wiki/Cloud", "sections": json.dumps([{"value": "A cloud is an aggregate of droplets.", "type": "paragraph"}]), "references": [{"identifier": "r1", "text": "Atmospheric source"}], "version": {"identifier": 100}},
        {"name": "Chocolate", "identifier": 20, "url": "https://en.wikipedia.org/wiki/Chocolate", "sections": "[]", "references": [], "version": {"identifier": 200}},
    ]), source, row_group_size=1)
    shard = "enwiki/data/enwiki_namespace_0_00000.parquet"
    entries = [{"name": shard, "totalBytes": source.stat().st_size}, {"name": "enwiki/data/enwiki_namespace_0_00001.parquet", "totalBytes": source.stat().st_size}]
    corpus = WikiCorpus(tmp_path / "corpus")
    monkeypatch.setattr(corpus, "_manifest", lambda url: entries)
    import kat.wiki as module
    calls = []

    class LocalFile:
        def __init__(self, url, size, **kwargs):
            self.file = open(source, "rb")
            self.bytes_read = source.stat().st_size
            calls.append(url)
        def __enter__(self): return self
        def __exit__(self, *args): self.file.close()
        def read(self, *args): return self.file.read(*args)
        def seek(self, *args): return self.file.seek(*args)
        def tell(self): return self.file.tell()
        @property
        def closed(self): return self.file.closed

    monkeypatch.setattr(module, "HTTPRangeFile", LocalFile)
    assert corpus.build_catalog(workers=1, shard_limit=1)["articles_indexed"] == 2
    assert corpus.build_catalog(workers=1, shard_limit=1)["articles_indexed"] == 2
    assert len(calls) == 1
    assert corpus.stats()["catalog_complete"] is False
    assert corpus.stats()["expected_english_shards"] == 2
    candidate = corpus.search("cloud")[0]
    assert candidate["article_id"] == 10
    fetched = corpus.fetch(candidate)
    assert fetched["article"]["name"] == "Cloud"
    assert fetched["provenance"]["dataset_version"] == 5
    assert fetched["provenance"]["revision_id"] == 100
    assert fetched["sections"][0]["text"].startswith("A cloud")
    assert fetched["references"][0]["identifier"] == "r1"
    assert corpus.search("Cloud")[0]["revision_id"] == 100
    assert corpus.fetch(candidate)["article"]["identifier"] == 10
    assert len(calls) == 2  # second fetch is content-addressed local cache
    bad = {**candidate, "article_id": 999}
    with pytest.raises(ValueError, match="identity"):
        corpus.fetch(bad)
