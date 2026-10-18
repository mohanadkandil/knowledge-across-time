# Evaluation protocol and six proposed agent cases

**These are preregistered question proposals, not recorded model outcomes.** No successful or failed live Nemotron/Hermes answer is claimed here. Offline fixtures live only inside pytest temporary directories; they are not submission cases.

A run counts toward the required three successes and three failures only after a real, completed Hermes **question** run using the configured required model, followed by a named human review. Comparison artifacts, missing credentials, unavailable endpoints, timeouts, unfinished answers and framework setup errors do not count. A completed answer can still be an authentic behavior failure when, for example, the agent retrieves a wrong source or mishandles a source; a recoverable tool error does not automatically disqualify that run.

## Source evidence already inspected

The three historical scans are exact rows in `NationalLibraryOfScotland/encyclopaedia_britannica_illustrated` at revision `309f765b1ecc83e0a7f7762e44b4a927a7555443`. Their scan identities are part of the deterministic 100-page selection; printed page numbers below were visually checked, not inferred from row indices.

| Historical row | Visible entry / printed page | Image SHA256 |
| --- | --- | --- |
| 57 | CHOCOLATE / 54; sixth edition, volume6 | `7d7650d5d60fdd55869e4c6800874479b67eaa2ecc4463f6a9549cfaf80c35d2` |
| 59 | CLOUD / 211; sixth edition, volume6 | `891965a7ca3ee9db3ed38ed2a5aede648b7d405b2793f3bae3d62ddacbc13a85` |
| 1776 | ELECTRICITY / 584; third-edition supplement, volume1 | `5ed864a29d363db6a7c9380249079c9c50b16b15bedde2855c6814920bf98399` |

The following modern articles were actually retrieved through the **organizer-provided shared API**, paginated to completion and verified against the server's full UTF-8 text SHA256. This is the sanctioned canonical `wikimedia/structured-wikipedia` snapshot at revision `417c267bb457fa645c22eb3b5c77764963194c70`, not a claim of byte identity with the Kaggle archive.

| Article | Page ID | Revision | Verified text SHA256 |
| --- | --- | --- | --- |
| [Capacitance](https://en.wikipedia.org/w/index.php?oldid=1352525037) | 140711 | 1352525037 | `701d5cf51c8c7aaeeac0d0e656731c12694f61155fe561bf1d6070eb8b613b37` |
| [Static electricity](https://en.wikipedia.org/w/index.php?oldid=1348121664) | 200136 | 1348121664 | `9475fe3251026d533d6bcca9ff7b8957d0f42bed519ee5d9d689c751f04c2cc5` |
| [Carbonic acid](https://en.wikipedia.org/w/index.php?oldid=1351882362) | 51420 | 1351882362 | `495cea063f20d53ae6e3c112a6533568d528607ad096afb2e46a16fe96c5a86c` |
| [Condensation](https://en.wikipedia.org/w/index.php?oldid=1344726255) | 47521 | 1344726255 | `5e6b4f99a714265207d72caa094c6acd61c055a3b51af010421cf67742b49a33` |
| [Cloud physics](https://en.wikipedia.org/w/index.php?oldid=1353591386) | 731795 | 1353591386 | `98f1e41d835ec89b7e7eb135acbe0f599396d6c8b1277a1a91e0802ed58e97a0` |

Cached exact texts and pagination provenance are in `data/wiki-remote/articles/`. The shared API supplies flattened text. Original structured reference objects and exact original section boundaries are unavailable through this access path; the adapter marks that limitation and does not fabricate them.

## Three candidate success questions

**S1 — Reported chocolate experiment versus its explanation.** Ask: “In row57, which statements report an intervention or observation, and which statement is Henly's conjecture? Compare the explanation with the retrieved Static electricity and Carbonic acid passages. What remains unverified?”

Expected behavior: identify cooling in tin pans, handling, remelting, dried/powdered material and added olive oil as parts of the historical report. Identify the proposed affinity/identity between carbonic acid and electric fluid as a conjecture. The modern articles describe charge imbalance and a chemical compound; they do not independently reproduce Henly's chocolate result. A successful answer cites both collections, preserves that uncertainty and avoids confidently naming a chocolate-specific charging mechanism from general static-electricity descriptions. The historical meaning of “carbonic acid” also needs caution; a title match alone does not resolve its exact referent.

**S2 — A changing electrometer reading.** Ask: “What happens when the chain in row1776 is raised and lowered? How could the modern Capacitance article help interpret this, and which assumptions would you need?”

Expected behavior: report the historical direction of the electrometer's change, then distinguish that literal observation from a proposed modern account involving charge, potential and geometry. The fetched Capacitance text defines the relevant ratio and says geometry/dielectric properties affect capacitance. It does not provide this historical apparatus's dimensions, complete boundary conditions or calibration. Any fixed-charge argument must be explicitly conditional. Do not call a qualitative explanatory sketch a new measured result, and do not apply a parallel-plate formula to the chain without justification.

**S3 — Historical uncertainty about cloud formation.** Ask: “Does row59 establish that electricity is necessary for condensation? Compare its stated uncertainty with the modern Condensation and Cloud physics articles.”

Expected behavior: preserve the old author's explicit statement that the needed experiment has not been supplied. Contrast the modern phase-change and cloud-microphysics accounts using source passages, while avoiding the stronger unsupported statement that electricity can never matter in clouds. This tests whether the agent can recognize continuity and historical caution rather than forcing a confident ‘old wrong / modern right’ narrative.

## Three possible authentic failure probes

These are **failure hypotheses**. If the agent handles a probe correctly, record it as such; do not relabel it a failure to fill a quota. Retain failed and successful attempts, prompts, candidate pools and the actual final answer.

**F1 — Ambiguous modern counterpart and interpretation.** Ask: “Does the modern Carbonic acid article verify the identity of the material named in Henly's electrical-fluid conjecture, or is this only a partial match?” Historical source: row57. Modern sources: Carbonic acid and Static electricity.

Potential failure: treating the identical phrase as proof of an unchanged historical chemical referent, or treating a modern chemical definition as an independent confirmation/refutation of every detail of the chocolate observation. Expected behavior is to separate lexical correspondence, modern definition and the unresolved historical referent. Score a failure only if the completed answer actually makes the unsupported identification. Retrieval is also a real risk: in a live API probe, simple “Chocolate” and “Cloud” queries did not include the main articles in the top10, whereas more specific physical terms produced relevant candidates. Search traces are evidence of that recall issue, not a recorded agent failure.

**F2 — OCR negation or column mixing.** Ask: “Which experiment concerning electrified air and its moisture does the CLOUD entry say has not yet been demonstrated?” Historical source: row59; modern sources: Condensation and Cloud physics for comparison.

Potential failure: Parse misses the negation, interleaves the adjacent CLOTH column, or the agent reports an established electrical-condensation experiment when the scan says evidence is lacking. Judge against the actual image and right-column passage. A quote that is literal in erroneous OCR can still be wrong against the source image. A parser/server outage with no completed question answer is an infrastructure failure and cannot fill this case slot.

**F3 — Unsupported quantitative reasoning.** Ask: “Using the chain experiment in row1776 and the supplied Capacitance article, predict a numerical change in the electrometer reading when the chain is raised by a further10cm.”

Potential failure: inventing a numerical reading, charge, capacitance or instrument calibration. The inspected historical page and modern article do not supply enough apparatus-specific data. Expected behavior is to state what additional geometry, charge/boundary conditions and measurement calibration would be required, and to label any illustrative model assumptions. A correct refusal is a successful answer, not a failure.

An additional source-quality risk was observed in the *retrieved* Carbonic acid text: chemical subscripts are lost in some formulas (the introductory formula is rendered as spaced letters). Preserve the exact service text and flag missing notation; do not claim a normalized formula is a literal quote from that extraction. This is a candidate follow-up probe, not a seventh recorded outcome.

## Review procedure

For every question, save the exact prompt, model/service identities, Hermes framework identity, candidate queries and retrieved pool, chosen source IDs, final answer and tool trace. A reviewer checks all material claims against both the parse and the source image, as well as the pinned modern text. Literal quote matching establishes string presence only; it does not establish interpretation, accurate OCR or entailment.

Use `Store.review` only after that review. Enter expected behavior, actual observed error or success, category and reviewer. `Store.cases()` revalidates eligibility and the reviewed run SHA256, so old review files cannot turn a comparison, subsequently failed run, or changed answer into a counted question case. No case outcome should be assigned by reading these proposed expectations alone.

## What offline tests establish

`tests/test_baseline.py` uses fake HTTP responses and temporary fixtures. It checks actual local LanceDB upsert/search and model/dimension guards; deterministic exact100 selection against an already-downloaded pinned corpus; citation presence checks without semantic claims; completed-question review eligibility; malformed embedding/reranking responses; parse fallback honesty; and credential redaction. `tests/test_wiki_remote.py` checks Unicode pagination, full-text checksums, snapshot/coverage identity, rejected inconsistent responses, cache reuse and bounded busy-service retries. Passing these tests does not establish that a live Nemotron endpoint or Hermes answer works.

## Actual shared-Wikipedia smoke observations

These are **live retrieval checks**, not live LLM/Hermes evaluations. `GET /ready`, `GET /v1/corpus`, `POST /v1/search` and full paginated `GET /v1/articles/{id}` requests succeeded through the organizer endpoint using Python3.12/httpx. Five complete article texts passed their advertised SHA256 checks; their IDs/revisions/checksums appear in the source table above. Capacitance and Cloud physics required two pages, so continuation and concatenation were exercised against the real service.

The unexpanded `Chocolate`, `Cloud`, `Carbon dioxide` and `Condensation` queries did not include their corresponding main articles in the top10 returned candidates. This is observed lexical recall behavior, not proof those articles are absent. The expanded query `condensation water vapor gas liquid phase` returned Condensation at rank3; `static electricity charge surface imbalance` returned Static electricity at rank1. `cloud atmospheric condensed water droplets` surfaced Cloud physics, and `carbon dioxide CO2 chemical compound` surfaced Carbonic acid; those relevant candidates were fetched, not automatically declared the best historical matches.

No HTTP API failure occurred in the successful Python3.12 retrieval smoke. An earlier probe using the system Python3.9/LibreSSL failed its TLS negotiation against the same endpoint; switching to the project's Python3.12 runtime resolved that client-runtime incompatibility. This is excluded from agent case counts. Search responses and provenance manifests are retained under `data/wiki-remote/searches/`, `verified-targets.json`, `expanded-verified-targets.json` and `relevant-verified-targets.json`. Their cache directory is a retrieval-smoke artifact; the application's configured corpus directory may be `wiki-shared`.
