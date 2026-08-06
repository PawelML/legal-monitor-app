# Phase 2: deterministic matching evaluation

Status: implemented

Approval: 2026-08-06 — Pawelo

## Problem and outcome

The matching preview has no measured quality. Before adding NIP, CEIDG,
embeddings, thresholds or delivery, PrawoRadar needs a reproducible evaluation
of the existing tag-intersection rule against company-specific expectations.

The outcome is an offline 20-act × 4-fictional-profile matrix with reviewed
expected matches, deterministic predictions derived from the committed v2
analysis projections, aggregate and per-profile precision/recall, and a
committed baseline result.

## Scope

- Four fictional profiles: road-freight carrier, construction contractor, food
  producer and tax-advisory firm.
- A complete 80-pair expected-match matrix for the current approved 20-act
  Phase 1 set, with concise rationales and delegated human assessment record.
- Offline matching metrics based on the same `business_relevant` and tag
  intersection semantics as `MatchingPreviewService`.
- Per-profile and aggregate precision/recall, a `make matching-eval` command,
  regression tests and committed initial result.

## Out of scope

- Changing the 20 Phase 1 labels, model, prompt, taxonomy, evidence protocol,
  matching rule, match threshold or profile API.
- NIP, CEIDG, PKD-to-tag inference, embeddings, users, UI, scheduler,
  delivery or alerting.
- Any legal conclusion that a particular act applies to a real company.

## Constraints and assumptions

- The profiles are fictional and contain only general sector descriptions and
  manually chosen taxonomy tags; no real-company or personal data is used.
- Missing an expected match and emitting an unexpected match are both reported;
  no numerical release threshold is invented in this slice.
- The 20-act Phase 1 set is explicitly partial. Its matching baseline is a
  diagnostic baseline, not evidence sufficient to enable delivery.

## Design

`evals/matching/v1/profiles.jsonl` supplies a profile ID and monitoring tags.
`labels.jsonl` stores one reviewed boolean for every profile/act pair.
`legal_monitor.match_evals.run` reads the existing Phase 1 projection fixture,
predicts a match only where an analysis is business-relevant and its tags
intersect with the profile tags, validates complete pair coverage and writes
aggregate plus per-profile precision/recall. No database, network or model is
used.

## Acceptance criteria

- [x] Four fictional profiles and all 80 reviewed pair labels are committed.
- [x] The command rejects incomplete, duplicate or unknown profile/act pairs.
- [x] Prediction semantics match `MatchingPreviewService` exactly.
- [x] Aggregate and per-profile results are committed and documented.
- [x] `make ci` runs the matching eval offline and passes.

## Risks and human decisions

- A match label is a product-relevance judgement, not legal advice; the
  assessment authority is delegated by Pawelo for this bounded fixture.
- Tag overlap cannot capture company size, products, exemptions or timing.
  Poor results must lead to a separately approved design change, not hidden
  heuristics or a threshold adjustment.
- The deferred 50-act Phase 1 baseline remains required before any automatic
  delivery decision.

## Test plan

- Unit: match construction, aggregate metrics and per-profile metrics.
- Regression: unknown, duplicate and incomplete pair coverage fail clearly.
- CI: run only committed fixtures without a network, database or model call.

## Delivery budget

One 80-pair diagnostic matching baseline. Stop after recording the result;
do not tune model output, tags or matching behaviour.
