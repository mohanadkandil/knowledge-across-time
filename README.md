# Knowledge Across Time

A research baseline for comparing 100 documented historical Britannica scans with evidence from the required pinned Wikipedia corpus. It separates changes in language, knowledge and coverage, retains uncertainty, and exposes the original evidence for human review.

The required stack is **Nemotron Parse 3.5**, `nvidia/llama-nemotron-embed-vl-1b-v2`, `nvidia/llama-nemotron-rerank-vl-1b-v2`, `nvidia/Nemotron-3.5-Super-VL` through Token Factory, LanceDB and **the real Hermes Agent framework**. The 18 October brief requires a static archive with **compiled LaTeX documents** and a **3-minute video**. Missing services fail explicitly; there is no substitute model or fabricated success path.

## Run

```sh
uv sync --python 3.12 --extra dev --frozen
cp -n .env.example .env
# Configure shared services, team retrieval container, own Token Factory key and Hermes runtime.
uv run kat doctor
uv run kat prepare
uv run kat parse 57
uv run kat compare 57
uv run kat archive
uv run kat serve
```

For the native interactive Hermes terminal, run `uv run kat hermes`. It loads the corpus plugin, keeps follow-up questions in the same session, and uses Super VL through Token Factory. See the [Hermes guide](docs/hermes.md#native-interactive-terminal).

The server binds to [localhost:8130](http://127.0.0.1:8130). Follow the [setup guide](docs/setup.md) for the exact corpus pins, model contracts, isolated Python 3.14 Hermes installation, verification commands and complete CLI. `uv run kat --help` lists available commands.

Read [the architecture](docs/architecture.md) for the CPU/GPU layers and [the acceptance checklist](docs/rubric.md) for the judging requirements. The [creative research](docs/creative-research.md) is a proposed extension.

## Evidence and progress

- Britannica selection is fixed before model evaluation: 100 scans, disclosed sampling procedure, scan hashes and original dataset rows. Failed parses and uncertain matches remain in the denominator.
- Prefer the organizer's pre-indexed Wikipedia API: lexical candidates and paginated text with returned revision/checksum provenance, followed by our semantic retrieval and reranking. The earlier Kaggle version 5 local reader is a separate fallback, not an identical snapshot or a required initial index build.
- Comparisons retain model calls, source IDs, quotes, uncertainty and literal-quote checks. Literal presence is not proof that a passage supports the generated claim.
- Questions run through [real Hermes](docs/hermes.md) with exactly three local source tools. Transcript/tool traces and model configuration are retained.
- Document three useful comparisons and three clear failure cases from **completed live Hermes question runs**, with source inspection. The [actual casebook](docs/actual-cases.md) labels automated inspection and qualified outcomes; the UI separately records human reviews. Configuration/service failures and readiness probes do not count.

Use `uv run kat status` for actual local progress. `doctor` distinguishes configuration from execution; `doctor --live` tests catalog access and Hermes importability. Explicit `doctor --live --inference` exercises the configured adapters after organizer request schemas are known. No published performance/quality result is implied by installing this repository.

## Current limits and deliverables

The [setup guide](docs/setup.md) now records actual shared Parse 3.5/Wikipedia URLs, exact model IDs and the starter's custom Docker recipe serving both retrieval models. A fresh installation needs a Nebius GPU deployment and its own Token Factory key. The team workspace has passed live checks for the required services; [saved execution receipts](evidence/live-services/all-services-live.json) and [GPU outputs](evidence/live-services/retrieval-gpu-smoke.json) document what ran. Supplied URLs alone are not live inference proof. Human review is necessary for OCR, semantic support and historical interpretation. The [Wikipedia notes](docs/wikipedia.md) explain the shared service and optional fallback.

`kat batch --stage compare` retains failures. `kat review` records human judgments. `kat archive` builds the static scan/region/LaTeX archive. `kat export` packages generated site artifacts, observed checklist status and selected reproducibility evidence, excluding keys and bulk corpus files. Export does not establish that 100 comparisons, compilations or 3+3 valid cases are complete.

The new brief's **3-minute video** supersedes provisional earlier durations. Show successful and failed cases. The GitHub repository must contain the solution, static website, compiled LaTeX, analysis and 3+3 case documentation. The three-minute video must be recorded and submitted separately. Source attribution and licenses must accompany retained excerpts and generated comparisons.

## Try the saved archive

The saved selection contains 100 scans. Parse 3.5 completed 99 outputs: 92 contain readable text and seven contain layout/picture regions only. Geometry plate row 1261 repeats figure labels and ends at its token limit; two bounded crop trials did not rescue it. Its failed attempt stays visible. The static snapshot includes all original scans and compiled LaTeX for the 99 completed outputs, including clearly labeled layout-only documents. Generated comparisons, original/revision links and visible quote-check failures accompany the processed pages. Ten real Hermes diagnostic runs and their limitations are recorded in the [casebook](docs/actual-cases.md). These are targeted examples, not a representative accuracy benchmark.

```sh
python3 -m http.server 8131 --directory site
```

Open [localhost:8131](http://127.0.0.1:8131). For the live local interface use `uv run kat serve`, then select row 57 to inspect its source regions. See [testing instructions](docs/testing.md).
