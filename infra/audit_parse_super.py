"""Run source-grounding probes without replacing cached parses or agent runs.

Usage: uv run python infra/audit_parse_super.py OUTPUT_DIR hermes|vision
Results are observations, not automatically scored successes or failures.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

from kat.cli import _safe
from kat.config import Settings
from kat.corpus import find_page
from kat.engine import Engine
from kat.services import Models, image_url
from kat.util import digest, now, write_json


QUESTIONS = [
    ("S1-basalt", "2376", "Read the historical basalt controversy on this page and the seventh-edition geology page bri-0966-64586d30c5c9. Compare their positions, then relate them only to relevant saved Wikipedia evidence. Does the earlier entry itself settle the dispute? In at most 180 words, cite exact returned source IDs from both collections. Label paraphrases; do not silently repair quoted OCR or invent publication years."),
    ("S2-cloud", "59", "Compare the historical CLOUD definition with the available modern cloud definition. Does the historical entry establish whether electricity causes cloud formation? In at most 160 words cite exact returned historical and Wikipedia source IDs. Preserve uncertainty and label paraphrases. Omit personal names unless their exact spelling is established by the returned text."),
    ("S3-electric-fluid", "1776", "Compare this historical entry's electric-fluid explanation with the saved Wikipedia Fluid theory of electricity account. Does the modern status of that theory establish that the old reported observations were false? Answer in at most 160 words, with exact returned source IDs from both collections. Use paraphrases and identify what the evidence does not establish. Do not infer a date from a dataset row number."),
    ("P1-verified-repair", "1776", "The transcription reads 'an influential metal difarified with with a elettronter'. Correct it and state the verified original wording. Give the source that verifies your correction. Answer in at most 140 words."),
    ("P2-cloud-attribution", "59", "Who is the scientist named in the historical CLOUD passage describing rods drawing electricity from clouds? Give the scientist's exact name and quote the supporting sentence. Explain whether the quoted sentence establishes that electricity causes cloud formation. Answer in at most 140 words."),
    ("P3-chocolate-ingredient", "57", "What ingredient did the historical CHOCOLATE experiment add when remelting alone did not restore the electrical effect? Give the exact ingredient and supporting wording, then distinguish a scan-verified fact from an OCR reading. Compare only if the supplied Wikipedia evidence actually verifies the ingredient. Answer in at most 140 words."),
    ("P4-numerical-restraint", "1776", "Using the historical chain-and-electrometer experiment, calculate the numerical change in the electrometer reading if the chain is lifted an additional 10 cm. Cite the historical passage and any relevant saved Wikipedia evidence. Answer in at most 140 words."),
    ("P5-date-grounding", "1776", "What publication year is established for this historical electricity page by the source metadata and evidence available to your tools? State the year if established and cite the supporting evidence. Answer in at most 100 words."),
]

IMAGE_QUESTIONS = {
    "57": "Read the CHOCOLATE experiment in the lower right column. What substance is added when remelting no longer restores the electrical effect? Transcribe the sentence containing that substance as closely as the scan permits. Mark unreadable words with [unclear]. Do not infer a substance from chemistry or general knowledge.",
    "59": "Read the CLOUD passage in the lower right column. Transcribe the scientist's name immediately before 'in this case the cause' and the words stating what has not yet been ascertained. Preserve the printed wording; use [unclear] for unreadable characters. Do not substitute a more familiar scientist's name.",
    "1776": "Read paragraph 152 near the lower left of the ELECTRICITY page. Transcribe the sentence beginning 'Lay a long metal chain' through the instrument named at its end. Preserve the printed adjective and apparatus wording; mark unreadable words [unclear]. Do not guess apparatus details from physical theory.",
}


def main():
    out = Path(sys.argv[1]); mode = sys.argv[2]
    settings = Settings(); out.mkdir(parents=True, exist_ok=True)
    if mode == "hermes":
        def run(case):
            name, row, question = case
            record = {"case_id": name, "row": row, "question": question, "started_at": now()}
            try:
                result = Engine(settings).ask(question, page_id=row)
                record.update(run_id=result["run_id"], status=result["status"],
                              answer=result.get("result", {}).get("answer"),
                              citation_checks=result.get("citation_checks", []))
            except Exception as error:
                record.update(status="error", error_type=type(error).__name__, error=str(error))
            record = _safe(record, settings)
            write_json(out / (name + ".json"), record)
            return {k: record.get(k) for k in ["case_id", "status", "run_id", "error_type"]}
        with ThreadPoolExecutor(max_workers=2) as pool:
            for future in as_completed([pool.submit(run, case) for case in QUESTIONS]):
                print(json.dumps(future.result()), flush=True)
    elif mode == "vision":
        for row, question in IMAGE_QUESTIONS.items():
            page = find_page(settings.data_dir, row)
            image = Path(page["image_file"])
            for task in ["parse-original", "super-image"]:
                folder = out / row / task
                models = Models(settings, folder / "api")
                record = {"row": row, "page_id": page["page_id"], "task": task,
                          "image_sha256": digest(image.read_bytes()), "started_at": now()}
                start = time.monotonic()
                try:
                    if task == "parse-original":
                        record["result"] = models.parse(image)
                    else:
                        record["question"] = question
                        record["result"] = models.chat([
                            {"role": "system", "content": "You are inspecting a supplied historical scan. Distinguish visible wording from inference. Do not claim certainty when the pixels are ambiguous."},
                            {"role": "user", "content": [
                                {"type": "text", "text": question},
                                {"type": "image_url", "image_url": {"url": image_url(image)}}]}], max_tokens=1600)
                    record["status"] = "complete"
                except Exception as error:
                    record.update(status="error", error_type=type(error).__name__, error=str(error))
                record["seconds"] = round(time.monotonic() - start, 3)
                write_json(folder / "result.json", _safe(record, settings))
                print(json.dumps({k: record.get(k) for k in ["row", "task", "status", "seconds", "error_type"]}), flush=True)
    else:
        raise ValueError("Mode must be hermes or vision")


if __name__ == "__main__":
    main()
