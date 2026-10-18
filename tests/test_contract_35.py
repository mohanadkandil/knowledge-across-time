"""Parse3.5 and pinned retrieval-service contracts, using explicit offline stubs."""
from copy import deepcopy

import pytest

from kat.config import Settings
from kat.services import ConfigurationError, Models, parsed_content
from kat.vendor.starter.config import EMBED_DIMENSIONS, EMBED_MODEL, EMBED_REVISION, PARSE_MODEL, RERANK_MODEL, RERANK_REVISION


@pytest.fixture
def configured(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path, embed_protocol="challenge", rerank_protocol="challenge",
                    embed_model=EMBED_MODEL, rerank_model=RERANK_MODEL, parse_model=PARSE_MODEL,
                    embed_api_url="https://fake.invalid/embeddings", rerank_api_url="https://fake.invalid/rerank")


def embedding_response():
    return {"model": EMBED_MODEL, "model_revision": EMBED_REVISION, "dimensions": EMBED_DIMENSIONS, "normalized": True,
            "data": [{"index": 0, "embedding": [1.] + [0.] * (EMBED_DIMENSIONS - 1)}]}


def test_parse35_normalized_tokens_keep_provider_order_and_residual():
    raw = "PREFIX\n<x_0.1><y_0.8>First lower region<x_0.5><y_0.9><class_Text>\n<x_0.2><y_0.1>Second upper region<x_0.7><y_0.3><class_Title>\nRESIDUAL"
    parsed = parsed_content(raw)
    assert [r["text"] for r in parsed["regions"]] == ["First lower region", "Second upper region"]
    assert [r["reading_order"] for r in parsed["regions"]] == [0, 1]
    assert parsed["regions"][0]["bbox_raw"] == [.1, .8, .5, .9]
    assert parsed["regions"][0]["coordinate_system"] == "normalized_0_1"
    assert all(r["bbox_within_page"] and r["coordinates_verified"] is False for r in parsed["regions"])
    assert "PREFIX" in parsed["unparsed_residual"] and "RESIDUAL" in parsed["unparsed_residual"]
    reversed_box = parsed_content("<x_0.8><y_0.2>Text<x_0.1><y_0.6><class_Text>")
    assert reversed_box["regions"][0]["bbox_within_page"] is False
    assert reversed_box["regions"][0]["bbox_raw"] == [.8, .2, .1, .6]


def test_challenge_document_and_image_payloads_do_not_use_old_modality_fields(configured, monkeypatch):
    model = Models(configured)
    requests = []
    def post(role, url, name, key, payload):
        requests.append(payload)
        return embedding_response()
    monkeypatch.setattr(model, "post", post)
    assert len(model.embed(["Fixture document"])[0]) == 2048
    model.embed(["data:image/png;base64,ZmFrZQ=="], modality="image")
    model.embed(["Fixture query"], query=True)
    assert requests[0] == {"model": EMBED_MODEL, "input": ["Fixture document"], "input_type": "document"}
    assert requests[1] == {"model": EMBED_MODEL, "input": [{"image": "data:image/png;base64,ZmFrZQ=="}], "input_type": "document"}
    assert requests[2]["input_type"] == "query"
    assert all(not ({"modality", "encoding_format", "embedding_type"} & set(payload)) for payload in requests)


@pytest.mark.parametrize("change", [
    {"model": "wrong-model"}, {"model_revision": "0" * 40}, {"dimensions": 1024}, {"normalized": False},
    {"data": [{"index": 0, "embedding": [1., 0.]}]},
    {"data": [{"index": 0, "embedding": [2.] + [0.] * 2047}]},
])
def test_pinned_embedding_response_identity_dimensions_and_normalization(configured, monkeypatch, change):
    model = Models(configured)
    response = {**embedding_response(), **change}
    monkeypatch.setattr(model, "post", lambda *args, **kwargs: response)
    with pytest.raises(ValueError):
        model.embed(["Fixture document"])


def test_challenge_rerank_limit_and_payload(configured, monkeypatch):
    model = Models(configured)
    calls = []
    def post(role, url, name, key, payload):
        calls.append(payload)
        return {"model": RERANK_MODEL, "model_revision": RERANK_REVISION, "score_type": "raw_logit",
                "results": [{"index": 0, "relevance_score": 1.5}]}
    monkeypatch.setattr(model, "post", post)
    assert model.rerank("q" * 2000, ["Fixture passage"] * 32, limit=8) == [{"index": 0, "score": 1.5}]
    assert set(calls[0]) == {"model", "query", "documents", "top_n"}
    assert calls[0]["top_n"] == 8 and isinstance(calls[0]["query"], str)
    with pytest.raises(ConfigurationError):
        model.rerank("q" * 2001, ["One"])
    with pytest.raises(ConfigurationError):
        model.rerank("q", ["One"] * 33)
    assert len(calls) == 1


@pytest.mark.parametrize("model_name,finish_reason", [(PARSE_MODEL, "length"), ("wrong-parser", "stop")])
def test_truncated_or_wrong_parse_response_is_not_a_success(configured, monkeypatch, tmp_path, model_name, finish_reason):
    image = tmp_path / "fixture.jpg"
    image.write_bytes(b"offline fixture, never sent to a live service")
    model = Models(configured)
    responses = []
    def post(role, url, name, key, payload):
        responses.append(payload)
        return {"model": model_name, "choices": [{"finish_reason": finish_reason,
                "message": {"content": "<x_0.1><y_0.2>Incomplete text<x_0.5><y_0.6><class_Text>"}}]}
    monkeypatch.setattr(model, "post", post)
    with pytest.raises(ValueError, match="identity|truncated"):
        model.parse(image)
    assert responses[0]["skip_special_tokens"] is False
    assert responses[0]["add_special_tokens"] is False
    assert responses[0]["model"] == PARSE_MODEL
