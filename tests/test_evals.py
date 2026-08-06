"""Regression tests for the deterministic Phase 1 metric calculations."""

from __future__ import annotations

import pytest

from legal_monitor.evals.run import GoldenLabel, Prediction, calculate_metrics


def label(eli: str, relevant: bool, tags: list[str]) -> GoldenLabel:
    """Build a concise human-reviewed golden label for a metric test."""
    return GoldenLabel(
        act_eli=eli,
        business_relevant=relevant,
        tags=tags,
        rationale="Ręcznie sprawdzona etykieta testowa.",
        reviewed_by="test",
    )


def test_metrics_report_relevance_and_micro_macro_tag_scores() -> None:
    metrics = calculate_metrics(
        [label("DU/2026/1", True, ["taxes_vat"]), label("MP/2026/1", False, [])],
        [
            Prediction(act_eli="DU/2026/1", business_relevant=True, tags=["taxes_vat"]),
            Prediction(act_eli="MP/2026/1", business_relevant=True, tags=[]),
        ],
    )

    assert metrics.relevance_precision == 0.5
    assert metrics.relevance_recall == 1.0
    assert metrics.tag_micro_precision == 1.0
    assert metrics.tag_macro_recall == 1.0


def test_metrics_reject_misaligned_or_unknown_taxonomy_records() -> None:
    with pytest.raises(ValueError, match="identical"):
        calculate_metrics([label("DU/2026/1", False, [])], [])
    with pytest.raises(ValueError, match="unknown"):
        calculate_metrics(
            [label("DU/2026/1", True, ["not_a_tag"])],
            [Prediction(act_eli="DU/2026/1", business_relevant=True, tags=[])],
        )
