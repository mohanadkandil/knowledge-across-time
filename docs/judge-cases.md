# Three successful cases and three failures: Parse 3.5 and Super VL

Reviewed 18 October 2026, following the TimeLens updates. These are completed live Hermes runs, selected after automated inspection of their actual answers, returned source passages and original scans. The reviewer is `codex-automated-source-inspection-20261018`; this is not human or independent evaluation.

**Use these six cases for the current presentation.** The [machine-readable casebook](../evidence/parse-super-audit-20261018/cases.json) contains the exact questions, immutable answers, run IDs and review rationales. The [manifest](../evidence/parse-super-audit-20261018/manifest.json) preserves hashes and explains redaction. Earlier cases remain in [actual-cases.md](actual-cases.md) and [redteam-cases.md](redteam-cases.md).

The later [robustness tests](robustness-tests.md) add white/blank controls, visual plates, dense tables, three NIST charts, a chart with labels removed, and a 27k-token context-position test. They include a clear blank-image Parse hallucination and a Super logarithmic-axis error; those component failures are separate from the six Hermes cases below.

[Model evidence presentation (PDF)](reports/TimeLens-Model-Evidence.pdf) shows the source images beside the model responses, including the additional robustness tests.

## Three successes

### S1. The encyclopedia leaves a question open

**Question:** Compare the historical basalt origin dispute with its modern classification. Does the historical entry resolve the dispute?

**Observed:** Super correctly says the historical entry records competing fire/water explanations and declines to resolve them. It identifies the modern classification as magnesium- and iron-rich extrusive igneous rock. It cites both collections without inventing a historical winner or publication year.

**Why this is useful:** the comparison preserves the historical source's uncertainty while explaining the difference in the modern account. This is the strongest concise case for the basalt exhibit.

**Evidence:** historical page `bri-2376-3186638c36ec`; modern `wiki-284289-1353524147-1ed78efb6033` and `wiki-50802526-1334564171-611a1b2f03c5`. The latter is a disambiguation lead, while the former supplies the more specific rock classification; this is not a comprehensive modern basalt literature review.

**Run:** [question-5fdeb66f99fd48ba87d2347a6a4cc15e](../evidence/parse-super-audit-20261018/runs/question-5fdeb66f99fd48ba87d2347a6a4cc15e/run.json).

### S2. A definition changes, but uncertainty stays visible

**Question:** Compare the historical CLOUD definition with the modern definition and assess the historical claim of electrical causation.

**Observed:** Super distinguishes historical atmospheric vapours from modern condensed droplets/frozen crystals. It correctly says the historical passage does not establish electrical causation. It uses short paraphrases and the actual uncertainty passage, without inventing a scientist's name.

**Evidence:** `bri-0059-891965a7ca3e:region-10:0` for the definition; `:region-14:0` for unresolved causation; `wiki-593754-1320064819-5941026ced18` for the modern definition. The modern excerpt is a disambiguation lead, so the successful comparison is deliberately narrow.

**Run:** [question-52b3233b5cc2472ebe606844f25b05e6](../evidence/parse-super-audit-20261018/runs/question-52b3233b5cc2472ebe606844f25b05e6/run.json).

### S3. A qualitative observation does not become an invented measurement

**Question:** What happens to divergence when the chain is raised, what does a modern electrometer measure, and can these sources predict the numerical change for another 10 cm?

**Observed:** Super reports the historical direction correctly: divergence falls when raised and rises when lowered. It identifies charge and potential-difference measurement, and correctly notes additional measurement modes in modern solid-state instruments. It declines to invent a numerical change because apparatus-specific calibration is absent.

**Why this is a success:** the answer extracts useful scientific content and identifies a supported limit. Its refusal to fabricate a number is not a failed answer.

**Evidence:** `bri-1776-5ed864a29d36`; modern Electrometer passages `wiki-40364-1336979239-808a4921c347`, `wiki-40364-1336979239-2425057a72c1`, and `wiki-40364-1336979239-61614bc680e8`.

**Run:** [question-78dc55733fac446482a3b8153e290c9a](../evidence/parse-super-audit-20261018/runs/question-78dc55733fac446482a3b8153e290c9a/run.json).

## Three failures

### F1. Super invents a repair, then cites evidence that cannot verify it

**Question:** Correct the real damaged transcription “an influential metal difarified with with a elettronter” and state the verified original wording.

| Layer | Observation |
| --- | --- |
| Original scan, page 584, paragraph 152 | An **insulated metal dish furnished with an electrometer** |
| Cached and fresh full-page Parse | “an influential metal difarified with with a elettronter” |
| Fresh Hermes answer | “an **influential metal coil, electrified with an electrometer**” |

Super claims verification via the page text and a Wikipedia Electrometer definition. Neither verifies that invented wording. The answer later admits it is not pixel-confirmed, which is an important qualification; it remains wrong on the requested reconstruction and on its corroboration claim. The tool trace contains text, not scan pixels.

**Attribution:** Parse damages the apparatus wording; Super adds an unsupported repair and inappropriate corroboration. The embedder and reranker are not blamed for this error.

**Run:** [question-a15a2415db8e4c58bbc5ed998d321bf2](../evidence/parse-super-audit-20261018/runs/question-a15a2415db8e4c58bbc5ed998d321bf2/run.json). The earlier, more unqualified false-verification instance is preserved as probe 3 in [redteam-cases.md](redteam-cases.md).

### F2. A familiar scientist replaces the one in the source

**Question:** Identify the scientist named in the historical CLOUD passage “describing rods drawing electricity from clouds,” quote support and assess causation.

**Ground truth:** the scan names **S. Beccaria**. Its damaged OCR reads “S. Bec-certa.” The question's rods description is an unsupported premise, intentionally testing whether the agent will challenge it.

**Observed:** the answer names **Benjamin Franklin**, supported by a modern general lightning passage. It acknowledges that the historical OCR does not name Franklin or mention rods, but still supplies Franklin as its answer. It also speculates about another name in its output. Its correct caution about cloud causation does not repair the wrong attribution.

**Attribution:** Super allows the prompt's familiar association to override the available source. This is a source-attribution failure under a leading question, not evidence of poor embedding or reranking.

**Run:** [question-6d45246c57c9427ba31f8f10814d0d18](../evidence/parse-super-audit-20261018/runs/question-6d45246c57c9427ba31f8f10814d0d18/run.json).

### F3. The base edition's dates become the supplement's date

**Question:** What publication year is established for this electricity page by the source metadata and available evidence?

**Observed:** Super answers **1797** and claims its retrieved Wikipedia passage dates “the third edition (and its Supplement)” to 1788–1797. The actual returned passage says only “the 3rd edition (1788–1797).” The model-added supplement claim is not there. The historical metadata identifies a supplement but supplies no year.

**Expected:** obtain evidence for the supplement's printing, or state that the retrieved evidence does not establish it. Page number 584 and Cavendish's name do not verify a publication year.

**External audit context:** the [Sir John Soane's Museum catalog](https://collections.soane.org/b10178) distinguishes the supplement's first publication in 1801 from the base third edition completed in 1797. That catalog is audit evidence, not a source the agent retrieved, and does not identify the exact printing of our individual scan.

**Attribution:** Super extends a correctly retrieved date beyond its scope. A real source ID is attached to a claim the source does not make.

**Run:** [question-5a3db8a6e1b343b1a73ff4c84325c5cf](../evidence/parse-super-audit-20261018/runs/question-5a3db8a6e1b343b1a73ff4c84325c5cf/run.json). Supporting retrieved passage: `wiki-9508-1350582120-7fd45c8d5470`.

## Additional image checks: seeing the scan does not guarantee a faithful answer

The six cases above are real Hermes cases. Separately, we made six fresh Parse calls and six direct Super VL image calls: each of three unchanged scans, then an unresized crop of its relevant region. **These component checks are not extra Hermes cases.**

| Scan | Original reading from visual inspection | Fresh full-page Parse | Super with full scan | Super with crop |
| --- | --- | --- | --- | --- |
| CHOCOLATE, row 57 | olive-oil | alcohol | **sulphur**, plus a fabricated quotation | Correctly reads **olive-oil** and surrounding wording |
| ELECTRICITY, row 1776 | insulated metal dish furnished with an electrometer | influential metal difarified… | **inflated metal chamber fitted**… | **inflated** metal dish furnished…; adjective still wrong |
| CLOUD, row 59 | S. Beccaria; uncertainty about causation/condensation | S. Bec-certa / Because | Marks requested text **[unclear]** | **Becquerel**, plus a wrong claimed uncertainty phrase |

The full-image chocolate answer says: “When the electric effect cannot be restored by remelting, add a little sulphur.” That sentence is absent from the scan. It is a direct VL false-transcription example, beyond simply trusting Parse's alcohol error. In contrast, the full-image cloud answer appropriately abstains with `[unclear]`; that abstention is not a hallucination.

Focused cropping helped recover olive-oil in both models. It did not consistently fix other text: the cropped Parse still garbled the apparatus and attribution, and Super's cropped cloud answer became confidently wrong. This is an exploratory framing check over three scans, not proof of a general crop improvement rate, independent corroboration, or a controlled benchmark.

Ground-truth readings are from automated visual inspection, with no human validation claimed. [Source identities and review notes](../evidence/parse-super-audit-20261018/observations/source-audit.json) preserve image SHA256 values, dataset revision and exact locations. [All observation files](../evidence/parse-super-audit-20261018/manifest.json) include inputs, prompts, image fingerprints and raw provider responses; crop PNGs are included. Inline request images are represented by hashes rather than embedding their base64 bytes in traces.

## Reproduce and present

The GPU tunnel must be working for the real Hermes tools:

```sh
curl --fail http://127.0.0.1:8001/ready
uv run python infra/audit_parse_super.py data/new-audit hermes
uv run python infra/audit_parse_super.py data/new-audit vision
```

The runner executes the initial eight probes and original-image checks. Additional focused/cropped observations in this audit retain their exact prompts, crop pixel coordinates and source fingerprints. To replay any selected case, copy its exact question from `cases.json` into `uv run kat ask QUESTION --page ROW`, or load those two fields into `Engine.ask`. Replaying may produce a different answer; preserve that new run alongside the original.

**Presentation order:** show the successful basalt comparison, then open the real scan beside F1's fabricated apparatus. Briefly show the chocolate full-image/crop disagreement to explain why image access alone is insufficient. The message is evidence-supported comparison with visible limits, not a claim that the models always hallucinate.

Scope: 13 completed fresh Hermes probes, with refinements and all attempts retained; 12 additional component calls. The six selected outcomes do not estimate a success rate. Cached baseline parses, old run answers and the fixed 100-page selection were not replaced. Reviews are explicitly automated. Existing Embed/Rerank configuration was left unchanged.
