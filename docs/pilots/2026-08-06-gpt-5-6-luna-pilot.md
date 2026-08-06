# GPT-5.6 Luna Phase 1 pilot — 2026-08-06

## Status

**No-go for a default analyser.** The pilot is implementation evidence, not a
quality baseline or legal review. Human review of the successful outputs is
still required.

## Configuration

- Provider/model: OpenAI `gpt-5.6-luna`
- API: Responses API with Structured Outputs and `store=false`
- Prompt: approved `pilot-v1`; raw text remains only in the ignored runtime
  environment
- Reasoning: `low`
- Source: one extracted official ELI PDF per act, supplied with page markers
- Persistence gate: schema, taxonomy and page-grounded quotation validation

## Sample

The sample contains one deliberately non-business candidate plus nine acts
selected across employment, tax, transport, food, environment, reporting,
construction and energy:

| ELI | Area | Latest outcome |
| --- | --- | --- |
| DU/2026/946 | public administration / negative candidate | succeeded |
| DU/2026/25 | employment | failed: evidence quotation |
| DU/2026/414 | excise tax | succeeded |
| DU/2026/293 | goods transport / SENT | succeeded |
| DU/2026/371 | food | failed: evidence quotation |
| DU/2026/174 | packaging and waste | failed: evidence quotation |
| DU/2026/333 | accounting | failed: evidence quotation |
| DU/2026/226 | construction | failed: evidence quotation |
| DU/2026/219 | transport support | failed: evidence quotation |
| DU/2026/606 | energy-product conformity | failed: evidence quotation |

## Observations

- 3 of 10 latest attempts passed all persistence gates; 7 of 10 were rejected
  because the model did not return a quotation found on the cited PDF page.
- Initial attempts also exposed free-form taxonomy tags. The output schema now
  exposes the approved tags as an enum; two subsequent successes used only
  allowed tags.
- The two successful, instrumented live calls consumed 2,934 input and 988
  output tokens with a combined latency of 10.3 s. These figures are not a
  complete pilot-cost total: usage for the earlier rejected calls was not
  persisted. The implementation now records provider usage even when later
  grounding validation rejects a response.
- The successful excise-tax analysis selected `taxes_vat`, showing that the
  present taxonomy may be too coarse for tax subdomains. This is a human-review
  finding, not evidence to change the taxonomy yet.

## Decision and next actions

Do not enable `gpt-5.6-luna` as the default analyser or use it for matching or
user alerts. Keep the strict evidence gate enabled.

Before another paid pilot, a human should review the three successful outputs
and choose an approved remedy for unreliable quotations: a revised prompt,
page/chunk citation identifiers in a new output schema, or a model/effort
comparison. Any prompt, taxonomy or model change requires its own eval diff and
approval under the Phase 1 specification.
