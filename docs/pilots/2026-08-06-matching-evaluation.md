# Deterministic matching evaluation — 2026-08-06

## Status

**No-go for automatic matching or alerts.** This is a diagnostic baseline for
the current tag-overlap preview, not a legal determination.

## Method

The evaluation uses the committed 20-act Phase 1 analysis projection and four
fictional profiles: road-freight carrier, construction contractor, food
producer and tax-advisory firm. Each of the 80 profile/act pairs has a reviewed
expected-match label. A prediction is positive only where the stored analysis
is business-relevant and has at least one tag selected by the profile.

No database, network or model call is made by `make matching-eval`.

## Result

| Scope | Expected | Predicted | True positive | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| All profiles | 20 | 32 | 20 | 0.6250 | 1.0000 |
| Road freight | 6 | 7 | 6 | 0.8571 | 1.0000 |
| Construction | 3 | 7 | 3 | 0.4286 | 1.0000 |
| Food producer | 5 | 8 | 5 | 0.6250 | 1.0000 |
| Tax advisory | 6 | 10 | 6 | 0.6000 | 1.0000 |

The rule emits 12 unexpected matches. Its recall in this small fixture is high,
but precision is insufficient for an alerting workflow, especially for the
construction profile. The result is consistent with the Phase 1 model evidence:
incorrect broad tags and false business-relevance classifications propagate
into profile matching.

## Decision and follow-up

Keep matching as a review-only preview. Do not add a threshold or hide these
results. The next separately approved quality task should expand the underlying
Phase 1 set from 20 to 50 acts, then rerun this full matrix before considering
PKD inference, embeddings, NIP/CEIDG, accounts or delivery.
