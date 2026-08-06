# ADR-0002: Pilot OpenAI GPT-5.6 Luna for act analysis

Status: accepted

Date: 2026-08-06

Approval: 2026-08-06 — Pawelo

Prompt approval: 2026-08-06 — Pawelo approved `pilot-v1`; its content remains
only in the ignored runtime environment.

## Context

Phase 1 needs a real analysis provider for a controlled, ten-act pilot. The
provider will receive public, extracted Polish legal-act text and must return a
strictly validated, page-grounded JSON record. The existing deterministic
provider remains the only provider used in automated tests.

This selection is quality- and cost-sensitive. It must not enable background
processing, matching, user alerts, or production delivery until the pilot has
been reviewed against human labels.

## Options considered

1. Keep the static provider only — preserves completely offline execution but
   cannot establish real-world analysis quality.
2. OpenAI `gpt-5.6-luna` through the Responses API — supports structured
   outputs and is intended for cost-sensitive, high-volume text workloads.
3. OpenAI `gpt-5.6-terra` or `gpt-5.6-sol` — potentially higher capability at
   a higher cost; defer unless the pilot shows Luna is insufficient.

## Decision

Use OpenAI `gpt-5.6-luna` only as the explicitly invoked provider for the
Phase 1 pilot. Use the Responses API with SDK-managed Structured Outputs,
`store=false`, and an initial `low` reasoning-effort baseline. The analysis
instructions and API key are environment variables; neither is committed.

The provider is not the application's default runtime path. The analysis CLI
requires a deliberate `--allow-live-call` acknowledgement before it can make a
network request. The provider returns data to the existing schema and
page-grounding validation, which remains the persistence gate.

## Consequences

- A 10-act pilot must record output quality, failures, latency and estimated
  cost, then receive human review before enabling the provider by default.
- The pilot should compare `low` with `medium` reasoning effort only if the
  initial results show material quality uncertainty.
- Full source text is sent to OpenAI only for the explicitly selected public
  act; no NIP, e-mail, account data or user content is in scope.
- `OPENAI_API_KEY` and `OPENAI_ANALYSIS_INSTRUCTIONS` must be supplied outside
  Git. Missing configuration fails before a request is attempted.
- Golden-set evaluation, quality thresholds and later model/prompt changes
  remain separate approval gates.
