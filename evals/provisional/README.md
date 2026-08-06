# Provisional label proposals

These labels are AI-authored review proposals based on the extracted official
act text. They are not a human-reviewed golden set, must not establish an eval
baseline, and must not authorize a model, prompt, taxonomy, matching threshold
or user-facing alert.

The 10 records in `pilot-v1-label-proposals.jsonl` were accepted by Pawelo on
2026-08-06 and copied to the approved seed set in `evals/golden/v1/`.

Each record has the same decision fields as a golden label plus its provenance.
After a human accepts an individual record, copy it into `evals/golden/v1/`
with `reviewed_by` set to the human approver and the approval date recorded in
the relevant specification or review note.
