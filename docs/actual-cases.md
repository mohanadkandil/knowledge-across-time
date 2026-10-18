# Actual agent cases: useful comparisons and observed failure modes

Reviewed 18 October 2026 through **automated source inspection**, not external or human evaluation. The reviewer read real Hermes run JSON, source-tool results, the source registry, and the original scan images for rows 57, 59 and 1776. No model calls were made for this review, no answer was edited, and no `Store.review` records were created. At inspection time there were **zero human-reviewed cases** in the store.

This casebook presents **three useful comparison examples and three observed failure modes**, rather than claiming exactly three flawless answers and three wholly failed answers. Some answers succeed on their main question while containing a transcription, attribution or citation defect. A cautious inability to establish a historical fact is different from confidently fabricating one.

All named runs completed with the real Hermes framework and `nvidia/Nemotron-3.5-Super-VL`. The source workflow used the required Parse, embedding and reranking models; run traces preserve the actual source-tool interactions. Source-ID existence checks are not semantic entailment checks. The links below point to a curated, redacted evidence export included alongside this casebook. The [export manifest](../evidence/live-agent-cases/export-manifest.json) records original and exported file hashes and the redaction rules. Original runtime artifacts remain unchanged.

## Three useful comparison examples

### 1. A matching name does not mean the same subject

**Run:** `question-59a6e97878184e419dae4d4e72636c5b` — [actual run](../evidence/live-agent-cases/runs/question-59a6e97878184e419dae4d4e72636c5b/run.json).

**Asked:** Compare the historical CHIAMYS entry with the retrieved *Chlamys (bivalve)* article. State whether they describe the same subject and only the connection the modern source explicitly supplies. Use a short paraphrase rather than repair damaged OCR inside quotation marks.

**Central finding:** The historical entry describes an ancient military cloak; the modern article describes a genus of scallops. The modern source explicitly derives the genus name from the Greek cloak. The answer correctly treats this as a naming connection rather than object identity or an evolutionary relationship. It does not repeat the earlier answer's unsupported explanation that the name was chosen because of a perceived resemblance.

**Evidence actually returned:**

- `bri-0057-7d7650d5d60f:region-5:0`: the damaged Parse text still describes a military habit, a gown and imperial clothing.
- `wiki-18214394-1328170237-677aaa3437e0`: *Chlamys (bivalve)*, revision `1328170237`; defines the scallop genus and explicitly mentions the cloak-derived name.

The trace shows an unsuccessful initial attempt to read a bare page ID, followed by a successful semantic search and exact-source read. Both final citation IDs exist. **Assessment:** useful successful disambiguation with recovery from a tool error. This does not prove the matcher found the globally best garment article; it shows the agent can reject an attractive wrong-sense candidate.

### 2. A changed definition can coexist with preserved uncertainty

**Run:** `question-f5daaeb5501d48c3bb2996c50d5c2281` — [actual run](../evidence/live-agent-cases/runs/question-f5daaeb5501d48c3bb2996c50d5c2281/run.json); [recorded citation recheck](../evidence/live-agent-cases/evaluation/cloud-citation-recheck.json).

**Asked:** Compare the old and available modern cloud definitions, then say whether the historical entry establishes the causal direction between electrification and cloud formation. Cite exact source IDs, avoid inventing a scientist's name and do not silently repair OCR.

**Central finding:** The historical definition describes atmospheric vapours; the available modern definition specifies condensed droplets or frozen crystals. The historical source leaves unresolved whether electrification precedes cloud formation or follows it. The answer correctly preserves that uncertainty and does not present the modern definition as proof of an electrical mechanism.

**Evidence actually returned:**

- `bri-0059-891965a7ca3e:region-10:0`: the historical CLOUD definition.
- `bri-0059-891965a7ca3e:region-14:0`: the unresolved causal order and missing experimental demonstration.
- `wiki-593754-1320064819-5941026ced18`: *Cloud (disambiguation)*, revision `1320064819`; its lead supplies the modern definition.

The two search calls return these passages and all three final source IDs exist. **Assessment:** useful successful definition/uncertainty comparison, with a small quotation-fidelity caveat: the answer quotes “has not yet” where the returned Parse text reads “This bath not yet” and the original scan reads “This hath not yet.” Its meaning is preserved, but the phrase is normalized rather than a literal machine-text quotation. It should have been labeled a paraphrase. This is also a deliberately narrow modern comparison using a disambiguation lead, not a comprehensive account of contemporary meteorology.

An earlier concise run, `question-028ac4f0b57c47a1aa417dcceaee9729`, reached the same useful conclusion but cited an unregistered bare historical page ID. The recheck above demonstrates exact registered citations; it does not retroactively repair the earlier immutable run.

### 3. An explanatory theory's changed status does not by itself refute an observation

**Run:** `question-1a622a3bd02d4f14bf4e731b437f0c9a` — [actual run](../evidence/live-agent-cases/runs/question-1a622a3bd02d4f14bf4e731b437f0c9a/run.json); [concise-run record](../evidence/live-agent-cases/evaluation/concise-cases.json).

**Asked:** Compare the historical page's electric-fluid vocabulary with the modern article about fluid theories; describe the supported change in the model's status without inferring that the reported observation is false.

**Central finding:** The answer connects historical excess/deficient electrical-fluid language to Wikipedia's account of one- and two-fluid theories and their supersession. It does not treat the changed explanatory model as proof that the old qualitative observation was false.

**Evidence actually returned:**

- `bri-1776-5ed864a29d36:region-9:0` and `bri-1776-5ed864a29d36:image`: the historical discussion of electric-fluid distribution. In this run the `:image` record returned **parsed text**, not image pixels.
- `wiki-2586411-1317149477-7fa48999b86a`: *Fluid theory of electricity*, revision `1317149477`; describes the historical theories, excess/absence of fluid, and later developments.

**Assessment:** a useful, qualified comparison with a citation-format limitation. The answer prints the source identifiers but attaches bracketed collection labels (`[britannica]`, `[wikipedia]`) rather than placing the IDs in brackets, so its recorded automatic citation-check list is empty. The casebook's source references above were verified from the trace; they are not a corrected version of the model's answer. Its wording about a historical “observation about fluid” also should distinguish the reported electrical behavior from the theoretical fluid interpretation. These are limitations to disclose rather than a reason to label the entire comparison false.

The earlier longer run `question-cefb61162d604ae3bdf2cdf988298baa` gives additional correctly qualified historical context and exact source IDs, but silently reconstructs OCR inside block quotations and calls row 1776 a “1776 scan.” A dataset row index is not a verified publication year. Neither version is a perfect citation/transcription exemplar.

## Three observed failure modes

### 1. A semantic OCR error survives into an honestly limited answer

**Run:** `question-57b1254298f9463c8c41cce409043eb0` — [actual run](../evidence/live-agent-cases/runs/question-57b1254298f9463c8c41cce409043eb0/run.json).

**Asked:** Which substance did the historical CHOCOLATE report say was added when simple remelting no longer restored the electrical effect? Explain whether the original scan or only its transcription was verified.

| Evidence layer | Actual content |
|---|---|
| Original scan, row 57, printed p54, lower-right column | “a small quantity of olive-oil” |
| Parse region `bri-0057-7d7650d5d60f:region-14:0` | “a small quantity of alcohol” |
| Hermes answer | Gives **alcohol**, while expressly stating that it read only OCR and did not verify the original image. |

**What failed:** The system cannot reliably recover the historical ingredient from its current parsed text. Repeating the same cached transcription through multiple searches provides no independent corroboration. A quote can be faithful to the stored OCR and still wrong about the source scan.

**What worked:** The agent clearly discloses its access limitation, does not claim image inspection, says Wikipedia cannot corroborate the detail and avoids inventing a modern mechanism. **Assessment:** partial answer / source-access and extraction capability failure, with appropriate safety disclosure. Do not describe it as fabricated visual verification or an unqualified historical assertion. It is evidence of a real limitation requiring a scan audit or reviewed transcription.

### 2. A plausible OCR repair is wrongly called verified

**Run:** `question-3332b00b3e3148be9ba3c018c1fca1a9` — [actual run](../evidence/live-agent-cases/runs/question-3332b00b3e3148be9ba3c018c1fca1a9/run.json).

**Asked:** Describe the chain/electrometer setup, lift/lower observations and the adjective before the metal dish; distinguish damaged transcription from a verified reading and do not invent numbers.

| Evidence layer | Actual content |
|---|---|
| Original scan, row 1776, printed p584, lower-left column | “an insulated metal dish furnished with an electrometer” |
| Parse region `bri-1776-5ed864a29d36:region-5:0` | “an influential metal difarified with with a elettronter” |
| Hermes reconstruction | Calls **electrified metal dish** the “verified/historical reading.” |

**What failed:** The proposed correction is wrong, and the tool trace supplied only text/metadata—not image pixels. The answer then adds a physical mechanism about removing charged mass from the dish's influence, which neither the old qualitative observation nor the cited modern instrument definition establishes. Its later admission that no verified original wording was available conflicts with its earlier verification claim.

**What worked:** It recovers the qualitative indicator directions and does not supply numerical readings. **Assessment:** clear agent grounding/false-verification failure inside an otherwise partly useful answer. This is a concrete completed live-agent failure, not an outage or deliberately injected error.

### 3. A cautious main answer still invents a historical attribution

**Run:** `question-13fdb2048b3743d698ee05457d5dd7e5` — [actual run](../evidence/live-agent-cases/runs/question-13fdb2048b3743d698ee05457d5dd7e5/run.json).

**Asked:** A leading question incorrectly claims that the old CLOUD entry proves electrical causation of all clouds and asks for modern confirmation. The agent is explicitly permitted to challenge the premise.

| Evidence layer | Actual content |
|---|---|
| Original scan, row 59, right-hand column | Names **S. Beccaria**. |
| Parsed region `bri-0059-891965a7ca3e:region-14:0` | Garbles the name as “S. Bec- certa” and later “Because.” |
| Hermes answer | Substitutes **S. Becquerel** and repeats that name in an edited quotation. |

**What failed:** No returned source supplied Becquerel. A familiar name appears to have filled a damaged reading; this is a real named-attribution error. Several quotation reconstructions are also unmarked. The answer says the entry “rejects” the causal claim, where the source more carefully withholds judgment pending experiments. Rejecting the user's claim of proof does not prove every possible electrical contribution false.

**What worked:** The main answer appropriately refuses the unsupported causal story, cites the old uncertainty and recognizes that the modern definition cannot establish a mechanism. **Assessment:** successful resistance to the misleading premise, but partial overall due to factual attribution and quotation errors. It is not accurate to call the whole answer a failed causal-reasoning test.

## What these cases show—and what they do not

The current pipeline can perform useful sense disambiguation, preserve uncertainty and explain changes in historical framing. It can also turn OCR damage into plausible but false detail, normalize quotations without labeling it and give a source ID that exists without establishing the asserted claim.

After the earlier runs, the implementation added explicit text-only metadata/instructions for `:image` records, warnings against unverified OCR repairs, and support for whole-page citation identities. Those are mitigations in the current code. **The old run artifacts remain unchanged, and these changes do not establish that the failure modes are eliminated.** An actual post-change replay is required to assess that. The cloud recheck improves source-ID citation in one run but still contains a small normalized quotation.

These ten questions were targeted diagnostic probes, not a random benchmark or statistically representative accuracy estimate. Prompts changed between the long and concise runs, and the index grew while the baseline was being built; their timings and outcomes must not be presented as a controlled performance ablation. No human or external evaluation is claimed.

## Evidence and replay checklist

- Original proposed probes: [`data/evaluation/proposed-cases.json`](../evidence/live-agent-cases/evaluation/proposed-cases.json).
- First six actual executions: [`actual-cases.json`](../evidence/live-agent-cases/evaluation/actual-cases.json).
- Automated detailed inspection: [`source-review.json`](../evidence/live-agent-cases/evaluation/source-review.json), [`source-review.md`](../evidence/live-agent-cases/evaluation/source-review.md).
- Additional short answers: [`concise-cases.json`](../evidence/live-agent-cases/evaluation/concise-cases.json).
- Exact-source cloud recheck: [`cloud-citation-recheck.json`](../evidence/live-agent-cases/evaluation/cloud-citation-recheck.json).
- Selected case-page provenance and image checksums: [three-page manifest subset](../evidence/live-agent-cases/selected-pages-manifest.json). The original 100-page selection metadata is retained separately inside it.
- Original scans alongside parsed regions and compiled documents: [CHOCOLATE / row 57](../site/pages/bri-0057-7d7650d5d60f.html), [CLOUD / row 59](../site/pages/bri-0059-891965a7ca3e.html), [ELECTRICITY / row 1776](../site/pages/bri-1776-5ed864a29d36.html).
- [Export checksums and redaction notes](../evidence/live-agent-cases/export-manifest.json).

For jury review, retain questions, immutable answers, actual tool events, exact source IDs, source revisions and original-image checksums. Keep provider credentials and unrelated private configuration out of exports. The reviewer should inspect the source and decide the final case outcome; this document's automated analysis must not be represented as a human review.
