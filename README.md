# PrawoRadar

Early-warning monitoring of Polish legal changes for businesses. The product
explains what changed, who may be affected and when it takes effect. It is a
monitoring service, not legal advice.

## Status

The repository is in **Phase -1: delivery contract**. Product implementation
starts in Phase 0; this phase establishes the specification, testing and review
standards used for every later change.

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

`make ci` is the local equivalent of the mandatory CI gates. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the delivery workflow and
[the plan](plans/legal-monitor-plan.md) for the product roadmap.

## Repository documentation

- `docs/specs/` — approved feature specifications and acceptance criteria.
- `docs/adr/` — architecture decision records.
- `docs/case-study/` — selected, anonymised delivery evidence for the public
  portfolio case study; it is not application data.
