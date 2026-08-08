# 50-act golden baseline — 2026-08-08

## Scope and controls

This report records the approved Phase 1 completion run from
`phase-1-golden-baseline-50.md`. It extends the already reviewed 20-act set
with 30 public official ELI sources: 20 DU acts and 10 MP acts. Each source
was extracted and source-reviewed before labelling. The bounded live analyses
used `gpt-5.6-luna`, the existing evidence-v2 protocol and unchanged
`baseline-v1` prompt version, with `store=false`.

The run establishes evaluation evidence only. It does not change the model,
prompt, taxonomy, matching rule, threshold, delivery or alert behaviour.

## Phase 1 analysis evaluation

`make eval` evaluated all 50 committed label/prediction pairs:

| Metric | Result |
| --- | ---: |
| Relevance precision | 0.7436 |
| Relevance recall | 0.9667 |
| Tag micro precision | 0.4667 |
| Tag micro recall | 0.6000 |
| Tag macro precision | 0.4556 |
| Tag macro recall | 0.5758 |

The committed `evals/results/baseline-v1.json` is the first 50-act baseline.
It is intentionally a measurement record, not a release threshold or a basis
for automatic delivery.

## Phase 2 deterministic matching evaluation

`make matching-eval` evaluated 200 semantic pairs: 50 acts by four fictional
profiles. The reviewed no-match defaults in the fixture make the full matrix
explicit while every expected match remains a specific profile override.

| Metric | Result |
| --- | ---: |
| Overall precision | 0.4590 |
| Overall recall | 0.8750 |
| True positives | 28 / 32 expected matches |
| Predicted matches | 61 |
| Evaluated pairs | 200 |

Per-profile precision/recall: construction contractor 0.3077 / 1.0000; food
producer 0.5882 / 0.7143; road-freight carrier 0.5385 / 1.0000; tax-advisory
firm 0.3889 / 1.0000. The machine-readable result is
`evals/matching/results/baseline-50-v1.json`.

The low precision and incomplete food-profile recall confirm that plain tag
intersection is a diagnostic baseline only. No tuning was performed in this
slice; any change requires a separately approved specification and an eval
comparison.

## Verification

The offline commands `make eval`, `make matching-eval` and `make ci` pass
against committed fixtures. They make no network, database or model call.
