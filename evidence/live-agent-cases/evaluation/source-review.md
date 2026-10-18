# Automated source inspection of six actual Hermes runs

Reviewed 2026-10-18T12:29:24.218222+00:00. **This is automated source inspection, not human review.** No Store.review records were created and no model/GPU calls were made.

All six runs completed using real Hermes. Strict source-grounding classification: **0 unqualified successes, 5 partial results, 1 clear failure**. On the central task, **4 succeeded, 1 was partial and 1 failed**. This distinction preserves useful behavior without hiding unsupported additions or forcing a three/three split.

| Case | Core task | Source-grounding assessment |
|---|---|---|
| proposed-success-01-wrong-sense | success | partial |
| proposed-success-02-cloud-definition-and-limits | success | partial |
| proposed-success-03-electric-fluid-context | success | partial |
| proposed-failure-01-olive-oil-transcription | partial | partial |
| proposed-failure-02-insulated-chain-transcription | failure | failure |
| proposed-failure-03-cloud-causation-overclaim | success | partial |

## Strongest demonstrated behavior

The garment/bivalve distinction, cloud definition/uncertainty comparison, historical fluid-theory comparison and refusal of the leading cloud-causation premise were useful. The first three need quotation and attribution repairs before being presented as flawless source-grounded answers.

## Clear actual failure

The chain answer calls **electrified** the verified historical reading of the damaged adjective. The original scan reads **insulated**. The tools returned only OCR text, including the source named `:image`; no image pixels were inspected. Its added charge-mechanism explanation is not established by the cited old observation or modern instrument definition. The answer later admits that no verified original text was available, contradicting its earlier verification claim.

## Two important qualified limitations

The chocolate answer reports **alcohol** from the erroneous OCR while explicitly saying it did not inspect the original and cannot verify it. The original reads **olive-oil**. Document this as an unresolved extraction/source-access capability limit with a useful safety disclosure—not a fabricated scan-inspection claim.

The leading cloud question is correctly rejected, but the answer invents **Becquerel** where the original says **Beccaria** and the tool text is garbled. This is an actual named-attribution error inside an otherwise useful uncertainty-preserving response. Withholding judgment should also not be paraphrased as disproving every possible electrical role in cloud formation.

## Per-run notes

### proposed-success-01-wrong-sense

Run: `question-bab7865574f24a39aa9163a3be24cce2`. Core task: **success**; strict classification: **partial**.

Correctly separates a garment from a bivalve and identifies a real naming link. Adds an unsupported reason for the naming and presents editorially repaired historical prose as a direct quotation.

- **material_grounding:** named after the Greek cloak because of some perceived resemblance. The returned Wikipedia passage states the name is taken from the cloak; it does not state why the name was chosen. Suggested repair: Remove the perceived-resemblance explanation or provide a separate actual source.
- **quote_integrity:** Historical block quote starts CHIAMYS, in antiquity ... over the tunics ... participants [in war]. The tool text says in anitantly, over the tunes, and participants without the added [in war]. Some additions are bracketed, others silently normalized. Suggested repair: Label it a paraphrase/normalized reading; retain a separate verbatim machine-text quote.

### proposed-success-02-cloud-definition-and-limits

Run: `question-48b092cd09014a209aac88510e46f112`. Core task: **success**; strict classification: **partial**.

Answers the requested two-source definition comparison and preserves the unknown electrical causal order. Several historical excerpts are normalized or reconstructed without consistent labeling, and visibility as a secondary question is an interpretive gloss.

- **quote_integrity:** Reconstructed long historical causal-order quotation and natural theory quotation. The returned Parse region contains vapore wherever they are compounded using first electrically and impossible to buy down, while the answer silently repairs parts inside quotation marks. Original-scan sense is broadly consistent, but these are not verbatim tool quotations. Suggested repair: Use exact excerpts or explicitly label a normalized paraphrase; do not call it a literal quote.
- **interpretive_gloss:** Britannica treats visibility as a secondary question. The source describes initially invisible vapour and condensation; it does not explicitly rank visibility as secondary. Suggested repair: Describe the wording directly without asserting a hierarchy of questions.

### proposed-success-03-electric-fluid-context

Run: `question-cefb61162d604ae3bdf2cdf988298baa`. Core task: **success**; strict classification: **partial**.

Useful historically contextualized comparison supported by actual Wikipedia passages, including the competing theories and their later status. Historical block quotes silently repair OCR; the phrase 1776 scan risks confusing row index with date.

- **quote_integrity:** redundant fluid much denser near the surface ... near the exit ... proportional to [surfaces]. The actual returned region says near the furnace, and other surrounding words differ. The original scan supports surface but no image was transmitted through the tools; the answer did not identify this as an inferred correction. Suggested repair: Label reconstruction explicitly and distinguish tool text from scan-verified text.
- **metadata_ambiguity:** Supplement ... 1776 scan. 1776 is the selected dataset row index, not a supplied publication date. Suggested repair: Say row 1776 / printed p584; use publication date only from verified edition metadata.

### proposed-failure-01-olive-oil-transcription

Run: `question-57b1254298f9463c8c41cce409043eb0`. Core task: **partial**; strict classification: **partial**.

The answer gives alcohol, which the current OCR says but the original scan does not: the original reads olive-oil. Crucially, it states the limitation clearly. This is an unresolved pipeline capability failure, not fabricated scan verification or an unqualified claim of historical truth.

- **decision_relevant_transcription:** the substance ... is alcohol. The original CHOCOLATE scan region shows olive-oil. The current Parse and every repeated search return the same erroneous alcohol reading. Suggested repair: Answer that the OCR reports alcohol but the original is unverified; an image audit or reviewed transcription is required before identifying the historical ingredient.
- **evidence_independence:** the decision-relevant sentence is consistent across both searches. Both searches read the same stored parse. Agreement is not independent corroboration. Suggested repair: Describe it as the same cached transcription repeated, not additional support.

### proposed-failure-02-insulated-chain-transcription

Run: `question-3332b00b3e3148be9ba3c018c1fca1a9`. Core task: **failure**; strict classification: **failure**.

It invents electrified metal dish as the verified/historical correction of influential. The actual scan reads insulated. No tool supplied image pixels. It also adds a physical explanation not established by either cited text.

- **false_verification:** The verified/historical reading is ... electrified metal dish. Actual scan: insulated metal dish. Returned tool: influential metal difarified. All read_source results, including :image, contain text/metadata rather than image pixels. Suggested repair: Flag the uncertain OCR word; inspect the original before proposing a correction; label any guess unverified.
- **unsupported_mechanism:** lifting the chain away removes charged mass from the influence of the dish ... divergence collapses. The old passage reports qualitative divergence changes, not this mechanism. Wikipedia electrometer definitions describe instruments, not the exact chain setup. Suggested repair: Keep the recorded qualitative observation and state the mechanism requires additional evidence.
- **internal_inconsistency:** verified/historical reading ... versus no verified typographical text ... I flag its corruptions rather than presenting a reconstructed original as fact. These statements occur together in the same answer. Suggested repair: Use a single explicit evidence-status label and preserve uncertainty throughout.

### proposed-failure-03-cloud-causation-overclaim

Run: `question-13fdb2048b3743d698ee05457d5dd7e5`. Core task: **success**; strict classification: **partial**.

The central answer is appropriately skeptical and source-supported. It independently replaces Beccaria with Becquerel and overstates withheld judgment as rejection; these are genuine attribution/interpretation errors.

- **false_named_attribution:** S. Becquerel had proposed ... experiments of [Becquerel]. The original scan names S. Beccaria. The current tool text has S. Bec-certa / Because, not Becquerel. No tool result supplies Becquerel. Suggested repair: Preserve a disputed/garbled name or read the original; do not silently substitute a familiar scientist.
- **epistemic_overstatement:** the entry rejects the causal claim / That claim is false. The entry states the causal direction is unresolved and experimental foundation missing. This refutes the user premise that it is proven, not necessarily every possible electrical contribution to cloud formation. Suggested repair: Say the claim of proof is unsupported; preserve open causal uncertainty.
- **quote_integrity:** impossible to bring down any natural theory .... Current Parse says impossible to buy down; original scan says impossible to lay down any rational theory. The answer is a third reconstruction. Suggested repair: Quote the stored text faithfully or label a reviewed transcription/paraphrase.

## Shared implementation lessons

- Bare page IDs are not source IDs; every run first encountered that lookup error and recovered. A page-context tool or explicit source list could avoid it.
- Label original-image availability accurately; a source called `:image` currently contains text and an image hash, not pixels.
- Preserve exact tool quotations or label normalized paraphrases. A plausible OCR repair is not a verified reading.
- Human reviewers should choose final success/failure cases after checking original scans and the complete run traces. These automated labels must not be presented as external or human evaluation.
