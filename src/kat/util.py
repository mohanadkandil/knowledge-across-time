import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, default=str)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def load_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def json_answer(text: str) -> Any:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Raw prose is not silently accepted as a successful structured comparison.
        raise ValueError("Model did not return valid JSON; raw response is retained in the run") from None


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def chunks(text: str, size: int = 1600, overlap: int = 160):
    for start in range(0, len(text), size-overlap):
        part = text[start:start+size]
        if part.strip():
            yield start, min(len(text), start+size), part
