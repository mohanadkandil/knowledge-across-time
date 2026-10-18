"""Local review interface. Long model operations run as inspectable background jobs."""
from __future__ import annotations

import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings
from .corpus import find_page, manifest
from .engine import Engine
from .util import load_json, now, write_json


class JobRequest(BaseModel):
    action: str
    page_id: str | None = None
    question: str = Field("", max_length=16000)
    queries: list[str] | None = None
    force: bool = False


class ReviewRequest(BaseModel):
    outcome: str
    rationale: str = Field(min_length=1, max_length=16000)
    expected: str = Field(min_length=1, max_length=16000)
    category: str = Field("", max_length=300)
    reviewer: str = Field(min_length=1, max_length=300)


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or (engine.settings if engine is not None else Settings())
    engine = engine or Engine(settings)
    root = Path(engine.root).resolve()
    (root / "site").mkdir(parents=True, exist_ok=True)
    jobs: dict[str, dict] = {}
    jobs_lock = threading.RLock()
    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kat-job")

    def scrub(value):
        if isinstance(value, dict):
            return {str(k): scrub(v) for k, v in value.items()
                    if str(k).lower() not in {"image_file", "authorization", "api_key", "access_token", "x-key", "x-api-key", "hermes_repo_path", "hermes_python"}
                    and not str(k).lower().endswith("_api_key")}
        if isinstance(value, (list, tuple)):
            return [scrub(item) for item in value]
        if isinstance(value, Path):
            return "[local path]"
        if isinstance(value, str):
            for secret in settings.secrets():
                value = value.replace(secret, "[REDACTED]")
            value = value.replace(str(root), "[data]").replace(str(Path.home()), "[home]")
            value = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[REDACTED]", value)
            value = re.sub(r"(?i)([?&](?:api[_-]?key|token|signature|x-goog-signature|credential|access_token)=)[^&\s\"']+", r"\1[REDACTED]", value)
            value = re.sub(r"/(?:Users|home|private|tmp|var|etc)/[^\s\"'<>]+", "[local path]", value)
        return value

    def page(page_id: str):
        try:
            return find_page(root, page_id)
        except KeyError:
            raise HTTPException(404, "Page is not in the documented selected corpus") from None

    def run_record(run_id: str):
        try:
            engine.store._validate_run_id(run_id)
        except ValueError:
            raise HTTPException(400, "Invalid run ID") from None
        record = load_json(root / "runs" / run_id / "run.json")
        if not record:
            raise HTTPException(404, "Run not found")
        return record

    def update_job(job_id: str, **changes):
        with jobs_lock:
            jobs[job_id].update(scrub(changes))
            write_json(root / "jobs" / f"{job_id}.json", jobs[job_id])

    def execute(job_id: str, request: JobRequest):
        update_job(job_id, status="running", started_at=now())
        try:
            if request.action == "batch":
                selected = engine.pages()
                results = []
                update_job(job_id, total=len(selected), completed=0)
                for selected_page in selected:
                    selected_id = selected_page["page_id"]
                    update_job(job_id, current_page=selected_id)
                    try:
                        result = engine.compare(selected_id)
                        results.append({"page_id": selected_id, "status": result.get("status", "complete"),
                                        "abstained": result.get("abstained", False), "run_id": result.get("run_id")})
                    except Exception as error:
                        results.append({"page_id": selected_id, "status": "error", "error": {"type": type(error).__name__, "message": scrub(str(error))}})
                    update_job(job_id, completed=len(results), results=results)
                result = {"pages": results, "processed": len(results),
                          "completed": sum(r["status"] == "complete" for r in results),
                          "abstained": sum(r["status"] == "abstained" for r in results),
                          "errors": sum(r["status"] == "error" for r in results)}
            elif request.action == "archive":
                from .archive import build_archive
                result = build_archive(engine)
            elif request.action == "parse":
                result = engine.parse(request.page_id, force=request.force)
            elif request.action == "match":
                result = engine.match(request.page_id, queries=request.queries)
            elif request.action == "compare":
                result = engine.compare(request.page_id)
            else:
                result = engine.ask(request.question, page_id=request.page_id)
            update_job(job_id, status="complete", result=result, finished_at=now())
        except Exception as error:
            update_job(job_id, status="error", error={"type": type(error).__name__, "message": scrub(str(error))}, finished_at=now())

    @asynccontextmanager
    async def lifespan(app):
        yield
        pool.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="Knowledge Across Time", lifespan=lifespan)
    app.state.engine = engine
    router = APIRouter()

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        return JSONResponse(status_code=500, content={"detail": {"type": type(error).__name__, "message": scrub(str(error))}})

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @router.get("/status")
    def status():
        return scrub(engine.status())

    @router.get("/health")
    def health():
        return {"status": "ok", "note": "API process only; model endpoints are not verified"}

    @router.get("/pages")
    def pages():
        selected = manifest(root)
        return scrub({"pages": engine.pages(), "selection_method": selected.get("selection_method"), "bias": selected.get("bias"), "revision": selected.get("revision")})

    @router.get("/pages/{page_id}")
    @router.get("/page/{page_id}")
    def page_details(page_id: str):
        selected = page(page_id)
        canonical = selected["page_id"]
        folder = engine.page_dir(canonical)
        return scrub({"page": selected, "parse": load_json(folder / "parse.json"),
                      "parse_error": load_json(folder / "parse-error.json"), "matches": load_json(folder / "matches.json"),
                      "comparison": load_json(folder / "comparison.json"), "sources": engine.store.page_sources(canonical),
                      "archive": {"html": f"/archive/pages/{canonical}.html" if (root / "site" / "pages" / f"{canonical}.html").is_file() else None,
                                  "pdf": f"/archive/documents/{canonical}.pdf" if (root / "site" / "documents" / f"{canonical}.pdf").is_file() else None}})

    @router.get("/pages/{page_id}/image")
    @router.get("/image/{page_id}")
    def original_image(page_id: str):
        selected = page(page_id)
        image = Path(selected["image_file"])
        if not image.is_file():
            raise HTTPException(404, "Selected original scan is unavailable locally")
        return FileResponse(image, media_type="image/png" if image.suffix.lower() == ".png" else "image/jpeg")

    @router.get("/sources/{source_id}")
    @router.get("/source/{source_id}")
    def source(source_id: str):
        if len(source_id) > 500:
            raise HTTPException(400, "Invalid source ID")
        try:
            return scrub(engine.store.source(source_id))
        except KeyError:
            raise HTTPException(404, "Source is not in the verified local source registry") from None

    @router.get("/runs")
    def runs():
        return scrub({"runs": engine.store.runs()})

    @router.get("/runs/{run_id}")
    @router.get("/run/{run_id}")
    def run(run_id: str):
        record = run_record(run_id)
        return scrub({**record, "review": load_json(root / "runs" / run_id / "review.json"),
                      "reviewable": engine.store._reviewable(record)})

    @router.get("/cases")
    def cases():
        return scrub(engine.store.cases())

    @router.post("/runs/{run_id}/review")
    def review(run_id: str, request: ReviewRequest):
        run_record(run_id)
        try:
            return scrub(engine.store.review(run_id, request.outcome, request.rationale, request.expected, request.category, request.reviewer))
        except ValueError as error:
            raise HTTPException(400, scrub(str(error))) from None

    @router.post("/jobs", status_code=202)
    def create_job(request: JobRequest):
        if request.action not in {"parse", "match", "compare", "ask", "batch", "archive"}:
            raise HTTPException(400, "Action must be parse, match, compare, ask, batch, or archive")
        if request.action in {"parse", "match", "compare"} and not request.page_id:
            raise HTTPException(400, "Select a page first")
        if request.page_id:
            request.page_id = page(request.page_id)["page_id"]
        if request.action == "ask" and not request.question.strip():
            raise HTTPException(400, "A question is required")
        if request.queries is not None and (not 1 <= len(request.queries) <= 4 or any(not q.strip() or len(q) > 150 for q in request.queries)):
            raise HTTPException(400, "Provide one to four nonempty search phrases, at most 150 characters each")
        # Configuration is only a readiness check, never a claim that endpoints work.
        required = {"parse": ["parse"], "match": ["parse", "embed", "rerank", "agent"],
                    "compare": ["parse", "embed", "rerank", "agent"], "batch": ["parse", "embed", "rerank", "agent"],
                    "ask": ["agent", "hermes", "embed", "rerank"], "archive": []}[request.action]
        readiness = settings.readiness()
        missing = [key for key in required if not readiness.get(key, {}).get("configured")]
        if missing:
            raise HTTPException(409, "Missing configuration: " + ", ".join(missing) + ". Configure local services before running this action.")
        with jobs_lock:
            if sum(job["status"] in {"queued", "running"} for job in jobs.values()) >= 4:
                raise HTTPException(409, "Four jobs are already queued or running; wait for one to finish")
            job_id = "job-" + uuid.uuid4().hex
            jobs[job_id] = {"job_id": job_id, "action": request.action, "page_id": request.page_id,
                            "status": "queued", "created_at": now()}
            write_json(root / "jobs" / f"{job_id}.json", jobs[job_id])
        pool.submit(execute, job_id, request)
        return scrub(jobs[job_id].copy())

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str):
        if not re.fullmatch(r"job-[0-9a-f]{32}", job_id):
            raise HTTPException(400, "Invalid job ID")
        with jobs_lock:
            record = jobs.get(job_id) or load_json(root / "jobs" / f"{job_id}.json")
            if not record:
                raise HTTPException(404, "Job not found")
            record = record.copy()
        if job_id not in jobs and record["status"] in {"queued", "running"}:
            record.update(status="interrupted", note="The server restarted; this job was not automatically resumed")
        return scrub(record)

    app.include_router(router, prefix="/api")
    app.include_router(router, include_in_schema=False)
    # check_dir=False lets the archive appear after a background build.
    app.mount("/archive", StaticFiles(directory=root / "site", html=True, check_dir=False), name="archive")
    return app
