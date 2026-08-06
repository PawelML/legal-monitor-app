# PrawoRadar

Early-warning monitoring of Polish legal changes for businesses. The product
explains what changed, who may be affected and when it takes effect. It is a
monitoring service, not legal advice.

## Status

Phase 0 (ELI metadata ingestion) is implemented. Phase 1 has the extraction,
validated-analysis and offline-evaluation foundations; its real-model pilot and
human-reviewed golden set remain in progress.

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

## Repository documentation

- `docs/specs/` — approved feature specifications and acceptance criteria.
- `docs/adr/` — architecture decision records.
- `docs/case-study/` — selected, anonymised delivery evidence for the public
  portfolio case study; it is not application data.
