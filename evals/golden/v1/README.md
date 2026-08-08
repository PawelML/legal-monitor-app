# Golden set v1

`labels.jsonl` contains the approved 50-act Phase 1 baseline. Add one
human-reviewed JSON record per line and the matching model projection to
`predictions.jsonl` only through a separately approved evaluation change. Do
not add PDFs, full extracted text, API keys or model prompts here.

Each label needs `act_eli`, `business_relevant`, `tags`, a short `rationale`,
`reviewed_by`, and `taxonomy_version: "v1"`. Use only tags listed in
`src/legal_monitor/analysis/taxonomy.py`. The approved baseline metrics are
stored in `evals/results/baseline-v1.json`.

With labels but no complete matching predictions, `make eval` reports a pending
state and succeeds without manufacturing a metric. A mismatch in a non-empty
prediction file remains an error.
