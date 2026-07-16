# Phase 0: application foundation and ELI metadata ingestion

Status: implemented

Approval: 2026-07-16 — Pawelo

Implementation verified: 2026-07-16 — Docker Compose, migration, health check
and two live ELI imports (1652 acts; second import created 0 duplicates).

## Problem and outcome

PrawoRadar needs a reproducible local runtime and a trustworthy, rerunnable
foundation for collecting metadata from Dziennik Ustaw (DU) and Monitor Polski
(MP). The first usable outcome is a database populated from a chosen year
without duplicate acts when the same import runs again.

## Scope

- In scope:
  - Docker Compose runtime for the FastAPI application and PostgreSQL with
    pgvector.
  - Async FastAPI skeleton with a health endpoint.
  - Alembic migrations creating `acts` and `job_runs`.
  - An async ELI client for the official yearly-act-list endpoint.
  - A command that imports DU and MP metadata for a supplied year.
  - Idempotent persistence keyed by the ELI identifier and operational records
    for each import attempt.
  - Unit, integration and ELI-client contract-fixture tests.
- Out of scope:
  - Scheduler/cron execution, legislative-process ingestion and text/PDF
    extraction.
  - LLM analysis, embeddings, matching, users, e-mail and web onboarding.
  - Live ELI calls in the normal automated test suite.

## Constraints and assumptions

- Product/legal constraints: imported data is public act metadata; no company
  or personal data is introduced in this phase.
- Technical constraints: Python 3.12+, FastAPI, PostgreSQL plus pgvector,
  SQLAlchemy/Alembic and Docker Compose as selected in the product plan.
- External API assumption: the official ELI endpoint
  `GET https://api.sejm.gov.pl/eli/acts/{publisher}/{year}` returns a yearly
  list of act metadata. The list includes an ELI identifier and `changeDate`;
  the client supports publishers `DU` and `MP` only. Source:
  <https://api.sejm.gov.pl/API_pl.html>.

## Design

Configuration is read only from environment variables and has safe local
defaults for Docker Compose. A thin router exposes `GET /health`; it reports
service and database readiness without exposing configuration or secrets.

The ELI adapter converts remote JSON into a typed internal record. The import
service calls that adapter for one publisher and year, then upserts acts by
their ELI identifier. A rerun updates fields when `changeDate` or other source
metadata changes, but never creates another act row. Every import gets one
`job_runs` record with its lifecycle, counts, timestamps and a safe error
summary.

The initial command is explicit, for example `python -m legal_monitor.ingest
--year 2026`. Scheduling is deferred so a failed or unexpected run is easy to
inspect and repeat during development.

## Acceptance criteria

- [x] `docker compose up --build` starts the app and database locally.
- [x] `GET /health` returns success only when the application can reach the
      database.
- [x] `alembic upgrade head` creates `acts` and `job_runs` from an empty
      database.
- [x] An import for DU and MP persists the tested ELI fixture data, including
      source metadata and `changeDate`.
- [x] Running the same import twice produces no duplicate ELI identifiers and
      records two observable job attempts.
- [x] A changed fixture updates the existing act instead of inserting another
      row.
- [x] Invalid ELI payloads and network failures leave a failed `job_runs`
      record and return a non-zero command result.
- [x] `make ci` passes without live ELI access.

## Risks and human decisions

- ELI schemas or availability may change. Fixtures and explicit payload
  validation make this visible before a production run; live execution needs
  timeout and retry policy but retries do not belong in the initial command.
- A large historical year can contain many records. Phase 0 imports an explicit
  year only and does not add a catch-up loop or scheduler.
- The database schema is intentionally limited. New product concepts require a
  new migration and, when hard to reverse, an ADR.
- The app must not treat a successful HTTP response as proof that all expected
  data was imported; job counts and terminal status are operational evidence.

## Test plan

- Unit: ELI payload conversion, publisher validation and command arguments.
- Integration: migrations, health endpoint, upsert behavior and `job_runs`
  lifecycle against PostgreSQL.
- Contract: versioned, minimal JSON fixtures derived from documented ELI list
  responses; no live network call in CI.
- End-to-end/manual: start Compose, run one import against a selected recent
  year, inspect row counts and rerun it.
- Eval/regression dataset: not applicable until Phase 1 LLM analysis.

## Delivery budget

One bounded Phase 0 implementation. Keep the agent context to this spec, the
product plan, existing quality configuration and official ELI documentation.
Stop before scheduler, PDF extraction or any LLM feature.
