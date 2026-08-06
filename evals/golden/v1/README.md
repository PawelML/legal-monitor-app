# Golden set v1

Add one human-reviewed JSON record per line to `labels.jsonl` and the matching
model projection to `predictions.jsonl`. Do not add PDFs, full extracted text,
API keys or model prompts here.

Each label needs `act_eli`, `business_relevant`, `tags`, a short `rationale`,
`reviewed_by`, and `taxonomy_version: "v1"`. Use only tags listed in
`src/legal_monitor/analysis/taxonomy.py`. The initial baseline requires at
least 50 reviewed acts before it can be committed to `evals/results/`.
