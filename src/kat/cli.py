"""Reproducible CLI for the actual baseline; no offline success substitutes."""
from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Annotated, Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import uuid
import zipfile

import httpx
import typer

from .config import Settings
from .corpus import find_page, manifest, prepare as prepare_corpus
from .engine import Engine
from .hermes_bridge import HERMES_COMMIT, run_hermes
from .services import Models, image_url
from .util import digest, load_json, now, write_json

app = typer.Typer(no_args_is_help=True, help="Knowledge Across Time: pinned sources, real models and reviewable evidence.")


def _safe(value: Any, settings: Settings) -> Any:
    if isinstance(value, dict):
        return {str(k): _safe(v, settings) for k, v in value.items()
                if not any(part in str(k).lower() for part in ("api_key", "authorization", "access_token", "password", "secret"))}
    if isinstance(value, (list, tuple)):
        return [_safe(v, settings) for v in value]
    if isinstance(value, str):
        for secret in settings.secrets():
            value = value.replace(secret, "[REDACTED]")
        if value.startswith(("https://", "http://")):
            parsed = urlsplit(value)
            # Signed URLs and userinfo never belong in a submission package.
            public_query = urlencode([(k, v) for k, v in parse_qsl(parsed.query)
                                      if k in {"datasetVersionNumber", "row", "page", "raw"}])
            value = urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], parsed.path, public_query, ""))
        return value
    return value


def _print(value: Any, settings: Settings | None = None) -> None:
    typer.echo(json.dumps(_safe(value, settings or Settings()), indent=2, ensure_ascii=False, default=str))


def _call(action: Callable, settings: Settings | None = None) -> Any:
    try:
        result = action()
        _print(result, settings)
        return result
    except Exception as exc:
        _print({"status": "error", "error_type": type(exc).__name__, "message": str(exc)}, settings)
        raise typer.Exit(1) from None


def _identity(settings: Settings) -> str:
    return digest(json.dumps({key: getattr(settings, key, None) for key in (
        "nemotron_agent_model", "token_factory_base_url", "parse_api_url", "parse_model",
        "embed_api_url", "embed_model", "embed_protocol", "rerank_api_url", "rerank_model",
        "rerank_protocol", "hermes_repo_path", "hermes_python", "wikipedia_api_url")}, sort_keys=True))


def _evidence(engine: Engine) -> dict:
    """Observed successful adapter records; not a claim of model authenticity."""
    roles = {name: {"successful_calls": 0, "model": model} for name, model in (
        ("agent", engine.settings.nemotron_agent_model), ("parse", engine.settings.parse_model),
        ("embed", engine.settings.embed_model), ("rerank", engine.settings.rerank_model))}
    paths = list((engine.root / "pages").glob("*/*-calls/*.json"))
    paths += list((engine.root / "runs").glob("*/api/*.json"))
    for path in paths:
        event = load_json(path, {})
        role = event.get("role")
        if role in roles and event.get("status") == "ok" and event.get("model") == roles[role]["model"]:
            roles[role]["successful_calls"] += 1
    runs = engine.store.runs()
    hermes = [r for r in runs if r.get("kind") == "question" and r.get("status") == "complete"
              and r.get("execution") == "live_models" and not r.get("error")
              and r.get("result", {}).get("framework") == "hermes"
              and r.get("result", {}).get("completed") is True and not r.get("result", {}).get("error")
              and bool(str(r.get("result", {}).get("answer", "")).strip())
              and r.get("result", {}).get("model") == engine.settings.nemotron_agent_model]
    roles["hermes"] = {"completed_question_runs": len(hermes), "commit_expected": HERMES_COMMIT}
    roles["vector_database"] = {"embedding_identity": engine.store.stats().get("embedding_identity")}
    return {"roles": roles, "all_required_traces_present":
            all(roles[r]["successful_calls"] > 0 for r in ("agent", "parse", "embed", "rerank"))
            and bool(hermes) and bool(roles["vector_database"]["embedding_identity"]),
            "note": "Successful recorded calls establish execution, not independent proof of the remote model's identity or answer quality."}


@app.command()
def prepare(parquet: Annotated[Path | None, typer.Option(help="Existing exact pinned Britannica Parquet; hash is checked.")] = None):
    """Download/check the pinned Britannica file and select the documented 100 pages."""
    settings = Settings()
    _call(lambda: prepare_corpus(settings.data_dir.resolve(), parquet), settings)


@app.command("wiki-index")
def wiki_index(workers: Annotated[int, typer.Option(min=1, max=8)] = 3,
               shard_limit: Annotated[int | None, typer.Option(min=0, help="Smoke-test limit; catalog remains explicitly partial.")] = None):
    """Fallback only: build a local catalog; the organizer's shared index is preferred."""
    def action():
        engine = Engine(Settings())
        if not hasattr(engine.wiki, "build_catalog"):
            return {"status": "not_required", "message": "The configured organizer API already provides the index.", "wikipedia": engine.wiki.stats()}
        return engine.wiki.build_catalog(workers=workers, shard_limit=shard_limit)
    _call(action)


@app.command()
def status():
    """Show persisted progress and trace evidence without making model requests."""
    def action():
        engine = Engine(Settings())
        result = engine.status()
        result["execution_evidence"] = _evidence(engine)
        result["last_doctor"] = load_json(engine.root / "verification" / "doctor.json")
        if result["last_doctor"]:
            result["last_doctor"]["matches_current_configuration"] = result["last_doctor"].get("configuration_identity") == _identity(engine.settings)
        return result
    _call(action)


@app.command()
def doctor(live: Annotated[bool, typer.Option(help="Query Token Factory's authenticated model catalog and import the isolated Hermes runtime.")] = False,
           inference: Annotated[bool, typer.Option(help="Also make metered Parse/Embed/Rerank/agent/Hermes smoke calls; requires --live.")] = False,
           page: Annotated[str, typer.Option(help="Selected scan row/page ID for image probes; defaults to row 57.")] = "57"):
    """Distinguish configured, importable, reachable and actually exercised services."""
    if inference and not live:
        raise typer.BadParameter("--inference requires --live")
    def action():
        engine = Engine(Settings()); settings = engine.settings
        report = {"checked_at": now(), "configuration_identity": _identity(settings),
                  "stack": settings.readiness(), "live_requested": live, "inference_requested": inference,
                  "checks": {}, "recorded_execution_evidence": _evidence(engine),
                  "note": "Configuration and catalog presence are not live inference verification. Smoke checks are not reviewed agent QA cases."}
        for name, item in report["stack"].items():
            item["live_verified"] = False
            item["verification"] = "not_tested"
        def check(name, fn):
            try:
                value = fn()
                report["checks"][name] = {"status": "ok", "result": value}
            except Exception as exc:
                report["checks"][name] = {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}
        check("local_store", lambda: {"sources": engine.store.stats(), "lancedb_version": importlib.metadata.version("lancedb")})
        if live:
            def catalog():
                if not settings.token_factory_api_key.get_secret_value() or not settings.nemotron_agent_model:
                    raise ValueError("Configure TOKEN_FACTORY_API_KEY and NEMOTRON_AGENT_MODEL first")
                response = httpx.get(settings.token_factory_base_url.rstrip("/") + "/models",
                    headers={"Authorization": "Bearer " + settings.token_factory_api_key.get_secret_value()}, timeout=settings.http_timeout)
                response.raise_for_status()
                ids = {r["id"] for r in response.json().get("data", [])}
                if settings.nemotron_agent_model not in ids:
                    raise ValueError("The exact configured agent model is absent from this key's catalog")
                return {"configured_model_present": True, "models_available": len(ids), "inference_verified": False}
            check("token_factory_catalog", catalog)
            def hermes_import():
                if not settings.hermes_python or not settings.hermes_repo_path:
                    raise ValueError("Configure HERMES_PYTHON and HERMES_REPO_PATH")
                script = "import sys;sys.path.insert(0,sys.argv[1]);from run_agent import AIAgent;from tools.registry import registry;print('KAT_IMPORT_OK')"
                with tempfile.TemporaryDirectory(prefix="kat-doctor-") as home:
                    env = dict(os.environ, HERMES_HOME=home)
                    result = subprocess.run([settings.hermes_python, "-c", script, settings.hermes_repo_path],
                        capture_output=True, text=True, env=env, timeout=60)
                if result.returncode or "KAT_IMPORT_OK" not in result.stdout:
                    raise RuntimeError("Hermes runtime import failed; follow docs/hermes.md (stderr is not exposed)")
                return {"importable": True, "inference_verified": False}
            check("hermes_import", hermes_import)
            wiki_url = getattr(settings, "wikipedia_api_url", "")
            if wiki_url:
                def shared_wikipedia():
                    ready = httpx.get(wiki_url.rstrip("/") + "/ready", timeout=settings.http_timeout)
                    ready.raise_for_status()
                    corpus = httpx.get(wiki_url.rstrip("/") + "/v1/corpus", timeout=settings.http_timeout)
                    corpus.raise_for_status()
                    return {"ready": ready.json(), "corpus": corpus.json(), "semantic_models_verified": False}
                check("shared_wikipedia", shared_wikipedia)
            retrieval_base = settings.embed_api_url.rsplit("/v1/", 1)[0] if "/v1/" in settings.embed_api_url else ""
            if retrieval_base:
                def retrieval_ready():
                    headers = {"Authorization": "Bearer " + settings.embed_api_key.get_secret_value()} if settings.embed_api_key.get_secret_value() else {}
                    response = httpx.get(retrieval_base + "/ready", headers=headers, timeout=settings.http_timeout)
                    response.raise_for_status()
                    return {"readiness": response.json(), "note": "Inspect production/GPU/model-revision fields; HTTP readiness alone is not our inference receipt."}
                check("retrieval_service_ready", retrieval_ready)
        if inference:
            folder = engine.root / "verification" / ("smoke-" + uuid.uuid4().hex)
            models = Models(settings, folder)
            def probe(role, fn):
                def execute():
                    value = fn()
                    report["stack"][role].update(live_verified=True, verification="smoke_call_succeeded")
                    return value
                check(role + "_inference", execute)
            probe("agent", lambda: {"response": models.chat([{"role": "user", "content": "Reply with the word READY."}], max_tokens=64)})
            probe("parse", lambda: {"characters": len(models.parse(Path(find_page(engine.root, page)["image_file"]))["text"])})
            def embeddings():
                vectors = models.embed(["A historical source states a claim.", "A modern source describes the same topic."])
                query = models.embed(["What changed?"], query=True)
                output = {"passages": len(vectors), "dimensions": len(vectors[0]), "query_dimensions": len(query[0])}
                if settings.embed_protocol in {"nim_vl", "challenge", "challenge_vl"}:
                    image = image_url(Path(find_page(engine.root, page)["image_file"]))
                    output["image_dimensions"] = len(models.embed([image], modality="image")[0])
                return output
            probe("embed", embeddings)
            probe("rerank", lambda: models.rerank("historical knowledge", ["A historical encyclopedia entry.", "A football score."], limit=2))
            def hermes():
                result = run_hermes("Search for the readiness source, read it and report its text with its source ID.",
                    model=settings.nemotron_agent_model, base_url=settings.token_factory_base_url,
                    api_key=settings.token_factory_api_key.get_secret_value(),
                    search=lambda query, limit=6: [{"source_id": "doctor-source", "text": "Adapter readiness check only."}],
                    read=lambda source_id: {"source_id": source_id, "text": "Adapter readiness check only."},
                    compare=lambda page: {"note": "No historical comparison in a readiness probe."}, max_iterations=4)
                if result.get("error"):
                    raise RuntimeError(result["error"]["message"])
                write_json(folder / "hermes.json", _safe(result, settings))
                return {"framework": result["framework"], "commit": result.get("framework_commit"), "tool_calls": len(result.get("tool_trace", []))}
            probe("hermes", hermes)
            report["note"] += " Probe documents are artificial readiness fixtures, never corpus evidence or evaluation cases."
        write_json(engine.root / "verification" / "doctor.json", _safe(report, settings))
        return report
    result = _call(action)
    if any(item["status"] == "error" for item in result["checks"].values()):
        raise typer.Exit(1)


@app.command("parse")
def parse_page(page: str, force: Annotated[bool, typer.Option(help="Explicitly replace the cached parse.")] = False,
               index: Annotated[bool, typer.Option(help="Also index with the deployed embedder; extraction alone is the default.")] = False):
    """Extract a selected page using its row number or full page ID."""
    _call(lambda: Engine(Settings()).parse(page, force=force, index=index))


@app.command("match")
def match_page(page: str, query: Annotated[list[str] | None, typer.Option("--query", help="Repeat to supply explicit candidate-search phrases.")] = None):
    """Match a page through title discovery, embeddings, LanceDB and reranking."""
    _call(lambda: Engine(Settings()).match(page, queries=query))


@app.command("compare")
def compare_page(page: str):
    """Produce a structured source-grounded comparison and literal-quote checks."""
    _call(lambda: Engine(Settings()).compare(page))


@app.command()
def batch(stage: Annotated[str, typer.Option(help="parse, match or compare; compare runs missing prerequisites.")] = "compare"):
    """Process every selected page; persist failures and continue to the next page."""
    if stage not in {"parse", "match", "compare"}:
        raise typer.BadParameter("--stage must be parse, match or compare")
    settings = Settings(); engine = Engine(settings)
    pages = manifest(engine.root)["pages"]
    if not pages:
        _print({"status": "error", "message": "Run kat prepare first."}, settings)
        raise typer.Exit(1)
    record = {"batch_id": "batch-" + uuid.uuid4().hex, "stage": stage, "started_at": now(),
              "selected_pages": len(pages), "rows": [], "note": "Every selected page is retained, including failures; this is not an accuracy score."}
    path = engine.root / "batches" / (record["batch_id"] + ".json")
    for index, page in enumerate(pages, 1):
        try:
            result = getattr(engine, stage)(page["page_id"])
            row = {"page_id": page["page_id"], "row_index": page["row_index"], "status": "complete"}
            if stage == "match" and not result.get("matches"):
                row.update(status="no_match", uncertainty=result.get("uncertainty"))
            if result.get("run_id"):
                row["run_id"] = result["run_id"]
        except Exception as exc:
            row = {"page_id": page["page_id"], "row_index": page["row_index"], "status": "error", "error_type": type(exc).__name__, "message": str(exc)}
        record["rows"].append(_safe(row, settings))
        write_json(path, record)
        typer.echo(f"{index}/{len(pages)} {page['page_id']} {row['status']}", err=True)
    record.update(finished_at=now(), completed=sum(r["status"] == "complete" for r in record["rows"]),
                  failed=sum(r["status"] == "error" for r in record["rows"]), no_match=sum(r["status"] == "no_match" for r in record["rows"]))
    write_json(path, record); _print(record, settings)
    if record["failed"]:
        raise typer.Exit(1)


@app.command()
def ask(question: str, page: Annotated[str | None, typer.Option(help="Optional selected Britannica page context.")] = None):
    """Run the real Hermes source-tool agent; retain its answer and tool transcript."""
    result = _call(lambda: Engine(Settings()).ask(question, page_id=page))
    if result.get("status") != "complete":
        raise typer.Exit(1)


@app.command()
def review(run_id: str, outcome: Annotated[str, typer.Option(help="success or failure")],
           rationale: Annotated[str, typer.Option(help="Human explanation of the observed outcome.")],
           expected: Annotated[str, typer.Option(help="What the agent should have done.")],
           reviewer: Annotated[str, typer.Option(help="Name/identifier of the human reviewer.")],
           category: Annotated[str, typer.Option(help="Failure category; required for failures.")] = ""):
    """Record human review of a completed live Hermes question run."""
    _call(lambda: Engine(Settings()).store.review(run_id, outcome, rationale, expected, category, reviewer))


@app.command()
def archive():
    """Build the static scan/region archive and compile its LaTeX documents."""
    def action():
        from .archive import build_archive
        return build_archive(Engine(Settings()))
    _call(action)


@app.command()
def export(output: Annotated[Path, typer.Option(help="Destination ZIP; existing files are not overwritten.")] = Path("submission.zip")):
    """Package selected provenance, results and reviews; omit keys and bulk corpus/index files."""
    def action():
        if output.exists():
            raise ValueError("Output already exists; choose a new --output path")
        engine = Engine(Settings()); settings = engine.settings
        state = engine.status(); evidence = _evidence(engine); cases = engine.store.cases()
        checklist = {"selected_100": state["pages_selected"] == 100,
                     "parsed_100": state["pages_parsed"] == 100, "compared_100": state["pages_compared"] == 100,
                     "human_reviewed_successes_at_least_3": cases["successes"] >= 3,
                     "human_reviewed_failures_at_least_3": cases["failures"] >= 3,
                     "all_required_stack_configured": all(r["configured"] for r in settings.readiness().values()),
                     "all_required_execution_traces_present": evidence["all_required_traces_present"],
                     "static_site_index_present": (engine.root / "site" / "index.html").is_file(),
                     "compiled_latex_pdfs_present": bool(list((engine.root / "site").rglob("*.pdf"))),
                     "compiled_documents_cover_100_selected_pages": state["pages_selected"] == 100 and len(list((engine.root / "site").rglob("*.pdf"))) >= 100,
                     "video": "Not generated or validated by this exporter: supply the organizer brief's 3-minute video separately."}
        project = Path(__file__).resolve().parents[2]
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            def json_file(name, value):
                archive.writestr(name, json.dumps(_safe(value, settings), indent=2, ensure_ascii=False, default=str))
            json_file("submission/checklist.json", checklist)
            json_file("submission/status.json", state)
            json_file("submission/execution-evidence.json", evidence)
            json_file("submission/reviewed-cases.json", cases)
            selected = manifest(engine.root)
            for page in selected["pages"]:
                page["image_file"] = "not_bundled/" + Path(page["image_file"]).name
            json_file("data/britannica/manifest.json", selected)
            # Whitelist small selected artifacts; no parquet, SQLite, LanceDB,
            # image corpus, full cached Wikipedia articles, .env or user home.
            patterns = ["pages/*/parse.json", "pages/*/parse-error.json", "pages/*/matches.json", "pages/*/comparison.json",
                        "pages/*/*-calls/*.json", "runs/*/run.json", "runs/*/review.json", "runs/*/api/*.json",
                        "batches/*.json", "verification/*.json", "verification/*/*.json", "wiki/manifest-v5.json", "wiki/catalog-status.json", "wiki/verified-targets.json"]
            for pattern in patterns:
                for path in sorted(engine.root.glob(pattern)):
                    if path.is_file() and not path.is_symlink():
                        json_file("data/" + path.relative_to(engine.root).as_posix(), load_json(path))
            # The required static deliverable may include only the selected
            # scan assets and compiled documents generated by build_archive.
            for site in (engine.root / "site", project / "site"):
                if not site.is_dir():
                    continue
                for path in sorted(site.rglob("*")):
                    if path.is_file() and not path.is_symlink() and path.suffix.lower() in {".pdf", ".tex", ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".svg", ".txt"}:
                        name = "site/" + path.relative_to(site).as_posix()
                        if name in archive.namelist():
                            continue
                        if path.suffix.lower() == ".json":
                            json_file(name, load_json(path))
                        elif path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
                            archive.writestr(name, path.read_bytes())
                        else:
                            text = path.read_text()
                            for secret in settings.secrets():
                                text = text.replace(secret, "[REDACTED]")
                            archive.writestr(name, text)
            used = set()
            for path in (engine.root / "pages").glob("*/comparison.json"):
                used.update(load_json(path, {}).get("source_ids", []))
            for run in engine.store.runs():
                used.update(c["source_id"] for c in run.get("citation_checks", []) if c.get("exists"))
            sources = []
            for source_id in sorted(used):
                try:
                    sources.append(engine.store.source(source_id))
                except KeyError:
                    sources.append({"id": source_id, "missing": True})
            json_file("data/selected-evidence.json", sources)
            for name in ["README.md", "ATTRIBUTION.md", "LICENSE", "pyproject.toml", "uv.lock", ".env.example", ".gitignore"]:
                path = project / name
                if path.is_file() and not path.is_symlink():
                    text = path.read_text()
                    for secret in settings.secrets():
                        text = text.replace(secret, "[REDACTED]")
                    archive.writestr("project/" + name, text)
            for directory, extensions in [("src", {".py", ".html", ".css", ".js"}), ("docs", {".md"}), ("tests", {".py"})]:
                for path in sorted((project / directory).rglob("*")):
                    if path.is_file() and not path.is_symlink() and (path.suffix in extensions or path.name == "LICENSE"):
                        text = path.read_text()
                        for secret in settings.secrets():
                            text = text.replace(secret, "[REDACTED]")
                        archive.writestr("project/" + path.relative_to(project).as_posix(), text)
            json_file("submission/export.json", {"created_at": now(), "scope": "Selected evidence and results only; original image/corpus/index files omitted.",
                      "checklist_complete": all(v is True for k, v in checklist.items() if k != "video"), "video_artifacts_included": False})
        return {"output": str(output.resolve()), "bytes": output.stat().st_size, "checklist": checklist,
                "note": "Exporting incomplete work is permitted; missing deliverables stay explicit in checklist.json."}
    _call(action)


@app.command()
def serve(port: Annotated[int, typer.Option(min=1, max=65535)] = 8130):
    """Serve the FastAPI app on localhost only."""
    import uvicorn
    uvicorn.run("kat.api:create_app", factory=True, host="127.0.0.1", port=port)
