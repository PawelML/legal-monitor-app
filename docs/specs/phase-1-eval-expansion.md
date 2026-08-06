# Phase 1: balanced evaluation expansion

Status: approved

Approval: 2026-08-06 — Pawelo (delegated assessment authority)

## Problem and outcome

The original approved seed has nine business-relevant acts and one negative
candidate, so it gives weak evidence about false alerts. Expand it to a
20-act, source-reviewed v2 evaluation set with a meaningful negative portion.

## Scope

- Extract and independently assess ten additional official DU acts.
- Add immutable human-delegated labels and v2 predictions for all 20 acts.
- Record offline metrics and a concise error analysis.

Out of scope: changing the model, prompt, taxonomy, thresholds, matching,
database schema, scheduling, notifications, or user-facing workflow.

## Constraints and assumptions

- Assessments use the extracted official PDF text, not title alone, and are
  product relevance judgements rather than legal advice.
- Pawelo has delegated the labelling assessment to the implementation agent.
- The existing taxonomy v1 is retained; a missing precise tag is recorded as a
  limitation, not remedied in this change.
- Calls remain an explicit, bounded twenty-act v2 pilot with `store=false`.

## Design

The additional positive candidates are DU/2026/107, 188, 239 and 1046.
The additional negative candidates are DU/2026/103, 116, 172, 189, 212 and
1023. DU/2026/103 is a deliberate edge case: its consolidated text contains
employer duties, but its publication does not itself change those duties.
Each is extracted before its label is set. The existing ten labels and their
predictions remain unchanged. The committed prediction fixture is regenerated
only from successfully persisted `pilot-v2-eval` analyses.

## Acceptance criteria

- [x] All ten selected official PDFs are extracted successfully.
- [x] Twenty source-reviewed labels are committed, with at least six negative
      candidates overall.
- [x] Each matching v2 prediction is persisted with deterministic evidence.
- [x] `make eval` covers all twenty acts and a report records outcomes.
- [x] `make ci` passes offline.

## Risks and human decisions

- Relevance is intentionally conservative: an act targeting only government,
  armed forces, electoral administration or international relations is a
  negative candidate unless its text creates a direct general business duty.
- This expansion does not justify automatic alerts or legal conclusions.
- Any taxonomy, threshold, prompt, model or rollout decision needs a separate
  approved specification and evidence.

## Test plan

- Unit: existing fixture validation and metrics tests.
- Integration: extraction and persisted v2 analysis for each selected act.
- Eval: offline comparison of the complete twenty-act fixture.

## Delivery budget

Ten official PDF extractions, ten bounded live v2 calls, one evidence report.
Stop after evaluation; do not tune the system in response to the result.
