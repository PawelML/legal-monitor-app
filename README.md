# PrawoRadar

Early-warning monitoring of Polish legal changes for businesses. The product
explains what changed, who may be affected and when it takes effect. It is a
monitoring service, not legal advice.

## Status

Phase 0 (ELI metadata ingestion) and the bounded Phase 2 profile/matching
foundation are implemented. Phase 1 has extraction, validated analysis and a
20-act offline evaluation set; the remaining 30 labels for its 50-act baseline
are intentionally deferred. Matching is a review-only preview, never an alert.

## Local development

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
make bootstrap
make ci
```

To run the Phase 0 stack locally:

```bash
docker compose up --build
curl http://localhost:8000/health
docker compose exec app uv run python -m legal_monitor.ingest --year 2026
```

The import command is deliberately explicit in Phase 0. It imports DU and MP
metadata for one year, writes one `job_runs` record and can be safely rerun;
scheduling and PDF extraction arrive in later phases.

## Controlled OpenAI analysis pilot

The OpenAI provider is deliberately opt-in and not used by tests or background
jobs. Copy `.env.example` to `.env`, set `OPENAI_API_KEY` and the separately
approved `OPENAI_ANALYSIS_INSTRUCTIONS`, then invoke exactly one act with an
explicit acknowledgement:

```bash
docker compose exec app .venv/bin/python -m legal_monitor.analyze \
  --provider openai --allow-live-call --act-eli DU/2026/946 \
  --prompt-version pilot-v1
```

This sends only the selected public act text for analysis. The provider uses
`gpt-5.6-luna` by default, persists only schema- and evidence-validated output,
and sets API response storage to false. See
[ADR-0002](docs/adr/0002-openai-luna-analysis-pilot.md) for the pilot gates.

`make ci` is the local equivalent of the mandatory CI gates. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the delivery workflow and
[the plan](plans/legal-monitor-plan.md) for the product roadmap.

## Company profile and matching preview

Phase 2 accepts a public KRS number, stores only a safe registry projection
(name, legal form and PKD codes), and lets the caller select existing taxonomy
tags. It does not accept or persist NIP, e-mail, natural-person details or the
raw KRS response. It has no authentication, delivery, score or alert behaviour.

After starting the local stack, create or refresh a profile and request a
non-deliverable preview:

```bash
curl --request PUT http://localhost:8000/profiles/krs/<10-digit-krs> \
  --header 'content-type: application/json' \
  --data '{"monitoring_tags":["construction","transport"]}'

curl --request POST \
  http://localhost:8000/profiles/<profile-id>/matches:preview
```

The API reports only the shared analysis/profile tags as a reason. It is not a
statement that the act applies to the company; manual review is required.

## Repository documentation

- `docs/specs/` — approved feature specifications and acceptance criteria.
- `docs/adr/` — architecture decision records.
- `docs/case-study/` — selected, anonymised delivery evidence for the public
  portfolio case study; it is not application data.
