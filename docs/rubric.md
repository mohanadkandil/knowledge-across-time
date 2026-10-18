# Submission acceptance checklist

Source: organizer's 18 October 2026 participant brief. Unverified work remains incomplete. This checklist does not assign our own jury score.

| Category | Points | Evidence to retain |
| --- | ---: | --- |
| Completion | 20 | All five checks below |
| Creativity: originality | 10 | A working team contribution beyond the starter, demonstrated on actual sources |
| Creativity: value | 10 | A clear example of how that contribution improves understanding |
| Parse 3.5 | 15 | Real calls, source fidelity review, preserved structure in compiled LaTeX |
| Embed and Rerank VL | 15 | Both models execute; embeddings retrieve and reranking changes downstream evidence |
| Hermes extension | 10 | A working added tool or workflow and a useful task it completes |
| Super 3.5 VL | 20 | Real Hermes integration, useful comparisons, grounding in both sources, appropriate uncertainty |

The five completion checks are worth four points each:

- Extract the selected scans and present compiled LaTeX documents on a static website.
- Process all 100 selected pages through matching. Keep failures and weak matches visible; the requirement does not demand perfect accuracy.
- Explain the comparison method and cite evidence from both collections.
- Deliver the Hermes comparison agent with three successful and three clear failure cases from the team's own runs.
- Submit the public repository and three-minute video showing successes and failures. Include the website, compiled documents, analysis and case documentation.

Use `kat status`, `kat doctor` and the export checklist to inspect progress. A configured endpoint, installed dependency or planned scenario does not establish execution. Temporary stub tests check software behavior; they do not count as the six model cases.

Keep a failed initial attempt separate from a repaired run. Do not label an appropriate refusal as a model failure simply to fill the case quota. Explain what failed, what evidence was available, and what the failure reveals about the pipeline.
