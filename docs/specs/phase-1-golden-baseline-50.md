# Phase 1: 50-act golden baseline completion

Status: implemented

Approval: 2026-08-08 — Pawelo (delegated assessment authority and bounded live pilot)

## Problem and outcome

The current 20-act set is explicitly partial. Complete the existing Phase 1
requirement with 30 source-reviewed acts, producing a 50-act DU/MP baseline
for the unchanged evidence-v2 analysis and matching evaluation.

## Scope

- Extract and assess the following 30 public acts: DU/2026/1000, 1017, 1020,
  1030, 1041, 1047, 145, 147, 197, 202, 207, 209, 16, 108, 109, 117, 130,
  135, 167, 213; MP/2026/160, 169, 170, 1, 10, 11, 12, 108, 112 and 136.
- Add labels and successful evidence-v2 projections for all 50 acts.
- Rerun Phase 1 and Phase 2 matching evals and record a comparison report.

## Constraints

- No change to the model, prompt, taxonomy, evidence protocol or matching rule.
- Labels are based on extracted official text, not titles; no PDFs or secrets
  are committed.
- The 30 live calls use `store=false`, remain bounded to this list and do not
  enable delivery or alerts.

## Acceptance criteria

- [x] All 30 selected official sources are extracted and source-reviewed.
- [x] `labels.jsonl` and `predictions.jsonl` cover exactly 50 matching acts.
- [x] The new sample contains both DU and MP plus at least 20 negative acts.
- [x] Both offline evals run with the 50-act fixture and a report is committed.
- [x] `make ci` passes offline.

## Delivery budget

Thirty extractions, thirty unchanged-model analyses and one comparison report.
Stop before any tuning, threshold, profile, delivery or alert change.
