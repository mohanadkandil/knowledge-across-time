# Setup and reproducible execution

The **18 October participant brief** requires all four named models, 100 selected Britannica pages, a static archive with **compiled LaTeX documents**, comparisons, a real Hermes agent, three successful and three failing cases, and a **3-minute video**. This supersedes earlier provisional notes. The [public starter](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge) is inspected at commit `88abda0d1882eb56a5cd78bc226f1fbc929cc33b`.

## Application and accounts

From `knowledge-across-time/`:

```sh
uv sync --python 3.12 --extra dev --frozen
cp .env.example .env
uv run kat --help
uv run kat doctor
```

AI Cloud and Token Factory need separate accounts. Run the retrieval models on Cloud and use your own Token Factory key for Super VL. The supplied shared Wikipedia and Parse services require no participant key. Keep `.env` local.

| Role | Exact model ID |
|---|---|
| Agent | `nvidia/Nemotron-3.5-Super-VL` |
| Parser | `nvidia/nemotron-3.5-parse` |
| Embedder | `nvidia/llama-nemotron-embed-vl-1b-v2` |
| Reranker | `nvidia/llama-nemotron-rerank-vl-1b-v2` |

The `.env.example` uses the starter's `SUPER_*`, `PARSE_BASE_URL` and `RETRIEVAL_BASE_URL` names. The app also accepts the full endpoint names below:

```dotenv
KAT_DATA_DIR=./data
TOKEN_FACTORY_BASE_URL=https://api.tokenfactory.nebius.com/v1
TOKEN_FACTORY_API_KEY=YOUR_OWN_KEY
NEMOTRON_AGENT_MODEL=nvidia/Nemotron-3.5-Super-VL
PARSE_API_URL=https://port8000-kh2kceraevwe0k1.tunnel.applications.uk-south2.nebius.cloud/v1/chat/completions
PARSE_MODEL=nvidia/nemotron-3.5-parse
PARSE_API_KEY=
WIKIPEDIA_API_URL=https://port8000-rks0xavparpzq59.tunnel.applications.uk-south2.nebius.cloud
EMBED_API_URL=http://127.0.0.1:8000/v1/embeddings
EMBED_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2
EMBED_PROTOCOL=challenge
EMBED_API_KEY=
RERANK_API_URL=http://127.0.0.1:8000/v1/rerank
RERANK_MODEL=nvidia/llama-nemotron-rerank-vl-1b-v2
RERANK_PROTOCOL=challenge
RERANK_API_KEY=
```

Use the challenge protocol in the current `.env.example`, **not a generic NIM request**. Supplied URLs and configured model names do not establish working inference.

## Retrieval Docker service

Build the supplied custom recipe on a Linux amd64 builder, or use an organizer-provided image **by its actual digest**. Do not invent an image name:

```sh
docker buildx build --platform linux/amd64 --load \
  -t nemotron-challenge-models:local infra/model-service
export RETRIEVAL_IMAGE=nemotron-challenge-models:local
docker run --rm --name nemotron-models --gpus device=0 \
  --read-only --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:8000:8000 "$RETRIEVAL_IMAGE"
```

Allow 60 GB builder disk, a CUDA 12.8-compatible NVIDIA driver and NVIDIA Container Toolkit. The documented reference GPU has 96 GB; another BF16 GPU needs its own input/memory test. Keep one service process per GPU. Build/package checks do not execute inference. See the [model-service guide](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/88abda0d1882eb56a5cd78bc226f1fbc929cc33b/docs/model-service.md).

The pinned [Dockerfile](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/88abda0d1882eb56a5cd78bc226f1fbc929cc33b/infra/model-service/Dockerfile) uses PyTorch 2.8.0/CUDA 12.8. [Model pins](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/88abda0d1882eb56a5cd78bc226f1fbc929cc33b/infra/model-service/model_pins.py): embedding `582e3bf72aee355e3c59ed89de53543c5b0657ee`, reranking `b8a9987b05b75db5ad949c825cbcbf6eb7c48b5a`; vectors 2048-dimensional.

```sh
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
curl --fail http://127.0.0.1:8000/v1/models
uv run python infra/model-service/smoke_gpu.py \
  --base-url http://127.0.0.1:8000/v1 --receipt data/verification/model-service-smoke.json
```

`/health` only checks the web process. Preserve a real GPU smoke receipt and inspect `/ready` for GPU/model warmup. No Cloud deployment or GPU execution is claimed complete here. When running on a Cloud VM, use the agreed private tunnel/SSH forwarding and set full application URLs accordingly.

The [actual contracts](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/88abda0d1882eb56a5cd78bc226f1fbc929cc33b/infra/model-service/contracts.py) accept embedding `input_type=query|document`, up to 16 inputs, and image records `{image: "data:image/png;base64,..."}`. Reranking accepts a string query, `documents`, optional `top_n`, and up to 32 documents. Extra `encoding_format`, `modality` and `embedding_type` fields are rejected by this service. Scores are raw logits, not probabilities. Chunk content to fit actual token limits; invalid requests need correction, not blind retries.

## Isolated Hermes

```sh
git clone https://github.com/NousResearch/hermes-agent.git .vendor/hermes-agent
git -C .vendor/hermes-agent checkout 354ad3d48786f2978c49be88f28c13d78fa0b6e0
uv venv --python 3.14 .venv-hermes
uv pip install --python .venv-hermes/bin/python -e .vendor/hermes-agent
```

Set absolute `HERMES_REPO_PATH` and `HERMES_PYTHON` paths in `.env`. The upstream manifest pins direct dependencies; its `uv.lock` supports `uv sync --frozen --no-dev` for the fully locked upstream environment. This version's dependencies are conditional on Python 3.14; the app's 3.12 environment is insufficient. It requires at least 64K supported model context.

Our real Hermes subprocess exposes only `search_sources`, `read_source`, `compare_page`, with a temporary profile and actual transcripts. It does not pretend the starter's unfinished handler is a completed agent. See [integration details](hermes.md). Import/registration checks do not establish answer quality.

## Verification and execution

```sh
uv run kat doctor
uv run kat doctor --live
# Explicit, potentially billed inference probes after services are ready:
uv run kat doctor --live --inference --page 57
uv run kat status
uv run kat prepare
# Or check an existing exact Parquet file:
uv run kat prepare --parquet /absolute/path/to/source.parquet
uv run kat parse 57
uv run kat match 57
uv run kat compare 57
uv run kat batch --stage compare
uv run kat ask "Which differences are language changes, and which are factual disagreements?" --page 57
uv run kat archive
uv run kat serve
```

Doctor separates configuration, catalog access/imports/readiness, and explicitly requested inference. Its artificial readiness fixtures never create agent evaluation cases. Reports stay below `data/verification`. Recheck after keys/deployments/models change. HTTP success and server-reported names do not independently attest remote weights.

Preparation fixes 100 scans with disclosed 80/20 page-class sampling and manual seeds 57,59,1776. Source revision: `309f765b1ecc83e0a7f7762e44b4a927a7555443`; file SHA256: `08f167015db23cb027995b2b6a6bc953b01d7c1ddf667de950465cc2b601af5c`. The brief permits hand-selected or random 100-page samples. Retain failures rather than replacing difficult pages.

**Use the shared pre-indexed Wikipedia API first; no full index build is required.** It supplies lexical candidates and paginated article text. Follow `next_offset`, verify full text hashes and preserve response revision/license/provenance. It supplies neither semantic matching nor an answer key; our embedder/reranker still decide candidates downstream. The shared response provenance governs this mode. The earlier local Kaggle version 5 reader is a separate fallback; do not claim the two snapshots are identical. `kat wiki-index` is only for an explicitly chosen local fallback. See the [organizer Wikipedia guide](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/88abda0d1882eb56a5cd78bc226f1fbc929cc33b/docs/wikipedia-api.md).

`batch` persists every page outcome and continues after failures, exiting nonzero on errors. `archive` pairs scans/regions with LaTeX compilation artifacts and failures. Source `.tex` alone is not compiled output. `serve` binds to 127.0.0.1:8130. Literal quote presence is not semantic entailment or OCR accuracy; inspect the evidence.

## Human review and submission

After inspecting a completed live Hermes question run:

```sh
uv run kat review question-RUN_ID --outcome success \
  --rationale "Explain the observed supported answer." \
  --expected "State the desired behavior." --reviewer "Reviewer name"
uv run kat review question-OTHER_ID --outcome failure --category unsupported-inference \
  --rationale "Identify the actual unsupported conclusion." \
  --expected "State the desired correction or abstention." --reviewer "Reviewer name"
uv run kat export --output submission.zip
```

These are format examples, not existing cases. Required cases: **three successes and three failures from completed live Hermes question runs**, human reviewed. Offline fixtures, smoke probes, configuration errors and failed-service runs do not count.

Export includes selected provenance/results/evidence, real traces/reviews, code/config template and generated static-site/LaTeX artifacts. It omits `.env`, bulk Parquet, SQLite/LanceDB, full article caches and dependency environments. The site may include selected 100 scan assets, not the whole dataset. Inspect the ZIP before publishing; retain source attribution/licenses and label generated analysis.

The checklist reports incomplete work explicitly. Record the **3-minute video** showing successful and failed cases and supply a GitHub repository containing the solution, static website, compiled LaTeX, analysis and 3+3 cases. This tool does not generate/upload the video or publish the repository.

## Structured comparison output

Structured comparisons send the Pydantic JSON schema through Token Factory `response_format`, with thinking disabled for these bounded extraction calls. The exact Super VL endpoint passed a live schema probe and two previously malformed comparisons completed with this setting. This enforces output structure; source IDs, exact quotes and semantic support still need separate checks. See the [provider documentation](https://docs.tokenfactory.nebius.com/ai-models-inference/json). Hermes remains a tool-using agent with free-form answers.
