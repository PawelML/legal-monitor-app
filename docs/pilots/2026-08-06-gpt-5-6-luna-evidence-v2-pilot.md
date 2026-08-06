# GPT-5.6 Luna evidence v2 pilot — 2026-08-06

## Status

**No-go for a default analyser or user alerts.** Evidence grounding is now
reliable at the persistence boundary, but this ten-act seed is too small and
contains a relevance false positive and excess tags. This is implementation and
evaluation evidence, not legal advice or a legal review.

## Configuration

- Provider/model: OpenAI `gpt-5.6-luna`
- API: Responses API with Structured Outputs and `store=false`
- Prompt: approved `pilot-v1` base instructions plus approved v2 evidence
  override; raw text remains only in the ignored runtime environment
- Reasoning: `low`
- Output schema: `v2`; model selects `p{page}-c{chunk}` source IDs and the
  application materialises the stored quotation from the official PDF text
- Sample: the same approved ten-act seed used by the v1 pilot

## Completion and operational comparison

| Measure | v1 | v2 |
| --- | ---: | ---: |
| Persisted analyses / attempts | 3 / 10 | 10 / 10 |
| Evidence quotation rejections | 7 | 0 |
| Recorded input tokens | incomplete (2 calls only) | 26,322 |
| Recorded output tokens | incomplete (2 calls only) | 4,563 |
| Recorded latency | incomplete (2 calls only) | 93.7 s total; 9.4 s average |

The v2 result demonstrates the intended protocol property: each persisted
quotation is exact, bounded source text selected by an ID the application
resolved. It does not establish that the selected fragment is sufficient for a
legal interpretation.

## Offline evaluation against the approved seed

`make eval` evaluates the committed v2 projections against the human-approved
labels. Results: 10 acts; relevance precision **0.9000**, recall **1.0000**;
tag micro-precision **0.6429**, micro-recall **1.0000**; tag macro-precision
**0.7188**, macro-recall **0.8750**.

The negative candidate `DU/2026/946` was predicted as business-relevant with
`construction` and `finance_reporting`, while its approved label is not
business-relevant with no tags. Extra tags also appeared for `DU/2026/25`,
`DU/2026/219`, and `DU/2026/293`. These are review findings; this pilot makes
no model, prompt, taxonomy, threshold, matching, or alerting change.

## Decision and next action

Keep v2 as the evidence protocol for further controlled pilots. Before any
default analyser or user-facing workflow is enabled, approve a broader,
balanced reviewed set (especially negative candidates), define acceptance
thresholds, and run a separately approved model/prompt evaluation.
