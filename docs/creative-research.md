# Creative layer after the required baseline

Research date: 18 October 2026. Primary-source research plus inspection of actual local scans and live Parse artifacts. This document proposes work; it does not report an implemented creative extension or a measured quality improvement. Only this Markdown file was changed for this research task.

## Recommendation: Challenge this conclusion

**Build one bounded Hermes extension: a user can challenge a comparison claim, make the agent inspect the original source region and its modern counterpart, and receive a defended, qualified, revised or unresolved conclusion.** Preserve the original answer and every source version. The same interaction can become a small Discovery Lab evidence game; it does not need a new timeline, a general physics simulator, fine-tuning or elaborate image generation.

The concrete problem is visible in our own current data. The Parse output for CHOCOLATE row 57 says a small quantity of **alcohol** was added; the inspected original scan says **olive-oil**. ELECTRICITY row 1776 says a chain lay in an **influential** metal dish in the parsed text; the scan reads **insulated**. Those are potentially consequential transcription errors. Quoting the parsed text accurately would not establish that the quotation matches the historical page. A live model run completed successfully as infrastructure can still produce an extraction failure.

This is more concrete than another generic report, and more achievable in two hours than claiming arbitrary historical text can be turned into scientific experiments. The technical contribution is a working, inspectable source-to-conclusion audit and revision workflow—not invention of OCR correction, fact checking or interactive education.

## The exact rubric changes the priority

The organizer's 13-page brief, locally extracted at [`research/organizer-brief-2026-10-18/participant-brief.txt`](../../research/organizer-brief-2026-10-18/participant-brief.txt), supersedes older descriptions: Parse **3.5**, the shared Wikipedia API, a static site with compiled LaTeX documents, and a **three-minute challenge video**. Its public [starter](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge) describes the unfinished stages the team must implement.

The brief awards 20 points for completion; 20 for creativity (10 originality, 10 value); 15 for Parse integration/fidelity/structure; 15 for embedding/reranking; 10 for a working useful Hermes extension; and 20 for Super VL integration, comparison, grounding and failure handling. These are separate checks, not guaranteed additive points for a feature. A missing mandatory component receives zero on its corresponding checks.

Therefore, the creative feature should improve an already required activity: exploring historical-modern differences while identifying errors and unsupported conclusions. A useful custom audit tool fits that brief more directly than an unrelated sponsor showcase. The [starter's Hermes guide](https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge/blob/main/docs/hermes.md) and the [pinned real Hermes tool registry](https://github.com/NousResearch/hermes-agent/blob/354ad3d48786f2978c49be88f28c13d78fa0b6e0/tools/registry.py) are primary implementation references. The current team bridge deliberately exposes only three tools, so an extension must actually add its schema, dispatch, parent callback and trace; a UI button alone is not a Hermes extension.

## Direction 1: Challenge this conclusion — recommended two-hour scope

### Before and after

**Before:** A fluent comparison cites a source ID. The user must independently notice whether its underlying OCR, article match or interpretation is wrong.

**After:** The user selects a suspect claim and challenges it: “Is this really an observation?”, “Did the scan say that?”, or “Does the modern passage discuss the same thing?” The agent traces the claim back to the actual page region and matched Wikipedia passage. It identifies the kind of dispute, proposes a supported response, and shows what changed while retaining uncertainty.

### Ninety-second judge interaction

1. **0–15 seconds:** Open the actual CHOCOLATE page, its live parsed regions and the actual modern match from the shared snapshot. Start from a real recorded comparison or question, not a fabricated flawed answer.
2. **15–35 seconds:** Let the judge click a suspicious phrase or choose a supplied challenge. The Hermes tool opens the original crop, parsed text, source IDs and modern supporting passage. The alcohol/olive-oil discrepancy is a strong prepared fixture, clearly identified as one observed Parse failure.
3. **35–55 seconds:** Super VL proposes a visual reading and marks whether the issue is extraction, matching, interpretation or insufficient evidence. A human-reviewed correction can be accepted into a separate revision; the original parse remains immutable. If the image is unclear, unresolved is the correct outcome.
4. **55–75 seconds:** Re-run only the affected page's comparison/question using the explicitly revised evidence, with embedding/reranking used where the text changes the match. Show the before/after, changed supporting source IDs and unchanged claims. Do not imply every OCR edit must change the conclusion.
5. **75–90 seconds:** A second example from CLOUD asks whether the historical author actually treated electrical cloud formation as proven. Show its stated uncertainty. Export the real failure/revision trace for model creators, including a case where the audit could not resolve the problem.

The prepared fixture demonstrates a real observed error. The judge's follow-up and tool selection should be live. If only a lookup deck is implemented, call it a reviewed educational exhibit rather than autonomous diagnosis.

### Small implementable tool contract

An `audit_comparison_claim` tool takes an existing run/page ID, claim or source ID, and a challenge category. It resolves only selected manifest pages and registered sources. It returns the actual scan region, original parsed reading, exact modern passage, a proposed reading/interpretation, explicit uncertainty, and permitted next actions. Restrict image access to that selected source; it is not a general filesystem or URL-reading tool.

Use required Super VL for visual inspection and reasoning. Keep Parse 3.5's raw output and boxes. Any alternative reading receives a new source/revision ID; a human-confirmed correction must be visibly distinguished from a model proposal. The old source remains available to the old run. The first version needs one audit tool and a small revision record, not a global truth graph or unrestricted self-repair agent.

Do not introduce a second OCR engine as the source of truth. A crop from a 600px original contains no newly recovered detail; enlargement may aid viewing/model focus but cannot restore information that was never captured. A box syntactically inside the page does not prove it encloses the intended text.

### Prior art and the defensible delta

- [RARR, ACL 2023](https://aclanthology.org/2023.acl-long.910/) already researches attribution and revises unsupported generated text. Our claim cannot be “the first agent that checks and revises its answers.”
- [Multimodal LLMs for OCR, OCR Post-Correction, and NER in Historical Documents](https://arxiv.org/abs/2504.00414) already studies visual correction on historical scans. Its results on German city directories do not establish accuracy on our Britannica pages.
- [Correctness is not Faithfulness in RAG Attributions](https://arxiv.org/abs/2412.18004) distinguishes a citation supporting a statement from genuine model reliance on that citation. We therefore retain run evidence and do not present literal quote checks as a trust certificate.
- [HistoricRAG, EDBT 2026](https://www.openproceedings.org/2026/conf/edbt/paper-321.pdf) already provides historical QA with original scans, timeline and map exploration. Merely showing a scan beside an answer is established.

The proposed contribution is the **working cross-era challenge workflow**, tied to this mandatory multimodal pipeline, with specific real errors, limited revisions and measured benefit. Originality under the rubric means a distinct executed team contribution beyond the starter; it does not require pretending these research categories are new.

### Ablation and honest failure cases

Select 20 actual regions from the completed 100-page base before measuring: include visually confirmed semantic transcription errors and readable controls, with the strata and selection bias disclosed. Two team members independently transcribe the short relevant spans and label disagreements; resolve only what the original supports.

First measure the audit tool: validated semantic errors found, false alarms on clean spans, abstentions on unclear scans, and character error rate on the reviewed short spans. Report counts and denominators. Then run 6–10 matched questions with the original evidence and with the audited/reviewed revision, using the same model, prompts and bounded call budget. Count unsupported historical claims, correct uncertainty preservation and whether both historical and modern evidence support the final comparison. This is an exploratory paired diagnostic; a small hand-selected set does not establish general accuracy.

An end-to-end improvement with a human correction demonstrates the assisted workflow, not autonomous correction quality. Separate the model's proposed-reading accuracy from the human-reviewed result. Keep a false audit alarm and an unresolved image as visible failures if they occur. Never deliberately inject an OCR error and present it as a naturally observed model failure.

## Direction 2: Evidence Surgery / Discovery Lab

**Before:** The user reads “old source says X, modern source says Y.” **After:** The user reveals or withdraws evidence and sees which parts of the comparison remain warranted. This makes historical knowledge change inspectable rather than merely narrated.

ELECTRICITY row 1776 reports the qualitative chain/electrometer observation; CHOCOLATE row 57 separates observation from conjecture; CLOUD row 59 explicitly discusses missing demonstration. These are eligible inspected historical pages. Exact modern counterparts and their specific explanatory content must come from the actual completed matching run; a plausible live Wikipedia title is not validation of the frozen comparison.

The bounded extension is a new Hermes tool that lists admissible evidence and its source/claim role for the selected investigation. A source exclusion must apply consistently to search, read and cached comparison tools, and remove derived answers that reveal the same information. Start a fresh agent session. If another passage still supplies the answer, removing one citation should not force abstention. Do not confuse “not in this admitted bundle” with historically false, unknown to humanity or erased from pretraining.

**Ninety-second moment:** Let a visitor predict the chain indicator direction; reveal the exact recorded passage; compare a checked modern explanation; withdraw the modern explanation and ask which historical observations remain supported. The diagram illustrates recorded observations, not a physics simulator or arbitrary quantitative predictions.

**Technical edge:** Evidence permissions, explicit claim roles, fresh-session replay and supported/unsupported answer updates. **Metric:** On 12 reviewed questions, compare normal answers, relevant-support removal and irrelevant-support removal. Record unsupported retained claims and unnecessary abstentions, with human review. Equivalent plain prompting is the baseline; access filtering must demonstrably add value.

**Prior art:** [Minimal Evidence Group Identification](https://aclanthology.org/2025.trustnlp-main.8/) and [User-Centric Evidence Ranking](https://aclanthology.org/2026.eacl-long.340/) already address sufficient/complementary evidence; [ExAnte](https://aclanthology.org/2026.eacl-long.72/) tests temporal leakage. [Context-faithful Prompting](https://arxiv.org/abs/2303.11315) already targets conflict between supplied context and model knowledge. [KnowledgeTrail](https://arxiv.org/html/2510.12113v2) already has timelines, generated illustrations and linked exploration. The specific scoped interaction and measured execution must carry the contribution.

**Why second:** It is compelling, but rigorous evidence removal touches every tool/context path and can exceed two hours. A visual “hide card” that leaves the evidence inside a cached comparison is only a UI trick. Ship it only when those access boundaries are real.

## Direction 3: Local challenger and failure capsules

**Before:** Three failures are anecdotes in the final README. **After:** A local assistant proposes precise challenges to actual answers, and human-confirmed failures export the question, sources, parse, retrieval/rerank results, model configuration and tool events needed for replay.

A useful small-model role is spotting lost qualifiers or suggesting questions grounded in supplied parsed text, such as “Why did you say proven when the author says conjectures?” It is not authorized to certify the original image or historical truth. The required main Super VL/Hermes workflow remains unchanged.

There is an official [NVIDIA Nemotron 3 Nano 4B GGUF model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF): it is a Q4_K_M compressed text model and documents llama.cpp deployment. **Text-only matters:** this model cannot independently read the scan; it can challenge provided text and propose questions. The existence of a local checkpoint does not prove our hardware's speed, quality or working runtime. No local deployment or latency measurement was performed in this research task. Do not run the enormous advertised maximum context for a small audit job.

**Ninety-second moment:** Main agent answers; local challenger proposes a source-linked objection; the audience tests it; the system defends or revises the answer; a human accepts/rejects the failure label. Export the actual replay capsule. Demonstrate model/device labels and one actual local request if claiming local AI. Cached suggestions need to be labeled cached.

**Metric:** Challenge 20 real answers with a fixed main-model call budget. Count verified failures found, false alarms, reviewer minutes and added model calls; compare random or manually written follow-ups at the same budget where possible. A local model must earn its latency or call savings with actual measurements. Do not label its unreviewed accusations as failure discovery.

**Why third:** Fits the model creators' interest in useful failures, but local deployment and another model can consume the whole window. Exporting replayable cases is already useful without autonomous red teaming. Use this after the audit interaction works, not as the reason to delay the mandatory base.

## Partner choices

Required Nemotron components and Hermes already provide the core. Add partners only when they perform an actual user-visible or reproducibility task:

- **BFL:** one reviewed conceptual apparatus illustration for an evidence game, with labels and factual states rendered in code. Generated visuals are not observations or accurate reconstructions. Existing Rumford art is not a verified eligible dataset example.
- **Hugging Face:** publish selected-page provenance and genuine replayable cases, subject to source licenses; include failed and unresolved examples.
- **Toloka:** human evaluation only if actual same-day annotation access/turnaround exists. Do not relabel team reviews as external expert validation.
- **Tavily:** optional original-experiment corroboration in a clearly separated extra-source layer. It must not silently replace the required shared Wikipedia corpus.
- **Devin:** parallel implementation/testing is a useful development process; it is not a runtime feature of the historical comparison agent.

## Two-hour delivery cut

This estimate is a proposed scope for strong engineers above an already working base, not a measured implementation duration.

1. **First 25 minutes:** choose one real source/claim failure and one clean control; review the original crop and exact modern passage. If there is no actual supported historical-modern pair, continue the base instead.
2. **Next 40 minutes:** add the restricted Hermes audit callback/schema and an immutable proposal/review record; retain every original artifact. Audit only one selected region per call.
3. **Next 30 minutes:** expose one “Challenge this conclusion” interaction and a compact before/after with citations and explicit proposed/reviewed/unknown states.
4. **Final 25 minutes:** replay the fixture and clean control, measure a small matched diagnostic, record a real failure, and capture the three-minute video around the complete required pipeline.

Stop before adding a new timeline framework, arbitrary experiment generation, image fine-tuning, exhaustive claim dependency graphs, automated historical truth scoring or unmeasured local cost claims. The strongest stage sentence is concrete: **“A perfect citation can still quote a bad transcription. Here is the original scan, the mistake, and exactly how our agent revises the comparison.”**
