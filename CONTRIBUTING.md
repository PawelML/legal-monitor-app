# Contributing

## Delivery principle

AI can assist with implementation, but a human remains accountable for product
scope, architecture, data handling and production release decisions. Work is
kept small, explicit and reviewable.

## Choose the smallest adequate process

| Change | Required evidence before implementation | Required checks |
| --- | --- | --- |
| Small bug fix or copy/UI change | Issue/task description, acceptance criterion | Relevant regression test, `make quality` |
| Feature or cross-cutting change | Approved spec in `docs/specs/` | Unit/integration tests, `make quality`; e2e when a user journey changes |
| Irreversible or high-risk decision | Spec plus ADR in `docs/adr/` | Full `make ci`, manual controlled-data test, explicit release approval |

High-risk includes external-data ingestion, LLM prompts/models and taxonomy,
matching thresholds, e-mail delivery, personal-data handling, dependencies and
database migrations.

## Change loop

1. Define the problem, scope, non-goals, acceptance criteria, risks and a
   proportionate budget in a task or spec.
2. Add or update positive, edge-case and regression tests before implementation.
3. Give an AI agent only the approved scope and relevant repository context.
4. Verify external APIs, domain rules and security-sensitive assumptions rather
   than trusting generated code.
5. Run `make ci` before requesting review.
6. Review the diff against the checklist below. A human approves high-risk
   changes and production e-mail sends.

## Review checklist

- Does the change meet the stated acceptance criteria and preserve non-goals?
- Are success, edge and regression paths tested at the right level?
- Are external API assumptions backed by a contract test, fixture or source?
- Are personal data, secrets and user-facing legal claims handled safely?
- Are jobs idempotent, observable and safe to retry where applicable?
- Are migrations, dependencies and operational consequences explicit?
- Is the diff small enough to understand and free of unrelated refactors?

## Documentation templates

Copy [the feature-spec template](docs/specs/_template.md) for a feature or
cross-cutting change. Copy [the ADR template](docs/adr/0000-template.md) when a
decision is expensive or difficult to reverse.

## Agent delivery evidence

For a few representative changes, record the model/tool, scoped context,
estimated token cost, human time, iterations, review findings and outcome in
[`docs/case-study/agent-work-log.md`](docs/case-study/agent-work-log.md).
Never record secrets, personal data or full private prompts.
