"""Explicit model adapters. Organizer model IDs/URLs are configuration, never substitutes."""
import base64
import math
import re
import time
import uuid
from urllib.parse import urlsplit
from html.parser import HTMLParser
from pathlib import Path

import httpx

from .config import Settings
from .util import digest, json_answer, now, write_json
from .vendor.starter.clients import JSONClient, _contents
from .vendor.starter.config import EMBED_DIMENSIONS, EMBED_MODEL, EMBED_REVISION, RERANK_MODEL, RERANK_REVISION


class ConfigurationError(RuntimeError):
    pass


def image_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def safe_payload(value):
    if isinstance(value, dict):
        return {k: safe_payload(v) for k, v in value.items() if k.lower() not in {"authorization", "api_key", "x-key"}}
    if isinstance(value, list):
        return [safe_payload(v) for v in value]
    if isinstance(value, str) and "base64," in value:
        return {"inline_media_sha256": digest(value), "characters": len(value)}
    return value


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def parsed_content(raw: str) -> dict:
    """Preserve all raw output and only claim boxes if the service supplied them."""
    # Parse 3.5's actual shared endpoint emits normalized coordinate tokens with
    # the class after each region. Preserve emitted order, including headers.
    number=r"-?(?:\d+(?:\.\d*)?|\.\d+)"
    pattern=rf"<x_({number})><y_({number})>(.*?)<x_({number})><y_({number})><class_([^>]+)>"
    token_regions=[]
    for index,match in enumerate(re.finditer(pattern,raw,flags=re.S)):
        x1,y1,text,x2,y2,kind=match.groups()
        bbox=list(map(float,[x1,y1,x2,y2]))
        token_regions.append({"region_id":f"region-{index}","text":text.strip(),"bbox_raw":bbox,"type":kind,
                              "coordinate_system":"normalized_0_1","bbox_within_page":all(0<=v<=1 for v in bbox) and bbox[0]<bbox[2] and bbox[1]<bbox[3],
                              "coordinates_verified":False,"reading_order":index})
    if token_regions:
        readable=any(region["text"].strip() for region in token_regions)
        layout_only=not readable and all(region["type"].casefold() in {"picture","image","figure","illustration"} for region in token_regions)
        if not readable and not layout_only:
            raise ValueError("Parser produced text regions without readable text; retain this page as a parse failure")
        residual=re.sub(pattern,"",raw,flags=re.S).strip()
        note="Provider order and normalized boxes retained. Coordinate validity is syntactic; OCR, reading order and box alignment need human review."
        if layout_only:
            note+=" No readable text was extracted; only picture/layout regions were returned. This does not establish that the original scan is blank."
        return {"text":"\n\n".join(r["text"] for r in token_regions),"regions":token_regions,"raw":raw,
                "readable_text":readable,"extraction_status":"text_extracted" if readable else "layout_only",
                "unparsed_residual":residual,"note":note}
    try:
        value = json_answer(raw)
    except ValueError:
        value = None
    regions = []
    if isinstance(value, dict):
        text = value.get("text") or value.get("markdown") or ""
        blocks = value.get("regions", value.get("blocks", []))
        for index, block in enumerate(blocks if isinstance(blocks, list) else []):
            if not isinstance(block, dict):
                continue
            content = block.get("text") or block.get("content") or ""
            if content:
                regions.append({"region_id": f"region-{index}", "text": str(content),
                                "bbox_raw": block.get("bbox"), "type": block.get("type"),
                                "coordinates_verified": False})
        if not text and regions:
            text = "\n\n".join(r["text"] for r in regions)
    else:
        parser = _Text(); parser.feed(raw)
        text = "\n".join(parser.parts).strip() if "<" in raw else raw.strip()
    if not str(text).strip():
        raise ValueError("Parser produced no readable text; retain this page as a parse failure")
    if not regions:
        regions = [{"region_id": "page", "text": str(text), "bbox_raw": None,
                    "type": "whole_page", "coordinates_verified": False}]
    return {"text": str(text), "regions": regions, "raw": raw, "readable_text":True,"extraction_status":"text_extracted",
            "note": "Boxes are unverified raw provider coordinates; whole-page fallback is explicit."}


class Models:
    def __init__(self, settings: Settings, trace_dir: Path | None = None):
        self.settings = settings; self.trace_dir = trace_dir; self.events = []

    def _scrub(self, text: str) -> str:
        for secret in self.settings.secrets():
            text = text.replace(secret, "[REDACTED]")
        return text

    def redact(self, value):
        if isinstance(value,str):return self._scrub(value)
        if isinstance(value,list):return [self.redact(item) for item in value]
        if isinstance(value,dict):return {k:self.redact(v) for k,v in value.items() if k.lower() not in {"authorization","api_key","access_token","x-api-key"}}
        return value

    def post(self, role: str, url: str, model: str, key: str, payload: dict) -> dict:
        if not url or not model:
            raise ConfigurationError(f"Configure {role.upper()} endpoint and exact organizer model ID in .env")
        started = time.monotonic()
        event = {"role": role, "model": model, "url": self._scrub(url), "started_at": now(), "request": self.redact(safe_payload(payload))}
        try:
            # No automatic POST retries; a timeout does not establish the request was unbilled.
            with httpx.Client(timeout=self.settings.http_timeout) as client:
                parts=urlsplit(url)
                transport=JSONClient(f"{parts.scheme}://{parts.netloc}",key,client=client,timeout=self.settings.http_timeout)
                result=self.redact(transport.request("POST",parts.path,payload=payload))
            if not isinstance(result,dict):raise ValueError(f"{role} returned a non-object JSON response")
            event.update(status="ok", response=safe_payload(result), usage=result.get("usage"))
            return result
        except Exception as error:
            event.update(status="error", error=self._scrub(str(error)))
            if self._scrub(str(error))!=str(error):
                raise RuntimeError(self._scrub(str(error))) from None
            raise
        finally:
            event["seconds"] = round(time.monotonic()-started, 3)
            self.events.append(event)
            if self.trace_dir:
                write_json(self.trace_dir / f"{len(self.events):03d}-{role}-{uuid.uuid4().hex[:12]}.json", event)

    def chat(self, messages: list[dict], max_tokens: int = 6144, *, enable_thinking: bool = False,
             response_schema: dict | None = None) -> str:
        s = self.settings
        if not s.token_factory_api_key.get_secret_value():
            raise ConfigurationError("Set TOKEN_FACTORY_API_KEY in the local .env")
        payload={"model":s.nemotron_agent_model,"messages":messages,"max_tokens":max_tokens,"temperature":0,
                 "chat_template_kwargs":{"enable_thinking":enable_thinking}}
        if response_schema is not None:
            payload["response_format"]={"type":"json_schema","json_schema":{
                "name":"source_comparison","strict":True,"schema":response_schema}}
        result = self.post("agent", s.token_factory_base_url.rstrip("/")+"/chat/completions", s.nemotron_agent_model,
                           s.token_factory_api_key.get_secret_value(),payload)
        content = result["choices"][0]["message"].get("content")
        if result.get("model")!=s.nemotron_agent_model or result["choices"][0].get("finish_reason")!="stop":
            raise ValueError("Agent model identity differs or generation is incomplete; inspect saved response")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Agent returned no final text; inspect the recorded model response")
        return content

    def parse(self, image: Path, max_tokens: int = 8744) -> dict:
        s = self.settings
        content = [{"type": "image_url", "image_url": {"url": image_url(image)}}]
        if s.parse_prompt:
            content.insert(0, {"type": "text", "text": s.parse_prompt})
        result = self.post("parse", s.parse_api_url, s.parse_model, s.parse_api_key.get_secret_value(),
                           {"model": s.parse_model, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
                            "temperature":0,"skip_special_tokens":False,"add_special_tokens":False})
        if result.get("model")!=s.parse_model or result["choices"][0].get("finish_reason")!="stop":
            raise ValueError("Parse model identity differs or output is truncated; raw provider response retained")
        return parsed_content(result["choices"][0]["message"]["content"])

    def embed(self, texts: list[str], *, query: bool = False, modality: str = "text") -> list[list[float]]:
        s = self.settings
        if s.embed_protocol not in {"challenge", "openai", "nim_vl"}:
            raise ConfigurationError("EMBED_PROTOCOL must be challenge, openai or nim_vl")
        payload = {"model": s.embed_model, "input": texts, "input_type": "query" if query else "passage", "encoding_format": "float"}
        if s.embed_protocol=="challenge":
            if s.embed_model!=EMBED_MODEL:raise ConfigurationError("Use the organizer's pinned Embed VL model")
            if query and modality!="text":raise ValueError("Organizer query embeddings accept text only")
            inputs=[{"image":text} for text in texts] if modality=="image" else texts
            _contents(inputs,16,allow_images=not query,text_limit=2000 if query else 32000)
            payload={"model":s.embed_model,"input":inputs,"input_type":"query" if query else "document"}
        elif s.embed_protocol == "nim_vl":
            payload.update(modality=modality, embedding_type="float")
        elif modality != "text":
            raise ConfigurationError("Image embeddings require the explicit nim_vl adapter")
        result = self.post("embed", s.embed_api_url, s.embed_model, s.embed_api_key.get_secret_value(), payload)
        if s.embed_protocol=="challenge":
            if result.get("model")!=EMBED_MODEL or result.get("model_revision")!=EMBED_REVISION or result.get("dimensions")!=EMBED_DIMENSIONS or result.get("normalized") is not True:
                raise ValueError("Embedding response model/revision/dimensions/normalization differs from the organizer contract")
        data=result.get("data")
        if not isinstance(data,list) or not all(isinstance(item,dict) and isinstance(item.get("index"),int) and isinstance(item.get("embedding"),list) for item in data):
            raise ValueError("Embedding response data must contain indexed embedding vectors")
        data = sorted(data, key=lambda item: item["index"])
        if [r.get("index") for r in data] != list(range(len(texts))):
            raise ValueError("Embedding response does not cover every requested input exactly once")
        vectors = [r["embedding"] for r in data]
        if not vectors or not all(isinstance(v, list) and v and all(isinstance(x, (int, float)) and math.isfinite(x) for x in v) for v in vectors):
            raise ValueError("Embedding response contains invalid/non-finite vectors")
        if len({len(v) for v in vectors}) != 1:
            raise ValueError("Embedding dimensions differ within a batch")
        if s.embed_protocol=="challenge" and any(len(v)!=EMBED_DIMENSIONS or abs(sum(x*x for x in v)-1)>.02 for v in vectors):
            raise ValueError("Organizer embeddings must be normalized 2048-dimensional vectors")
        return vectors

    def rerank(self, query: str, passages: list[str], limit: int = 8) -> list[dict]:
        if not passages:
            return []
        s = self.settings
        if s.rerank_protocol == "nim":
            payload = {"model": s.rerank_model, "query": {"text": query}, "passages": [{"text": p} for p in passages], "truncate": "END"}
        elif s.rerank_protocol in {"cohere","challenge"}:
            if s.rerank_protocol=="challenge" and (s.rerank_model!=RERANK_MODEL or len(passages)>32 or len(query)>2000):
                raise ConfigurationError("Organizer reranking requires its pinned model, at most32 documents and a query up to2000 characters")
            if s.rerank_protocol=="challenge":_contents(passages,32)
            payload = {"model": s.rerank_model, "query": query, "documents": passages, "top_n": min(limit, len(passages))}
        else:
            raise ConfigurationError("RERANK_PROTOCOL must be nim or cohere")
        result = self.post("rerank", s.rerank_api_url, s.rerank_model, s.rerank_api_key.get_secret_value(), payload)
        if s.rerank_protocol=="challenge" and (result.get("model")!=RERANK_MODEL or result.get("model_revision")!=RERANK_REVISION or result.get("score_type")!="raw_logit"):
            raise ValueError("Reranker model/revision/raw-logit contract differs")
        rows = result.get("rankings", result.get("results", []))
        if not isinstance(rows,list) or not all(isinstance(row,dict) for row in rows):
            raise ValueError("Reranker response must contain a rankings/results list")
        checked = []
        seen = set()
        for row in rows:
            index = row.get("index")
            score = row.get("logit", row.get("relevance_score", row.get("score")))
            if not isinstance(index, int) or not 0 <= index < len(passages) or index in seen or not isinstance(score, (int, float)) or not math.isfinite(score):
                raise ValueError("Reranker returned invalid indices/scores")
            seen.add(index); checked.append({"index": index, "score": score})
        if not checked:
            raise ValueError("Reranker returned no ranked candidates")
        return sorted(checked, key=lambda r: r["score"], reverse=True)[:limit]
