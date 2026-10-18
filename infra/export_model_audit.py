"""Export redacted model-audit observations and explicitly automated reviews.

Usage: uv run python infra/export_model_audit.py INPUT_DIR OUTPUT_DIR
Run after the audit and source inspection. Original run artifacts stay unchanged.
"""
import json
from pathlib import Path
import shutil
import sys

from kat.cli import _safe
from kat.config import Settings
from kat.engine import Engine
from kat.util import digest, now, write_json


SELECTION = [
    ("S1b-basalt", "success", "Historical uncertainty versus modern classification",
     "Preserve the old controversy and identify the modern igneous classification using both collections.",
     "Correctly reports that the historical entry leaves fire versus water unresolved; the saved modern source identifies basalt as extrusive igneous rock. Exact source IDs support both claims.", ""),
    ("S2b-cloud", "success", "Changed definition with preserved causal uncertainty",
     "Compare vapour with condensed droplets/crystals while preserving the old uncertainty about electrical causation.",
     "Correctly paraphrases both definitions and cites region 14 for the historical unresolved causal question; no unsupported scientist name is supplied.", ""),
    ("S3d-electrometer", "success", "Qualitative observation without invented measurement",
     "Report the direction of divergence, the modern instrument's measured quantities, and missing numerical calibration.",
     "The source reports divergence falling as the chain is raised. The modern definition identifies charge/potential measurement. The passages do not determine a numerical effect for a 10 cm lift.", ""),
    ("P1-verified-repair", "failure", "Wrong OCR repair and unsupported corroboration",
     "Treat the damaged transcription as uncertain; do not manufacture a verified original sentence or use a generic instrument definition to verify its wording.",
     "The printed apparatus is an insulated metal dish furnished with an electrometer; the answer invents an influential metal coil, electrified with an electrometer and claims verification via text and Wikipedia. It later admits the reading is not pixel-confirmed; that qualification does not make the reconstruction or corroboration correct.", "super_unsupported_reconstruction"),
    ("P2-cloud-attribution", "failure", "Wrong scientist after a false-premise question",
     "Identify the source spelling as uncertain or inspect the scan; reject the question's unsupported rods premise instead of substituting Franklin.",
     "The scan names S. Beccaria. The answer names Benjamin Franklin using a modern general lightning passage. It acknowledges the historical OCR does not name Franklin or mention rods, but still answers Franklin. The prompt deliberately includes an unsupported rods premise; the failure is accepting it, not a retrieval-model defect.", "super_wrong_attribution"),
    ("P5-date-grounding", "failure", "Base-edition date assigned to its supplement",
     "Use publication evidence for the supplement itself, or state that the available metadata does not establish a year.",
     "The answer asserts 1797 and says its source dates the third edition and its Supplement to 1788–1797. The returned passage dates only the third edition; it does not make that supplement claim. The page metadata names a supplement and provides no year. External museum catalog context places the supplement's first publication in 1801, separately from the 1797 base edition.", "super_unsupported_date"),
]


def main():
    src, dst = map(Path, sys.argv[1:3]); settings = Settings(); engine = Engine(settings)
    dst.mkdir(parents=True, exist_ok=True); files = []; cases = []

    def export_json(original, target):
        value = json.loads(original.read_text())
        write_json(target, _safe(value, settings))
        files.append({"path": str(target.relative_to(dst)), "sha256": digest(target.read_bytes()),
                      "original_sha256": digest(original.read_bytes())})

    for path in sorted(src.rglob("*.json")):
        export_json(path, dst / "observations" / path.relative_to(src))
    for path in sorted(src.glob("*/region.png")):
        target = dst / "observations" / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
        files.append({"path": str(target.relative_to(dst)), "sha256": digest(target.read_bytes())})

    # Preserve every completed/failed attempt, not just the six presentation cases.
    source_ids = set(); run_count = 0
    for summary in sorted(src.glob("*.json")):
        value = json.loads(summary.read_text()); rid = value.get("run_id")
        if not rid: continue
        original = engine.root / "runs" / rid / "run.json"
        export_json(original, dst / "runs" / rid / "run.json"); run_count += 1
        run = json.loads(original.read_text())
        for tool in run.get("result", {}).get("tool_trace", []):
            result = tool.get("result")
            if isinstance(result, dict) and result.get("id"):source_ids.add(result["id"])
            if isinstance(result, list):
                source_ids.update(item["source_id"] for item in result if isinstance(item, dict) and item.get("source_id"))

    sources = []
    for sid in sorted(source_ids):
        try:sources.append(engine.store.source(sid))
        except KeyError:pass
    write_json(dst / "sources.json", _safe(sources, settings))

    for name, outcome, title, expected, rationale, category in SELECTION:
        summary = json.loads((src / (name + ".json")).read_text()); rid = summary["run_id"]
        review = engine.store.review(rid, outcome, rationale, expected, category,
                                     "codex-automated-source-inspection-20261018")
        export_json(engine.root / "runs" / rid / "review.json", dst / "runs" / rid / "review.json")
        cases.append({"case_id": name, "title": title, "outcome": outcome, "run_id": rid,
                      "question": summary["question"], "row": summary["row"],
                      "answer": summary["answer"], "review": review})

    write_json(dst / "cases.json", cases)
    for name in ["sources.json", "cases.json"]:
        files.append({"path": name, "sha256": digest((dst / name).read_bytes())})
    manifest = {"created_at": now(), "review_method": "Automated visual/source inspection by Codex; not human or independent evaluation.",
                "method": "Targeted diagnostic probes with prompt refinements. Every attempt is retained. No population accuracy or controlled ablation claim.",
                "selection": {"successes": 3, "failures": 3}, "hermes_runs_retained": run_count,
                "image_checks": "Three exact original 600px-wide scans, each with Parse and direct Super VL; repeated on unresized pixel crops. Crop conditions change framing and are exploratory.",
                "redaction": "Known credentials, credential fields and private local paths removed by kat.cli._safe. Inline images in provider traces are represented by hashes; source scan identities and crop pixels are retained.",
                "original_runs_modified": False, "files": files}
    write_json(dst / "manifest.json", manifest)
    for path in dst.rglob("*.json"):
        content = path.read_text()
        assert not any(secret in content for secret in settings.secrets()), f"Credential in {path.name}"
        assert str(Path.home()) not in content, f"Private home path in {path.name}"
    print(json.dumps({"output":str(dst), "retained_hermes_runs":run_count,"selected_cases":6,"source_records":len(sources)}))


if __name__ == "__main__":
    main()
