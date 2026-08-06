# Repository Guidelines

## Project Structure & Module Organization

PrawoRadar monitors Polish legal changes for businesses; it is a monitoring and
early-warning product, not legal advice. Application code is under
`src/legal_monitor/`: `eli/` adapts the Sejm ELI API, `services/` owns business
workflows, `models.py` contains persistence models, and `ingest.py` is the
explicit import command. Alembic migrations live in `migrations/versions/`.
Tests and ELI JSON fixtures are in `tests/`. Product plans are in `plans/`;
approved feature specs and ADRs belong in `docs/specs/` and `docs/adr/`.

## Build, Test, and Development Commands

Use Python 3.12+ and `uv`.

- `make bootstrap` — install locked development dependencies.
- `make ci` — run Ruff, formatting checks, Mypy strict, pytest, and the eval
  command; run this before requesting review or committing.
- `docker compose up --build` — start FastAPI and PostgreSQL with pgvector.
- `curl http://localhost:8000/health` — confirm application and database
  readiness.
- `docker compose exec app .venv/bin/python -m legal_monitor.ingest --year 2026`
  — explicitly import DU and MP metadata for one year.
- `docker compose exec app .venv/bin/python -m legal_monitor.extract --act-eli DU/2026/946`
  — download and extract one official PDF after metadata has been imported.

## Coding Style & Naming Conventions

Use four-space Python indentation, complete type annotations, and async I/O for
network and database operations. Ruff formats and lints; Mypy runs in strict
mode. Prefer small typed adapters and services over framework-heavy modules.
Use `snake_case` for files, functions, variables, and test names; use clear,
domain-specific names such as `MetadataIngestionService` and `source_change_date`.
Do not make live ELI calls in automated tests—use versioned fixtures and
`httpx.MockTransport` instead.

## Testing Guidelines

Write `test_*.py` pytest tests for success, failure, and regression behavior.
Ingestion changes must prove idempotency, source-payload validation, and useful
`job_runs` records. Test user-facing flows at the appropriate level; keep CI
network-independent. Run `make ci` after every meaningful change.

## Commit, Review, and Agent Workflow

Follow the existing Conventional Commit style, e.g.
`feat: add phase zero legal act ingestion foundation` or `chore: ...`.
Keep commits narrow and reviewable. For a feature or cross-cutting change, copy
`docs/specs/_template.md`, define acceptance criteria and tests before coding,
then record approval directly below `Status` as `YYYY-MM-DD — approver`.
Use an ADR for difficult-to-reverse decisions. Review generated changes for API
assumptions, personal-data handling, retries/idempotency, migrations, and
unrelated diff size.

## Security & Operational Boundaries

Keep secrets in environment variables or `.env`, never in Git. Treat NIP and
e-mail as sensitive data in later phases. Do not change LLM prompts, taxonomy,
matching thresholds, database migrations, or production e-mail behavior without
an approved spec, relevant regression/eval evidence, and human approval.
