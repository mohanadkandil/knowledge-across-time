# Robustness tests: blank pages, diagrams, charts and long context

Executed 18 October 2026 against the configured Nemotron Parse 3.5 and Nemotron 3.5 Super VL endpoints. These are additional component diagnostics, separate from the [three successful and three failed real Hermes cases](judge-cases.md). Embed/Rerank configuration was unchanged.

The test plan, input hashes, questions and expected properties were saved before these calls. Inspection is automated by Codex, not human or independent evaluation. [Evidence and provenance](../evidence/robustness-audit-20261018/manifest.json) include all outcomes; failures were not edited into successes.

## What we tested and actually observed

| Test | Expected behavior | Parse 3.5 | Super VL |
| --- | --- | --- | --- |
| Completely white page | No text or inferred subject | **Invents 28,356 characters**, repeats figure references, reaches the 8,744-token limit | Correctly says blank; refuses to invent a medical treatment |
| Actual blank Britannica scan, row 15 | Recognize stained paper without readable article content | Correctly returns an empty Picture region | Correctly says no readable text or treatment |
| Crowded geometry plate, row 1261 | Preserve figure labels without inventing prose or time-series data | **Repeats A/B labels until the token limit**; output is truncated | Correctly identifies geometric diagrams rather than a measured trend; small plate-number details are not independently scored |
| Illustrated MICROSCOPE plate, row 2078 | Identify instrument; avoid an invented magnification | Extracts some heading/figure text and labels, with omissions/garbling | Correctly identifies microscopes and says figure 24 establishes no numerical optical magnification |
| Dense historical mineral table | Keep values in their correct row and column | **Misreads numerical cells**, e.g. second Silica value as 59 rather than 58; Alumina as 31.5/44.5 rather than 23.5/24.5 | Correctly reads the requested Silica, Lime and total values; some heading spelling is imperfect |
| NIST histogram | Read axes; preserve plotted values; avoid invented units | Reads axis names but produces an inaccurate numerical table | Correctly returns tallest count about 18 and no printed physical units, but omits the requested title/axis labels |
| NIST bimodal histogram | Identify the two-mode structure without inventing physical causes | Produces an unreliable numerical table, compressing the plotted horizontal range | Correctly identifies bimodality, axes and absent physical units/causal evidence; its approximate mode-location wording is not treated as a verified numerical result |
| NIST Weibull chart | Recognize logarithmic scales; distinguish cumulative hazard from probability | Produces inaccurate point estimates, e.g. first time 20 versus publisher's 37 | **Calls x linear when both axes are logarithmic**; correctly counts six markers and avoids interpreting hazard as probability above 100% |
| Histogram with all labels/ticks removed | Describe visible bars, abstain on exact units and data values | **Emits an uncalibrated numerical table** with invented generic columns and values | Correctly says exact ticks, units and subject cannot be established |
| Long comparison context | Retrieve correct historical/modern sources and preserve uncertainty at different positions | Not a parser task | Passes the specified checks in the short control and all three long positions |

The blank and geometry decoder failures are not network outages: provider responses were received with `finish_reason=length`. Our adapter correctly rejects the truncated outputs and keeps the raw provider response. They are extraction failures, not completed Hermes failure cases.

## Strongest new examples to show

### 1. A blank image becomes a fictional document

Input: a synthetic 600 × 836 white PNG, distinct from the required historical sample. Parse receives only its official document-parsing prompt and the image, not the leading medical question used separately for Super.

Its response begins:

> will be able to provide the necessary information for the information. We have used this information on the website and we can use the same method as described in Section 2.

It then repeats assertions about results shown in numbered figures, despite the white image containing no text or figures. Output: 8,744 completion tokens; 28,356 characters; truncated. Super recognizes the same image as blank. The actual historical blank scan is handled correctly by both, so a claim that all blank inputs fail would be false.

Files: [white input](../evidence/robustness-audit-20261018/white-control.png), [Parse observation](../evidence/robustness-audit-20261018/images/blank-white/parse/result.json), [Super observation](../evidence/robustness-audit-20261018/images/blank-white/super-image/result.json).

### 2. A chart scale is confidently misidentified

Input: NIST's [Weibull cumulative-hazard figure and source explanation](https://www.itl.nist.gov/div898/handbook/apr/section2/apr222.htm). The horizontal tick positions and publisher's description establish logarithmic x and y scales.

Super says: **“X-axis: linear. Y-axis: logarithmic.”** This is a clear visual interpretation error, independent of embedding/reranking. It correctly reads the title, six points and axis names, and correctly avoids treating cumulative hazard as a probability above 100%.

The source page supplies six failure times and cumulative-hazard values; Parse's recovered numerical table disagrees with them. The first time is 37 in the publisher's table but 20 in Parse. These observations warn against treating generated chart tables as exact digitization; they do not establish a general numerical error rate.

Files: [chart](../evidence/robustness-audit-20261018/loghazard-0.png), [Parse observation](../evidence/robustness-audit-20261018/images/nist-log-hazard/parse/result.json), [Super observation](../evidence/robustness-audit-20261018/images/nist-log-hazard/super-image/result.json).

### 3. Removing labels does not remove the parser's numbers

Input: an explicitly derived crop of NIST's histogram, retaining bars while removing title, tick values and axis labels. This is a negative control, not an unmodified publisher image.

Super correctly abstains on exact coordinates, units and subject. Parse emits columns `column_1`/`column_2` with numeric rows such as `1 | 0`, `2 | 5`, and `3 | 10`. Those may resemble an invented indexing/height scheme, but the source provides no calibration for interpreting them as actual data. They must not be passed downstream as source measurements.

Files: [unlabeled crop](../evidence/robustness-audit-20261018/histogram-without-labels.png), [Parse observation](../evidence/robustness-audit-20261018/images/chart-without-labels/parse/result.json), [Super observation](../evidence/robustness-audit-20261018/images/chart-without-labels/super-image/result.json).

## Long-context comparison: what the passing result means

The same historical CLOUD passages and modern definition were tested in:

- A short two-document control: 3,272 context characters; 1,061 provider-reported input tokens.
- An 18-document context: 106,321 context characters; 27,185 provider-reported input tokens.
- Historical target at the beginning, middle and end of the long context. The modern target remained at the end; document texts were otherwise held constant.

Four checks were defined: correct historical document ID, correct modern document ID, preservation of historical causal uncertainty, and a literal quotation present in the supplied historical text. **All four checks passed in all four conditions.** Definitions were also inspected and remained appropriate.

The long context uses real saved source text, including damaged OCR. Quotes were checked against that input text, not certified as accurate scan transcriptions. Some chosen quotes do not themselves demonstrate the uncertainty claim; the full source passage does. These checks do not measure exhaustive citation entailment.

This is one targeted comparison question with one run per position. It is not evidence of universal long-document understanding, a context-window limit, or a statistically representative “lost in the middle” benchmark. No long-context failure was observed here, and none is fabricated to fill a quota. The failed image tests and passed context tests should be reported together.

## Inputs, scope and replay

External figures are from NIST, the original chart publisher:

- [Histogram / Michelson dataset example](https://www.itl.nist.gov/div898/handbook/eda/section3/eda33e.htm).
- [Symmetric bimodal histogram](https://www.itl.nist.gov/div898/handbook/eda/section3/histogr4.htm).
- [Weibull cumulative-hazard example](https://www.itl.nist.gov/div898/handbook/apr/section2/apr222.htm).

Download URLs, timestamps, original image hashes and the lossless RGB-PNG conversions are retained in `internet-inputs.json`. Only pixels and each test's question were sent to Super; publisher explanations/data were used for review, not secretly supplied as model answers. Original charts and derived controls are distinguished in the input plan.

Execution: nine image conditions × two model endpoints, plus four direct Super context requests: **22 component tasks**. The question-specific Super calls and official generic Parse calls are different tasks, so this is not a fair head-to-head model ranking. Temperature was zero. The two truncated Parse responses remain errors, with their raw content preserved.

```sh
# Copy the retained inputs from evidence into a fresh output directory first.
uv run python infra/audit_robustness.py data/new-robustness-audit images
uv run python infra/audit_robustness.py data/new-robustness-audit context
```

For the image runner, retain names `histogram-0.png`, `bimodal-0.png`, `loghazard-0.png` and `basalt-table.png` from the input provenance. Synthetic white and unlabeled controls are created deterministically. The other input scans come from the existing selected dataset. The context runner reads the current saved source registry, so compare its generated plan with the archived plan before treating a replay as identical.

The fixed 100-page sample, cached parses and earlier agent answers were not replaced. These external charts do not count toward required Britannica coverage or the six Hermes cases. The main casebook remains [judge-cases.md](judge-cases.md).
