# Phase 1: grounded act analysis and evaluation harness

Status: approved

Approval: 2026-07-16 — Pawelo

Baseline completion: 2026-08-08 — Pawelo approved the bounded source review
and unchanged-model run. `evals/golden/v1/` now contains the required 50-act
baseline and `evals/results/baseline-v1.json` is its reviewed metric record.
This establishes evaluation evidence only; it does not enable changes to the
model, prompt, taxonomy, matching, thresholds, alerts or delivery.

## Problem and outcome

ELI metadata alone cannot tell a business what a legal act changes or whether
it matters. PrawoRadar needs a repeatable, evidence-backed analysis of each
act, measured against human labels before it is ever used for matching or
email delivery.

The outcome is: a PDF-backed act can be extracted, analysed into a validated
Polish JSON record, reanalysed without losing history, and evaluated locally
against a reviewed golden set. The product remains an early-warning monitor,
not legal advice.

## Scope

- In scope:
  - Download text-only source material from official ELI PDFs; do not retain
    PDF files.
  - Local PDF text extraction with `pdfplumber`, per-page provenance, SHA-256
    of extracted text, status and safe error details.
  - Versioned `act_texts` and `act_analyses` persistence plus `job_runs` for
    extraction and analysis attempts. An analysis is tied to source-text hash,
    schema version, taxonomy version, prompt version and model identifier.
  - A Pydantic output contract: plain-language summary, business relevance,
    affected parties, tags, obligations, effective date, impact level (1–5)
    and short page-linked evidence quotations. No chain-of-thought is stored.
  - A versioned taxonomy v1: `taxes_vat`, `employment`, `payroll`, `health_and_safety`,
    `data_protection`, `ecommerce`, `food`, `transport`, `construction`,
    `environment`, `finance_reporting`, `consumer_protection`.
  - A provider boundary with a deterministic fake for tests; one real model is
    evaluated on a 10-act pilot before it becomes the configured analyser.
  - Golden set v1: at least 50 acts, selected across DU/MP, act types and
    business relevance. Each label records relevance, expected tags and a
    concise human rationale; source PDFs are not committed.
  - `make eval` producing committed, machine-readable results and a readable
    diff against the approved baseline.
- Out of scope:
  - OCR, sending PDFs directly to a model, embeddings, company profiles,
    matching, scheduler, web UI and email delivery.
  - Any automatic legal conclusion, enforcement action or user-facing alert.

## Constraints and assumptions

- The official ELI PDF is the authoritative text. Extraction failure is
  observable and retryable; it must never silently produce an empty analysis.
- PDF text is public, but API keys and raw production prompts are secrets and
  are supplied only through environment variables, never fixtures or Git.
- The first extractor targets digitally generated PDFs. Scanned/garbled PDFs
  are marked `failed` or `needs_review`; OCR is a separate later decision.
- The analysis provider and exact model are intentionally not selected by this
  spec. This avoids an irreversible cost/quality choice before pilot evidence.

## Design

An explicit CLI accepts one or more ELI identifiers, resolves an official PDF,
extracts text page by page and stores the result. The extraction command is
idempotent for unchanged source content. A separate analysis CLI consumes a
stored successful text record and writes a new immutable analysis version.
Neither command calls the other implicitly.

The analyser receives only the extracted text and a versioned prompt. Its JSON
response is parsed and validated before persistence. Every evidence quotation
must occur on the referenced extracted page; otherwise the analysis fails.
Tags must belong to taxonomy v1, impact must be 1–5, and a non-relevant act
cannot contain obligations or tags. Model failure, invalid JSON or failed
grounding creates a failed job record, not a partial analysis.

Golden labels and expected output are stored as compact JSON/JSONL fixtures
under `evals/golden/v1/`; PDFs and full extracted legal texts are excluded.
`make eval` uses a named analysis version, calculates relevance precision and
recall plus micro/macro tag precision and recall, and writes a timestamped
result to `evals/results/`. The first reviewed run establishes the baseline.

## Acceptance criteria

- [x] Migration creates the text and analysis version tables without changing
      Phase 0 ingest semantics.
- [ ] A fixture PDF extracts stable, non-empty page text; malformed and
      image-only fixtures produce explicit terminal statuses.
- [x] Re-running extraction for unchanged input produces no duplicate current
      text record; changed text is represented by a new hash/version.
- [x] Valid analysis JSON persists with provenance; invalid schema, unknown
      tag, invalid evidence and provider error persist no analysis and record
      failed jobs.
- [x] The deterministic analyser makes all automated tests offline and stable.
- [x] Golden set v1 contains at least 50 human-reviewed labels and no source
      PDF or secret.
- [x] `make eval` reports all stated metrics and a diff from its baseline.
- [ ] Before a real model becomes default, a 10-act pilot has a committed
      comparison report covering quality, failures, latency and estimated cost.
- [ ] Any later prompt, model or taxonomy change includes an eval diff and a
      dated human approval in its spec or decision record.

## Risks and human decisions

- PDF structure varies; a successful extraction does not establish legal
  correctness. Human review of golden labels and pilot outputs is mandatory.
- Recall is more important than precision for the future alerting product, but
  numeric release thresholds will be set only after the first labelled pilot;
  inventing targets before a baseline would be misleading.
- Pawelo must approve: the taxonomy wording, 10-act pilot review, selected
  provider/model and the first 50-act golden baseline. Selecting the real
  provider/model requires a short ADR with cost, data handling and quality
  comparison before enabling live calls.
- Prompt-injection-like text inside an act is treated as source material, not
  instructions. The system prompt must require structured analysis only.

## Test plan

- Unit: PDF normalisation, hashing, taxonomy and output/grounding validators.
- Integration: migrations, text/analysis versioning, idempotency and failed
  `job_runs` using a fake ELI text source and deterministic analyser.
- Contract: minimal PDF fixtures, golden JSONL schema and provider-response
  fixtures; no network or LLM call in CI.
- End-to-end/manual: extract and analyse the agreed 10 official pilot acts;
  review all output before model selection.
- Eval/regression: run the 50-act golden set locally for every prompt, model or
  taxonomy change; commit the result and review its diff.

## Delivery budget

Implement in bounded slices: extraction and validators first; offline analysis
and eval harness second; real-provider pilot only after the ADR approval. Keep
the context to this spec, Phase 0 interfaces, fixture data and the selected
provider's official documentation. Stop before OCR, matching or any
user-facing workflow.
