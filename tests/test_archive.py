"""Archive behavior checks without downloading or executing a LaTeX compiler."""
from pathlib import Path
from types import SimpleNamespace

from kat.archive import build_archive, latex_document, tex_escape
from kat.util import write_json


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
