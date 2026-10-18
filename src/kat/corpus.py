"""Pinned original scan selection. No discovery OCR is substituted for Nemotron Parse."""
import collections
import hashlib
import io
from pathlib import Path

import httpx
import pyarrow.parquet as pq
from PIL import Image

from .util import digest, load_json, now, write_json

REPOSITORY = "NationalLibraryOfScotland/encyclopaedia_britannica_illustrated"
REVISION = "309f765b1ecc83e0a7f7762e44b4a927a7555443"
FILE_SHA = "08f167015db23cb027995b2b6a6bc953b01d7c1ddf667de950465cc2b601af5c"
SOURCE_URL = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/data/train-00000-of-00001.parquet"
SEEDS = [57, 59, 1776]


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare(data_dir: Path, parquet: Path | None = None) -> dict:
    target = data_dir / "britannica"
    target.mkdir(parents=True, exist_ok=True)
    source = parquet or target / "source.parquet"
    if not source.exists():
        partial = source.with_suffix(".partial")
        with httpx.stream("GET", SOURCE_URL, follow_redirects=True, timeout=120) as response:
            response.raise_for_status()
            with partial.open("wb") as stream:
                for block in response.iter_bytes(1024*1024):
                    stream.write(block)
        if sha_file(partial) != FILE_SHA:
            raise ValueError("Britannica download hash differs from pinned dataset")
        partial.rename(source)
    if sha_file(source) != FILE_SHA:
        raise ValueError("Local Britannica file does not match the pinned source hash")
    rows = pq.read_table(source).to_pylist()
    if len(rows) != 2573:
        raise ValueError("Pinned corpus has an unexpected row count")
    chosen = set(SEEDS)
    # Fixed 80 text-class / 20 illustrated-class selection, spread over volumes.
    # Three disclosed manual seeds are counted within the text-class quota.
    for label, count in [(0, 80), (1, 20)]:
        groups = collections.defaultdict(list)
        for index, row in enumerate(rows):
            if row["label"] == label and index not in chosen:
                groups[row["id"]].append(index)
        for group in groups.values():
            group.sort(key=lambda i: digest(f"20261018:{i}"))
        volumes = sorted(groups, key=lambda volume: digest(f"20261018:{volume}"))
        remaining = count - sum(rows[i]["label"] == label for i in chosen)
        while remaining:
            progressed = False
            for volume in volumes:
                if groups[volume] and remaining:
                    chosen.add(groups[volume].pop(0)); remaining -= 1; progressed = True
            if not progressed:
                raise ValueError("Not enough rows for the declared sampling strata")
    pages = []
    for index in sorted(chosen):
        row = rows[index]
        raw = row["image"]["bytes"]
        image_sha = digest(raw)
        image = Image.open(io.BytesIO(raw))
        extension = ".png" if image.format == "PNG" else ".jpg"
        page_id = f"bri-{index:04d}-{image_sha[:12]}"
        path = target / "images" / (page_id + extension)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
        pages.append({"page_id": page_id, "row_index": index, "volume_id": row["id"],
                      "metadata": row["meta"], "label": row["label"], "sha256": image_sha,
                      "width": image.width, "height": image.height, "image_file": str(path.resolve()),
                      "dataset": REPOSITORY, "revision": REVISION, "split": "train",
                      "source_url": f"https://huggingface.co/datasets/{REPOSITORY}/viewer/default/train?row={index}",
                      "manual_seed": index in SEEDS})
    manifest = {"created_at": now(), "dataset": REPOSITORY, "revision": REVISION,
                "source_file_sha256": FILE_SHA, "total_dataset_rows": len(rows), "selected_count": len(pages),
                "selection_method": "Three disclosed manual seeds (57,59,1776), then deterministic SHA-256-seeded round-robin over volume groups to reach 80 label-0 and 20 label-1 rows; seed 20261018. Fixed before model evaluation; no dropping failed parses/matches.",
                "bias": "Manual seeds favor known scientific content; illustration strata do not imply topic or historical truth. This is not a representative estimate of all Britannica.",
                "pages": pages}
    write_json(target / "manifest.json", manifest)
    return manifest


def manifest(data_dir: Path) -> dict:
    return load_json(data_dir / "britannica" / "manifest.json", {"pages": [], "selected_count": 0})


def find_page(data_dir: Path, page_id: str) -> dict:
    for page in manifest(data_dir)["pages"]:
        if page["page_id"] == page_id or str(page["row_index"]) == page_id:
            return page
    raise KeyError("Page not in the documented selected corpus")
