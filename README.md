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

`make ci` is the local equivalent of the mandatory CI gates. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the delivery workflow and
[the plan](plans/legal-monitor-plan.md) for the product roadmap.

## Repository documentation

- `docs/specs/` — approved feature specifications and acceptance criteria.
- `docs/adr/` — architecture decision records.
- `docs/case-study/` — selected, anonymised delivery evidence for the public
  portfolio case study; it is not application data.
