# Phase 2: company profile and matching foundation

Status: implemented

Approval: 2026-08-06 — Pawelo

## Problem and outcome

PrawoRadar has analysed legal acts but cannot yet express which existing
analyses may concern a particular company. The first Phase 2 slice stores a
company profile from the public KRS by KRS number and exposes explainable,
non-deliverable tag matches.

The outcome is a profile containing public registry identity and PKD codes, a
manually selected set of taxonomy tags, and an API preview that returns only
analyses with at least one shared tag and names those tags as the reason.

## Scope

- Async KRS current-extract client using the official Ministry of Justice API,
  with bounded timeout and typed, mock-transport tests.
- KRS-number validation and normalisation; explicit not-found and malformed
  source handling.
- Persistent company profiles containing public KRS identity, current PKD codes,
  manually selected monitoring tags, a source timestamp and refresh time.
- Idempotent profile creation/refresh and a read-only matching-preview API.
- Deterministic tag intersection against persisted, business-relevant analyses.
- Immutable `match_runs` job evidence and a human-readable reason per result.

## Out of scope

- NIP input or persistence, CEIDG/REGON integration, e-mail addresses, users,
  authentication, magic links, consent, delivery, scheduler and public UI.
- Embeddings, PKD-to-taxonomy inference, a numerical match score or any
  threshold that decides whether an alert is delivered.
- Changing the analysis model, prompt, taxonomy, existing analyses or Phase 1
  evaluation results.
- Automatic legal conclusions, enforcement or user-facing notifications.

## Constraints and assumptions

- KRS data and PKD codes are public-source data, but profile identifiers are
  treated as sensitive operational data. This slice accepts KRS only, does not
  persist NIP, e-mail or natural-person details, and does not return raw KRS
  source payloads through the API.
- The official API call is opt-in through an explicit refresh endpoint; tests
  use `httpx.MockTransport` and are network-independent.
- A match is a review queue entry, not an alert. It is intentionally
  conservative in its claims: shared taxonomy tag only.
- The deferred 20/50 Phase 1 baseline is not a release gate for this isolated,
  non-deliverable preview; it remains a gate before automated matching or
  alerts.

## Design

`KrsClient.fetch_current_extract(krs_number)` normalises a ten-digit KRS
number, requests `GET /api/krs/odpisaktualny/{krs_number}` and converts the
minimal public registry fields into a typed `KrsCompanyRecord`. It never logs
the source body. `CompanyProfileService.refresh_from_krs()` inserts or updates
one profile identified by KRS number and records a `profile_refresh` job.

A profile's `monitoring_tags` is a validated subset of taxonomy v1 chosen by
the caller. `MatchingPreviewService.preview(profile_id)` reads the latest
business-relevant analysis for each act, returns an item iff its tags intersect
with `monitoring_tags`, and stores a `matching_preview` job. Returned reasons
are the sorted shared tags; no numerical score exists.

The profile API is deliberately small:

- `PUT /profiles/krs/{krs_number}` refreshes public KRS fields and accepts
  `monitoring_tags` in its JSON body.
- `GET /profiles/{profile_id}` returns the stored safe projection.
- `POST /profiles/{profile_id}/matches:preview` produces the non-deliverable
  preview and returns its job ID and reasons.

## Acceptance criteria

- [x] Invalid, not-found and malformed KRS responses are explicit errors and
      never create a profile.
- [x] Refresh is idempotent for one KRS number and records an observable job.
- [x] A profile has no NIP, e-mail, person or raw-source-payload persistence.
- [x] Only business-relevant analyses sharing a selected tag appear in a
      preview, with an explainable shared-tag reason.
- [x] Re-running a preview creates an observable job but no duplicate match
      records or delivery side effects.
- [x] Tests are network-independent and `make ci` passes.

## Risks and human decisions

- KRS may omit or reshape optional fields; the adapter must reject an unusable
  record rather than guess.
- A tag match is not evidence that a legal act applies to the company. No UI or
  notification may imply otherwise.
- Mapping PKD to tags, accepting NIP/CEIDG data, embeddings, match thresholds,
  user identity and any delivery flow require separate specifications and
  approvals.

## Test plan

- Unit: KRS normalisation/parsing and tag intersection.
- Integration: profile refresh idempotency, failed jobs and preview job records
  using SQLite and a fake KRS client.
- Contract: official KRS-shaped fixture through `httpx.MockTransport`.
- Manual: one explicit local KRS refresh only after tests pass; no production
  delivery.

## Delivery budget

One KRS-backed profile and deterministic matching-preview slice. Stop before
NIP, CEIDG, embeddings, thresholds, authentication, UI, scheduling or e-mail.
