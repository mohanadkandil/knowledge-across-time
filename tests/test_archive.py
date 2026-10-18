"""Archive behavior checks without downloading or executing a LaTeX compiler."""
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser

from kat.archive import build_archive, comparison_html, latex_document, tex_escape
from kat.util import digest, load_json, write_json


def sample_page(tmp_path, row=57):
    image = tmp_path / f"source-{row}.jpg"
    image.write_bytes(b"test-image-placeholder-not-for-visual-validation")
    return {"page_id": f"bri-{row:04d}-fixture", "row_index": row, "metadata": "An <unsafe> title & metadata",
            "sha256": "a" * 64, "revision": "b" * 40, "image_file": str(image),
            "source_url": f"https://huggingface.co/datasets/example/viewer?row={row}"}


def sample_parse():
    return {"parse_model": "test-parse-model", "text": "Fixture extracted text.",
            "regions": [{"region_id": "region-0", "text": r"\input{/etc/passwd} \write18{touch /tmp/nope} 5% $x_1$ & # <script>alert(1)</script>",
                         "type": "Text", "reading_order": 0, "bbox_raw": [.1, .2, .5, .6], "bbox_within_page": True}]}


def test_latex_source_text_is_escaped_not_executable(tmp_path):
    raw = r"\write18{command} $x_1$ % & # ~ ^" + "\x00\x01\n"
    escaped = tex_escape(raw)
    assert r"\write18{" not in escaped
    assert r"\textbackslash{}write18\{command\}" in escaped
    assert all(char not in escaped for char in ["\x00", "\x01"])
    assert all(token in escaped for token in [r"\$", r"\_", r"\%", r"\&", r"\#"])
    assert "U+8870" in tex_escape("衰")  # Explicit rendering label; raw/HTML glyph stays unchanged.
    document = latex_document(sample_page(tmp_path), sample_parse())
    assert r"\input{" not in document and r"\write18{" not in document
    assert r"\textbackslash{}input\{/etc/passwd\}" in document
    assert "model-extracted text, not a corrected transcription" in document


def test_archive_keeps_missing_parses_and_failed_compilation_visible(tmp_path, monkeypatch):
    parsed_page = sample_page(tmp_path, 57)
    pending_page = sample_page(tmp_path, 59)
    write_json(tmp_path / "britannica/manifest.json", {"pages": [parsed_page, pending_page], "selection_method": "fixture-only selection"})
    write_json(tmp_path / "pages" / parsed_page["page_id"] / "parse.json", sample_parse())
    engine = SimpleNamespace(root=tmp_path, settings=SimpleNamespace(latex_engine="missing-compiler"),
                             store=SimpleNamespace(cases=lambda: {"cases": [], "successes": 0, "failures": 0}))
    monkeypatch.setattr("kat.archive.shutil.which", lambda name: None)
    report = build_archive(engine)
    assert report["selected"] == 2 and report["parsed"] == 1 and report["compiled"] == 0
    assert report["pages"][0]["compilation_error"]
    parsed_html = (tmp_path / "site/pages" / (parsed_page["page_id"] + ".html")).read_text()
    assert "&lt;script&gt;" in parsed_html and "<script>" not in parsed_html
    assert "&lt;unsafe&gt;" in parsed_html
    assert "LaTeX compilation pending/failed" in parsed_html
    assert 'left:10.0%;top:20.0%;width:40.0%' in parsed_html
    pending_html = (tmp_path / "site/pages" / (pending_page["page_id"] + ".html")).read_text()
    assert "Not yet extracted" in pending_html
    assert not (tmp_path / "site/documents" / (pending_page["page_id"] + ".tex")).exists()
    assert not list((tmp_path / "site/documents").glob("*.pdf"))


def test_comparison_escapes_claims_and_quotes_and_links_only_web_sources():
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.hrefs = []
        def handle_starttag(self, tag, attrs):
            if tag == "a": self.hrefs.append(dict(attrs).get("href"))

    malicious = '<script>alert("source")</script>'
    source_id = 'wiki-"<unsafe>'
    sources = {
        source_id: {"title": malicious, "url": "https://example.org/article?a=1&b=2", "provenance": {"revision_url": "https://example.org/oldid/123"}},
        "unsafe-url": {"title": "Bad URL", "url": "javascript:alert(1)"},
    }
    result = {"comparison": {
        "summary": malicious,
        "matches": [{"source_id": source_id, "relevance": malicious, "explanation": malicious},
                    {"source_id": "unsafe-url", "relevance": "weak", "explanation": "Inspect URL"}],
        "similarities": [{"claim": malicious, "evidence": [{"source_id": source_id, "quote": malicious}]}],
        "differences": [{"kind": malicious, "historical_claim": malicious, "modern_claim": malicious, "explanation": malicious,
                         "evidence": [{"source_id": "missing", "quote": "unregistered quotation"}]}],
        "uncertainties": [malicious]},
        "citation_checks": [{"source_id": source_id, "quote": malicious, "source_exists": True, "literal_quote_found": False}]}
    rendered = comparison_html(result, sources.__getitem__)
    links = Links(); links.feed(rendered)
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    assert '<blockquote><pre>&lt;script&gt;' in rendered
    assert "https://example.org/article?a=1&b=2" in links.hrefs
    assert "https://example.org/oldid/123" in links.hrefs
    assert "../sources/" + digest(source_id) + ".json" in links.hrefs
    assert all(not href.startswith("javascript:") for href in links.hrefs)
    assert "FAILED literal quote check" in rendered
    assert "Source unavailable" in rendered and "Literal quote not checked" in rendered
    assert "semantic support" in rendered and "OCR errors" in rendered
    assert "Raw comparison JSON and audit checks</summary>" in rendered
    assert "Historical source claim" in rendered and "Modern source claim" in rendered


def test_archive_preserves_source_provenance_and_abstention(tmp_path, monkeypatch):
    page = sample_page(tmp_path)
    write_json(tmp_path / "britannica/manifest.json", {"pages": [page]})
    folder = tmp_path / "pages" / page["page_id"]
    write_json(folder / "parse.json", sample_parse())
    source = {"id": "wiki-fixture", "kind":"wikipedia", "title": "Modern article", "url": "https://en.wikipedia.org/wiki/Fixture",
              "revision_id":42,"provenance": {"revision_id": 42}}
    write_json(folder / "comparison.json", {"comparison": {"summary": "A readable summary", "matches": [{"source_id": source["id"], "relevance": "partial", "explanation": "Only one topic overlaps."}]},
                                           "source_ids": [source["id"]], "citation_checks": []})
    engine = SimpleNamespace(root=tmp_path, settings=SimpleNamespace(latex_engine="missing-compiler"),
                             store=SimpleNamespace(source=lambda _: source.copy(), cases=lambda: {"cases": []}))
    monkeypatch.setattr("kat.archive.shutil.which", lambda _: None)
    build_archive(engine)
    exported = load_json(tmp_path / "site/sources" / (digest(source["id"]) + ".json"))
    assert exported["provenance"] == source["provenance"]
    rendered = (tmp_path / "site/pages" / (page["page_id"] + ".html")).read_text()
    assert "A readable summary" in rendered and "Only one topic overlaps." in rendered
    assert 'https://en.wikipedia.org/w/index.php?oldid=42' in rendered
    abstained = comparison_html({"abstained": True, "comparison": {"summary": "No readable historical text.", "uncertainties": ["Layout only."]},
                                "citation_checks": [], "literal_quotes_all_found": False}, engine.store.source)
    assert "Comparison abstained" in abstained and "No readable historical text." in abstained
    assert "No literal quote checks recorded" in abstained
    assert "FAILED literal quote" not in abstained and "Counterparts and relevance" not in abstained
