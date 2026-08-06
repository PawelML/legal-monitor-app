# GPT-5.6 Luna balanced evaluation expansion — 2026-08-06

## Status

**No-go for a default analyser, automatic matching, or user alerts.** The
expanded source-reviewed set exposes a material false-alert rate. The result is
evaluation evidence, not legal advice or a legal review.

## Set and method

This run extends the approved ten-act v2 set to 20 official DU acts. The 20
labels contain 13 business-relevant and 7 non-business candidates. The added
negative cases cover a consolidated-text announcement, military uniforms and
pay, a local election, an interstate treaty, and municipal boundary changes.

Each prediction comes from a persisted `gpt-5.6-luna` low-reasoning v2
analysis. The model selected source chunk IDs; the application materialised the
stored quotations from the official extracted PDF. Ten new calls succeeded; one
initial call for DU/2026/1046 failed safely on an unknown chunk reference and
was retried unchanged successfully. No invalid analysis was persisted.

## Offline result

| Metric | Result |
| --- | ---: |
| Sample count | 20 |
| Relevance precision | 0.6842 |
| Relevance recall | 1.0000 |
| Tag micro-precision | 0.5000 |
| Tag micro-recall | 0.9286 |
| Tag macro-precision | 0.4848 |
| Tag macro-recall | 0.6061 |

The model marked five added negative candidates as business-relevant:
DU/2026/103 (consolidated-text announcement), 116 (military uniforms), 172
(local election), 212 (military pay), and 1023 (municipal boundaries). It
correctly rejected DU/2026/189 (treaty). It also substituted `finance_reporting`
for the approved `taxes_vat` tag on DU/2026/239. These are model-output
findings; they do not cause a prompt, taxonomy or threshold change.

## Operational evidence

The ten successful additional calls used 79,557 input and 4,725 output tokens,
with 57.4 s recorded total latency (5.7 s average). The safely rejected first
DU/2026/1046 attempt used 5,422 input and 699 output tokens with 5.1 s latency.
Token figures are operational telemetry, not a pricing statement.

## Decision and next action

Retain deterministic evidence v2 and the explicit analysis gate. Do not enable
automatic alerting or matching. A future, separately approved experiment should
focus on relevance conservatism and taxonomy selection against a larger,
source-reviewed set; it must define acceptance thresholds before any model or
prompt change.
