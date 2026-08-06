# Phase 1: deterministic evidence references v2

Status: approved

Approval: 2026-08-06 — Pawelo

## Problem and outcome

The Phase 1 pilot showed that the model can classify acts but often fails the
strict gate because it rewrites rather than copies PDF quotations. The outcome
is an evidence protocol in which the model selects a stable source-fragment ID
and the application persists the exact text of that fragment.

## Scope

- Split each normalised extracted page into stable, bounded chunks identified
  as `p{page}-c{chunk}`.
- Send chunk identifiers with their text to the analyser.
- Accept only chunk identifiers from the model and materialise stored page and
  quotation fields from the matching source chunk.
- Version the persisted analysis schema as `v2` while preserving v1 records.
- Rerun the same approved 10-act seed as an explicit paid pilot comparison.

## Constraints and assumptions

- The source PDF remains authoritative; no model-supplied quotation is stored.
- The raw v2 evidence instructions and API key remain only in `.env`.
- Chunk selection is evidence for relevance, not legal advice or a legal
  conclusion.
- No taxonomy, matching, user alert, scheduler or email behaviour changes.

## Design

Chunks contain at most 450 normalised characters and are numbered in source
order. The OpenAI Structured Outputs schema exposes `EvidenceReference` with a
pattern-constrained `chunk_id`. `ActAnalysisService` resolves every ID before
persistence and runs the existing page-quotation validation over the
materialised output. Unknown references fail the job without an analysis.

## Acceptance criteria

- [ ] Model input contains stable page/chunk identifiers.
- [ ] A valid v2 response persists only exact quotations taken from selected
      source chunks.
- [ ] Unknown chunk IDs leave no analysis and record a failed job.
- [ ] The same 10-act seed produces a committed v1/v2 pilot comparison.
- [ ] `make ci` remains offline and passes.

## Risks and human decisions

- Chunk choice can still be irrelevant or incomplete; human review of the
  approved seed remains required.
- The pilot may show that a higher reasoning effort or different model is
  warranted, but neither change is made by this spec.

## Test plan

- Unit: chunk identifiers, chunk boundaries and reference materialisation.
- Integration: accepted and unknown references through `ActAnalysisService`.
- Pilot: rerun the approved ten-act seed and compare completion, classification,
  latency and token evidence with v1.

## Delivery budget

One bounded Phase 1 protocol revision and one ten-act comparison. Stop before
changing the model, taxonomy or any user-facing workflow.
