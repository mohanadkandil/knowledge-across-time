# Knowledge Across Time: agent handoff

Updated 18 October 2026, 15:50 Europe/Berlin. Hackathon submission deadline: 18:30 today.

## Start here

The working baseline is built. The user is choosing a creative scientific domain and currently considering **light**. Their latest request was to create this handoff, not to implement the light concept. Continue from that decision point; verify suitable historical evidence before presenting a domain as ready or building its showcase.

Repository: `https://github.com/mohanadkandil/knowledge-across-time`.
Local workspace: `/Users/mohannedkandilicloud.com/Desktop/hacks/knowledge-across-time`.

1. Read this file and inspect `git status` before editing; other agents may share the workspace.
2. For project history, retrieve GBrain context for entity `project-knowledge-across-time`. Saved facts have timestamps; newer facts supersede older progress descriptions. Keep credentials out of memory.
3. Verify service readiness with the commands below. Preserve the current GPU VM, index, selected sample and recorded agent runs.
4. If continuing creative work, resolve the historical-source question under “Light investigation” first. A passing mention of optics does not establish enough material for a scientific comparison.

## What the user wants

- Win the NVIDIA knowledge-comparison track and compete in the grand final. Best use of Nemotron is also a goal; the listing says “NVIDIA DGX Card.” The user calls it a DGX Spark, but that exact hardware prize has not been confirmed.
- Finish the required baseline before creative extras. Demonstrate real execution, including three useful cases and three genuine failures.
- An immediately understandable, surprising domain; generic comparison chat and a pretty timeline alone are insufficient.
- A proposed product flow: start from a current Wikipedia article, add our URL prefix, and explore historical counterparts, dated changes and cited evidence. **The prefix flow and creative timeline are not implemented.**
- A reusable comparison experience plus a polished showcase topic. A hand-built scientific illustration must not be described as a universal automatically generated simulation.
- Practical, candid recommendations. The user has rejected overly complicated electricity explanations and weak “technology progressed” stories. Avoid repeatedly declaring a different idea the strongest without new evidence.
- Plain commit messages. The user requested the humanizer skill and no AI boilerplate in messages. Existing commit timestamps are genuine and have not been changed.

## Mentor feedback: direct evidence

The user supplied a transcript of a conversation with the NVIDIA mentor:

- The mentor praised another team's comparison of historical and modern medicine.
- He advised choosing a scientific topic and showing changes in understanding; geology and biology were examples.
- He explicitly liked the user's draggable timeline proposal. This is positive feedback, not a prediction of winning.
- Failure cases can be Super making unsupported claims about the supplied sources, inventing details or accepting a wrong topic match. Independent source inspection by Codex was acceptable in the mentor's example.
- Appropriate uncertainty or a service outage is not, by itself, a hallucination case.

## Light investigation: current creative lead, not yet selected

Proposed audience hook: **“Can adding more light create darkness?”**

An illustrative single/double-opening experiment reveals bright and dark interference bands. The historical/modern comparison then explores how explanations of light developed. Visitors inspect the actual source passages and challenge the agent's account.

Important scientific and evidence boundaries:

- Classical wave theory explains interference. A two-slit animation alone does not establish quantum behaviour.
- Historical editions may already explain waves. Read the actual edition rather than assuming all historical accounts are corpuscular or incorrect.
- Quantum developments and the photoelectric effect can be modern context only when supported by retrieved evidence. Our historical collection predates those developments.
- An illustration is a teaching aid, not a historical image or a validated numerical simulation.
- Timeline dates must come from publication metadata or explicitly cited events. **Dataset row 1776 is not the year 1776.**

Research leads already found:

- [OpenStax: Young's double-slit experiment](https://openstax.org/books/college-physics-ap-courses/pages/27-3-youngs-double-slit-experiment).
- [AIP: Einstein and the photoelectric effect](https://history.aip.org/exhibits/einstein/essay-photoelectric.htm).
- [NLS Britannica collection](https://data.nls.uk/data/digitised-collections/encyclopaedia-britannica/), covering the first eight editions, 1768–1860.
- Search found an [NLS historical optics PDF](https://deriv.nls.uk/dcn23/1139/1107/113911070.23.pdf); the web reader failed because it is about 19 MB. Its exact inclusion in the required Hugging Face sample has not been established.
- A third-party transcription site has eighth-edition LIGHT and OPTICS entries, but these are discovery leads, not a replacement for the required dataset or original scan verification.

What is actually in our current 100-page sample: a brief VISION/optics definition on row 781 and a MICROSCOPE plate on row 2078. **No substantial light-theory passage is confirmed yet.** Find suitable pages within the full required dataset before promising this direction. Keep any additional exploratory pages separate from the fixed evaluation sample unless the selection method and all affected deliverables are deliberately updated.

## Other domain leads already inspected

These are machine-text leads; verify the scans before using exact wording:

| Dataset row | Material | Status |
| --- | --- | --- |
| 1776 | Electricity, electric-fluid distribution, conductor/chain/electrometer experiment | Existing useful comparisons and genuine grounding failures; user found the proposed explanation difficult |
| 795 | Electrical experiments involving plants | Existing human-electrotherapy matches do not establish an appropriate botanical counterpart |
| 59 | Clouds; unresolved relationship between electricity and condensation | Existing source-supported uncertainty case |
| 2376 | Basalt; competing fire/water origin explanations; Giant's Causeway and Staffa | Promising geology lead; scan and modern match still need review |
| 2545 | Furnace, air pumps and pressure gauge helping assess actual performance | Technology lead; no creative exhibit implemented |
| 995 | Gas lighting, equipment and operating costs | User felt city-lighting history was weaker than a scientific change of understanding |

Full required HF dataset is cached at `../research/dataset-fit-2026-10-18/britannica/train.parquet` (relative to repo): 2,573 scans; columns `image`, `label`, `id`, `meta`. The current file has no OCR column. It is not a full encyclopedia text index. Volume ranges in metadata are not proof of a particular article on a scan.

## Working baseline and its limits

Most recently recorded results, not a claim of a fresh full rerun:

- Fixed 100 selected scans, with documented selection and hashes.
- 99 parser outputs: 92 readable, seven layout/picture-only. Row 1261 remains a failed geometry-plate parse with repeated labels; two crop trials did not rescue it.
- 91 candidate-matched structured comparisons, seven abstentions, two retained errors. Row 1245 has no supported plate query.
- 99 compiled PDFs; 101 static HTML pages; 2,059 relative links checked.
- Only **26/91** structured comparisons passed all literal-quote checks. Literal presence still does not prove semantic support or OCR fidelity.
- Ten completed real Hermes diagnostic runs, with three useful comparisons and three qualified failure modes. Zero human review records at the last audit. Read [the actual casebook](docs/actual-cases.md), which carefully distinguishes partial successes and failures.
- Most recent software suite: 67 passed. No full suite was rerun for the latest documentation-only change.
- Static archive is tracked in `site/`; runtime data is under ignored `data/`.
- `dist/base-review-20261018.zip` predates the native interactive Hermes integration. Regenerate and inspect the final export before submission.
- Three-minute submission video and creative extension remain outstanding.

Concrete real failures: row 57's original “olive-oil” becomes OCR “alcohol”; row 1776's original “insulated” dish becomes an unsupported “electrified” reconstruction called verified; row 59's Beccaria becomes an invented Becquerel attribution. Preserve original runs and qualify outcomes as the casebook does.

## Required architecture and running it

Read [architecture](docs/architecture.md), [setup](docs/setup.md), [Hermes](docs/hermes.md) and [testing](docs/testing.md) for exact contracts and pins.

- CPU workspace: ingestion, matching logic, local LanceDB, tool execution, real Hermes orchestration, static archive/LaTeX generation.
- Organizer services: shared Nemotron Parse **3.5** and indexed Wikipedia lexical search/full-article API.
- Team GPU: exact pinned Nemotron Embed VL and Rerank VL models, deployed together using the organizer's custom container recipe.
- Token Factory: `nvidia/Nemotron-3.5-Super-VL` for agent reasoning. Credentials are already in ignored local `.env`; read them through settings, never print or copy them into this file, commits, memory or logs.
- Wikipedia is the sanctioned shared `wikimedia/structured-wikipedia` snapshot, not byte-identical to the earlier Kaggle option. Details: [Wikipedia notes](docs/wikipedia.md).

```sh
cd /Users/mohannedkandilicloud.com/Desktop/hacks/knowledge-across-time
curl --fail http://127.0.0.1:8001/ready
uv run kat status
uv run kat hermes
# Resume a previous native conversation:
uv run kat hermes --resume latest
# Separate one-question evaluation entry point:
uv run kat ask "Compare the historical CLOUD definition with the available modern evidence." --page 59
```

Native Hermes uses an isolated ignored profile `data/hermes-cli/` and four tools: `search_sources`, `read_source`, `compare_page`, `browse_corpus`. The Python 3.12 application executes tools; the pinned Hermes runtime uses Python 3.14. Existing paths are configured in `.env`; do not reinstall from scratch without checking them.

`search_sources` embeds a query, searches **our saved LanceDB corpus**, and reranks hits. It does **not** search all Wikipedia or call the shared Wikipedia API directly. Initial page matching uses the shared Wikipedia API to obtain candidates and article text. `browse_corpus` filters the saved 100 historical pages and their OCR; it is not BERTopic clustering. `read_source` returns text; an `:image` source ID does not mean Hermes received pixels.

At 15:50 Berlin, both `http://127.0.0.1:8001/ready` and `http://127.0.0.1:8130/health` returned HTTP 200. Local app: port 8130. Static archive can be served independently with `python3 -m http.server 8131 --directory site`.

### Recent search outage and recovery

The user encountered `service connection failed` from native `search_sources`. Reproduced exact symptom. Cause: the local SSH tunnel had stopped; shared Wikipedia and remote GPU services were healthy. Restored a background SSH forward with keepalives. The exact Homer tool request then returned three embedded/reranked results. Those results are incidental references, not proof of a dedicated Homer entry.

Recovery command template and explanation are in [docs/hermes.md](docs/hermes.md). The forward maps **localhost 8001 to VM loopback 8000**. Local port 8000 belongs to another service; preserve it. Background SSH still depends on network connectivity and laptop wakefulness. Existing Hermes conversations can retry without restarting.

One reserved GPU VM already exists: `kat-retrieval`, assigned `group40-project`, project ID `project-e05xn07dln00ye1fxm3s1m`. It uses one RTX PRO 6000 Blackwell 96 GB GPU. Connection/deployment details are under ignored `data/deployment/`; reuse them. Keep the API on VM loopback. Direct project access works even though tenant project listing was denied.

## Rubric and submission

[docs/rubric.md](docs/rubric.md) is the concise checklist. The 18 October participant PDF supersedes the earlier listing: Parse 3.5 and a **three-minute** submission video are current requirements.

Required: 100-page documented selection/matching coverage, static website and compiled LaTeX, evidence-supported comparisons, real Hermes, all required models, three successful and three clear failed own agent cases, public repository and video. Perfect matching accuracy is not required; failures remain visible.

Weights: completion 20, creativity 20 (originality 10/value 10), Parse 15, Embed/Rerank 15, Hermes extension 10, Super 20. Read the detailed rubric before optimizing a side feature. The final-stage presentation is five minutes; team rule is 2–4 people. Actual team composition is not verified here.

Original participant PDF is attached in the conversation and locally at:
`/Users/mohannedkandilicloud.com/.t3/userdata/attachments/8defadbd-934f-495e-9c08-9667d79e1a32-51539cc0-8d91-4cfc-acfa-8d26d0285e2d-pdf.pdf`.

## Proposed challenger and partners

[docs/creative-research.md](docs/creative-research.md) describes an unbuilt local challenger: a small local Nemotron proposes challenges to the main agent's answers; source inspection verifies failures. Inspiration: [Perez et al., Red Teaming Language Models with Language Models](https://arxiv.org/abs/2202.03286). The paper's original task differs; our grounding adaptation has no demonstrated result yet. No local challenger has been deployed.

The user has BFL credits; generated illustrations are optional and must be labeled. No BFL use is needed for the baseline. The user previously referenced `https://arxiv.org/pdf/2510.12113`; inspect it before claiming our proposal implements that paper. No claim about its contents is established here.

## Git state and handoff boundary

Existing commits:

- `9c66d47` Set up Britannica comparison baseline.
- `89ab5bc` Add live comparisons and evaluation evidence.
- `3b24d0c` Connect corpus tools to interactive Hermes.
- `36237f6` Document how to restore the retrieval tunnel.

Before creating this file, the working tree was clean and local main was three commits ahead of its configured upstream. No push was performed in this session; verify remote state before making claims. This handoff is a new local file. A GitHub star was requested earlier but its completion is not verified here.

Next useful result: identify a readable historical light passage in the required dataset, verify its actual claim against the scan, retrieve its modern counterpart, and present one short source-supported before/after story to the user. If that evidence cannot be found promptly, explain the limitation and use an already verified domain rather than inventing a history.
