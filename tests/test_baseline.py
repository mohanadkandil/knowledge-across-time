"""Offline behavior tests; synthetic model responses are never live evaluation cases.

LanceDB tests exercise the actual local database. HTTP tests use MockTransport and
fake credentials. Optional corpus test reads only an already-downloaded pinned file.
"""
import copy
import json
import os
from pathlib import Path

import httpx
import lancedb
import pytest

from kat.config import Settings
from kat.corpus import FILE_SHA, SEEDS, prepare
from kat.engine import citation_checks, language_metrics
from kat.services import Models, parsed_content
from kat.store import Store
from kat.util import digest, write_json


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path, token_factory_api_key="FAKE-TEST-CREDENTIAL-DO-NOT-USE",
                    nemotron_agent_model="test-agent-only", embed_api_url="https://fake.invalid/embeddings",
                    embed_model="test-embed-only", embed_protocol="nim_vl", rerank_api_url="https://fake.invalid/rerank",
                    rerank_model="test-rerank-only", rerank_protocol="nim")


def mock_endpoint(monkeypatch, handler):
    original_client = httpx.Client
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr("kat.services.httpx.Client", lambda **kwargs: original_client(transport=transport, **kwargs))


def test_exact_100_selection_is_reproducible_if_pinned_source_is_cached(tmp_path):
    supplied = os.environ.get("KAT_TEST_BRITANNICA_PARQUET")
    workspace_cache = Path(__file__).resolve().parents[2] / "research/dataset-fit-2026-10-18/britannica/train.parquet"
    source = Path(supplied) if supplied else workspace_cache
    if not source.is_file():
        pytest.skip("Set KAT_TEST_BRITANNICA_PARQUET to an existing pinned corpus; this test never downloads it")
    first = prepare(tmp_path / "one", parquet=source)
    second = prepare(tmp_path / "two", parquet=source)
    assert first["source_file_sha256"] == FILE_SHA
    assert first["total_dataset_rows"] == 2573
    assert first["selected_count"] == len(first["pages"]) == 100
    assert {p["row_index"] for p in first["pages"]} >= set(SEEDS)
    assert sum(p["label"] == 0 for p in first["pages"]) == 80
    assert sum(p["label"] == 1 for p in first["pages"]) == 20
    assert len({p["page_id"] for p in first["pages"]}) == 100
    identity = lambda result: [(p["row_index"], p["page_id"], p["sha256"]) for p in result["pages"]]
    assert identity(first) == identity(second)
    for page in first["pages"]:
        assert digest(Path(page["image_file"]).read_bytes()) == page["sha256"]


def test_real_lancedb_upsert_search_and_model_dimension_guard(tmp_path):
    store = Store(tmp_path)
    sources = [
        {"id": "historical-57", "kind": "britannica", "page_id": "57", "title": "CHOCOLATE", "text": "Reported observations, followed by a conjecture."},
        {"id": "modern-heat", "kind": "wikipedia", "title": "Heat", "text": "Synthetic passage for local vector-storage verification."},
    ]
    store.put_sources(sources)
    store.vector_upsert(sources, [[1., 0., 0.], [0., 1., 0.]], "test-embedding-model")
    assert store.vector_search([1., 0., 0.], "test-embedding-model", limit=1)[0]["id"] == "historical-57"
    filtered = store.vector_search([1., 0., 0.], "test-embedding-model", limit=5, kind="wikipedia")
    assert [r["id"] for r in filtered] == ["modern-heat"]
    changed = {**sources[0], "text": "Replacement evidence text."}
    store.put_sources([changed])
    store.vector_upsert([changed], [[0., 0., 1.]], "test-embedding-model")
    assert lancedb.connect(tmp_path / "lance").open_table("evidence").count_rows() == 2
    found = store.vector_search([0., 0., 1.], "test-embedding-model", limit=1)[0]
    assert found["id"] == changed["id"] and found["text"] == changed["text"]
    with pytest.raises(ValueError, match="model|identity"):
        store.vector_upsert([changed], [[0., 0., 1.]], "different-model")
    with pytest.raises(ValueError, match="dimensions|identity"):
        store.vector_upsert([changed], [[0., 1.]], "test-embedding-model")
    with pytest.raises(ValueError, match="identity"):
        store.vector_search([0., 1.], "test-embedding-model")
    with pytest.raises(ValueError, match="identity"):
        store.vector_search([0., 0., 1.], "different-model")
    assert store.stats()["embedding_identity"] == {"model": "test-embedding-model", "dimensions": 3}


def test_literal_quote_checks_do_not_claim_semantic_entailment():
    sources = {"historical-57": {"text": "It soon loses the property by handling. This is a conjecture."}}
    answer = {"differences": [{"evidence": [
        {"source_id": "historical-57", "quote": "loses the property\nby handling"},
        {"source_id": "historical-57", "quote": "carbonic acid is electricity"},
        {"source_id": "missing", "quote": "This is a conjecture."},
        {"source_id": "historical-57", "quote": "   "},
    ]}]}
    checks = citation_checks(answer, sources)
    assert [c["literal_quote_found"] for c in checks] == [True, False, False, False]
    assert [c["source_exists"] for c in checks] == [True, True, False, True]
    assert all(c["semantic_support"] == "requires human review" for c in checks)
    assert "not evidence of factual change" in language_metrics("fluid fluid", "charge")["note"]


def completed_question(run_id="fixture-question"):
    return {"run_id": run_id, "kind": "question", "execution": "live_models", "status": "complete",
            "question": "Synthetic fixture question; not an actual model run.", "created_at": "2026-10-18T00:00:00Z",
            "test_fixture": True,
            "result": {"framework": "hermes", "completed": True,
                       "answer": "Synthetic fixture answer [historical-57].", "tool_trace": []}}


def do_review(store, run_id, outcome="success"):
    return store.review(run_id, outcome, "Synthetic fixture human rationale", "Expected fixture behavior", "retrieval", "test reviewer")


@pytest.mark.parametrize("mutation", [
    {"kind": "comparison"}, {"execution": "offline_stub"}, {"status": "error"}, {"status": "running"},
    {"error": {"type": "ConfigurationError", "message": "Missing endpoint"}},
    {"result": {"framework": "other", "completed": True, "answer": "Text"}},
    {"result": {"framework": "hermes", "answer": "Completion flag missing"}},
    {"result": {"framework": "hermes", "completed": False, "answer": "Partial output"}},
    {"result": {"framework": "hermes", "completed": True, "answer": "   "}},
    {"result": {"framework": "hermes", "completed": True, "answer": "Text", "error": {"code": "provider_failure"}}},
])
def test_review_excludes_infrastructure_comparisons_and_unfinished_runs(tmp_path, mutation):
    store = Store(tmp_path)
    run = {**completed_question(), **mutation}
    store.save_run(run)
    with pytest.raises(ValueError):
        do_review(store, run["run_id"])
    assert store.cases()["successes"] == store.cases()["failures"] == 0


def test_review_can_count_a_completed_hermes_behavior_failure_but_revalidates_old_reviews(tmp_path):
    store = Store(tmp_path)
    run = completed_question()
    # Wrong source IDs can be a model behavior failure even if the run completes.
    run["result"]["tool_trace"] = [{"name": "read_source", "status": "error", "result": {"error": "Unknown source ID"}}]
    store.save_run(run)
    do_review(store, run["run_id"], outcome="failure")
    assert store.cases()["failures"] == 1
    # Legacy/orphaned review JSON must not manufacture eligible cases.
    invalid = completed_question("fixture-comparison")
    invalid["kind"] = "comparison"
    store.save_run(invalid)
    write_json(tmp_path / "runs" / invalid["run_id"] / "review.json", {"outcome": "success"})
    assert store.cases()["successes"] == 0
    # Revalidate eligibility when an existing run is subsequently marked failed.
    run["status"] = "error"
    store.save_run(run)
    assert store.cases()["failures"] == 0


@pytest.mark.parametrize("response", [
    {"data": []},
    {"data": [{"index": 1, "embedding": [1., 2.]}]},
    {"data": [{"index": 0, "embedding": [1.]}, {"index": 0, "embedding": [2.]}]},
    {"data": [{"index": 0, "embedding": [1., float("nan")]}, {"index": 1, "embedding": [0., 1.]}]},
    {"data": [{"index": 0, "embedding": [1.]}, {"index": 1, "embedding": [0., 1.]}]},
])
def test_malformed_embedding_outputs_are_rejected(settings, monkeypatch, response):
    # Bypass JSON encoding for NaN: this deliberately malformed provider response
    # tests adapter validation rather than the HTTP library's JSON serializer.
    model = Models(settings)
    monkeypatch.setattr(model, "post", lambda *args, **kwargs: response)
    with pytest.raises(ValueError):
        model.embed(["first", "second"])


@pytest.mark.parametrize("response", [
    {"rankings": []},
    {"rankings": [{"index": 2, "logit": 1.}]},
    {"rankings": [{"index": 0, "logit": 1.}, {"index": 0, "logit": .5}]},
    {"rankings": [{"index": 0, "logit": float("inf")}]},
    {"rankings": [{"index": 0, "logit": "high"}]},
])
def test_malformed_rerank_outputs_are_rejected(settings, monkeypatch, response):
    model = Models(settings)
    monkeypatch.setattr(model, "post", lambda *args, **kwargs: response)
    with pytest.raises(ValueError):
        model.rerank("question", ["one", "two"])


def test_fake_http_endpoint_receives_auth_but_traces_redact_credentials(settings, monkeypatch, tmp_path):
    secret = settings.token_factory_api_key.get_secret_value()
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "credential_echo": secret, "nested": {"Authorization": "Bearer " + secret}})

    mock_endpoint(monkeypatch, handler)
    model = Models(settings, tmp_path / "calls")
    model.post("agent", "https://fake.invalid/chat", "test-model", secret,
               {"messages": [{"role": "user", "content": "An ordinary fixture prompt."}]})
    assert requests[0].headers["Authorization"] == "Bearer " + secret
    assert secret not in json.dumps(model.events)
    for file in (tmp_path / "calls").glob("*.json"):
        assert secret not in file.read_text()


def test_provider_error_does_not_expose_fake_key(settings, monkeypatch, tmp_path):
    secret = settings.token_factory_api_key.get_secret_value()
    mock_endpoint(monkeypatch, lambda request: httpx.Response(401, text="Rejected credential " + secret))
    model = Models(settings, tmp_path / "calls")
    with pytest.raises(RuntimeError) as error:
        model.post("agent", "https://fake.invalid/chat", "test-model", secret, {"input": "fixture"})
    assert secret not in str(error.value)
    assert secret not in json.dumps(model.events)
    assert model.events[0]["status"] == "error"


def test_parse_never_invents_boxes_or_readable_text():
    parsed = parsed_content('{"text":"An observed phrase"}')
    assert parsed["regions"][0]["bbox_raw"] is None
    assert parsed["regions"][0]["coordinates_verified"] is False
    with pytest.raises(ValueError):
        parsed_content('{"regions":[]}')
