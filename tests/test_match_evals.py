"""Regression tests for deterministic profile-to-act matching metrics."""

from __future__ import annotations

import pytest

from legal_monitor.evals.run import Prediction
from legal_monitor.match_evals.run import MatchLabel, MatchProfile, calculate_metrics


def profile(profile_id: str, tags: list[str]) -> MatchProfile:
    """Build a fictional profile for a compact metric test."""
    return MatchProfile(
        profile_id=profile_id,
        name="Profil testowy",
        description="Fikcyjny profil używany tylko do testu metryk.",
        monitoring_tags=tags,
    )


def label(profile_id: str, act_eli: str, expected_match: bool) -> MatchLabel:
    """Build a reviewed expected pair for a compact metric test."""
    return MatchLabel(
        profile_id=profile_id,
        act_eli=act_eli,
        expected_match=expected_match,
        rationale="Ręcznie sprawdzona relacja profil–akt.",
        reviewed_by="test",
    )


def test_matching_metrics_use_relevance_and_tag_intersection() -> None:
    """An irrelevant tagged act cannot match; results are available per profile."""
    profiles = [profile("transport", ["transport"]), profile("food", ["food"])]
    predictions = [
        Prediction(act_eli="DU/2026/1", business_relevant=True, tags=["transport"]),
        Prediction(act_eli="DU/2026/2", business_relevant=False, tags=["food"]),
    ]
    labels = [
        label("transport", "DU/2026/1", True),
        label("transport", "DU/2026/2", False),
        label("food", "DU/2026/1", False),
        label("food", "DU/2026/2", True),
    ]

    aggregate, per_profile = calculate_metrics(profiles, predictions, labels)

    assert aggregate.precision == 1.0
    assert aggregate.recall == 0.5
    assert aggregate.sample_count == 4
    assert per_profile["transport"].precision == 1.0
    assert per_profile["food"].recall == 0.0


def test_matching_metrics_reject_incomplete_or_duplicate_pair_matrix() -> None:
    """No partial profile evaluation may look like a complete quality result."""
    profiles = [profile("transport", ["transport"])]
    predictions = [Prediction(act_eli="DU/2026/1", business_relevant=True, tags=[])]

    with pytest.raises(ValueError, match="cover every"):
        calculate_metrics(profiles, predictions, [])
    with pytest.raises(ValueError, match="unique"):
        calculate_metrics(
            profiles,
            predictions,
            [label("transport", "DU/2026/1", False)] * 2,
        )
