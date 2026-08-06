"""Offline evaluation of deterministic profile-to-act tag matching."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from legal_monitor.analysis.taxonomy import TAGS_V1, TAXONOMY_VERSION
from legal_monitor.evals.run import Prediction

DEFAULT_PROFILES = Path("evals/matching/v1/profiles.jsonl")
DEFAULT_LABELS = Path("evals/matching/v1/labels.jsonl")
DEFAULT_PREDICTIONS = Path("evals/golden/v1/predictions.jsonl")


class MatchProfile(BaseModel):
    """One fictional company profile used only for offline evaluation."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=5, max_length=1000)
    monitoring_tags: list[str]


class MatchLabel(BaseModel):
    """One reviewed expected match for a profile and a legal act."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(min_length=1)
    act_eli: str = Field(min_length=1)
    expected_match: bool
    rationale: str = Field(min_length=5, max_length=1000)
    reviewed_by: str = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class MatchMetrics:
    """Legible binary-match metrics for a bounded fixed profile set."""

    precision: float
    recall: float
    true_positive_count: int
    predicted_match_count: int
    expected_match_count: int
    sample_count: int


def _read_jsonl[ModelT: BaseModel](path: Path, model: type[ModelT]) -> list[ModelT]:
    """Read strict, committed JSONL fixtures."""
    return [
        model.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _validate_tags(tags: list[str]) -> None:
    unknown_tags = set(tags).difference(TAGS_V1)
    if unknown_tags:
        raise ValueError(f"unknown taxonomy tags: {sorted(unknown_tags)}")


def predicted_matches(
    profiles: list[MatchProfile], predictions: list[Prediction]
) -> dict[tuple[str, str], bool]:
    """Apply exactly the preview service's relevance-plus-tag-overlap rule."""
    for profile in profiles:
        _validate_tags(profile.monitoring_tags)
    for prediction in predictions:
        _validate_tags(prediction.tags)
    return {
        (profile.profile_id, prediction.act_eli): (
            prediction.business_relevant
            and bool(set(profile.monitoring_tags).intersection(prediction.tags))
        )
        for profile in profiles
        for prediction in predictions
    }


def calculate_metrics(
    profiles: list[MatchProfile],
    predictions: list[Prediction],
    labels: list[MatchLabel],
) -> tuple[MatchMetrics, dict[str, MatchMetrics]]:
    """Validate the full matrix, then calculate aggregate and profile results."""
    profiles_by_id = {profile.profile_id: profile for profile in profiles}
    predictions_by_eli = {prediction.act_eli: prediction for prediction in predictions}
    label_pairs = {(label.profile_id, label.act_eli) for label in labels}
    if len(profiles_by_id) != len(profiles):
        raise ValueError("matching profiles must have unique profile_id values")
    if len(predictions_by_eli) != len(predictions):
        raise ValueError("matching predictions must have unique act_eli values")
    if len(label_pairs) != len(labels):
        raise ValueError("matching labels must have unique profile/act pairs")
    expected_pairs = {
        (profile.profile_id, prediction.act_eli)
        for profile in profiles
        for prediction in predictions
    }
    if label_pairs != expected_pairs:
        raise ValueError("matching labels must cover every profile/act pair")
    if any(label.profile_id not in profiles_by_id for label in labels):
        raise ValueError("matching label references an unknown profile")
    predicted_by_pair = predicted_matches(profiles, predictions)
    labels_by_pair = {(label.profile_id, label.act_eli): label for label in labels}
    aggregate = _metrics_for_pairs(predicted_by_pair, labels_by_pair, expected_pairs)
    per_profile = {
        profile.profile_id: _metrics_for_pairs(
            predicted_by_pair,
            labels_by_pair,
            {(profile.profile_id, prediction.act_eli) for prediction in predictions},
        )
        for profile in profiles
    }
    return aggregate, per_profile


def _metrics_for_pairs(
    predicted_by_pair: dict[tuple[str, str], bool],
    labels_by_pair: dict[tuple[str, str], MatchLabel],
    pairs: set[tuple[str, str]],
) -> MatchMetrics:
    """Calculate metrics for a complete known set of profile/act pairs."""
    true_positive_count = sum(
        predicted_by_pair[pair] and labels_by_pair[pair].expected_match
        for pair in pairs
    )
    predicted_match_count = sum(predicted_by_pair[pair] for pair in pairs)
    expected_match_count = sum(labels_by_pair[pair].expected_match for pair in pairs)
    return MatchMetrics(
        precision=_safe_ratio(true_positive_count, predicted_match_count),
        recall=_safe_ratio(true_positive_count, expected_match_count),
        true_positive_count=true_positive_count,
        predicted_match_count=predicted_match_count,
        expected_match_count=expected_match_count,
        sample_count=len(pairs),
    )


def parse_args() -> argparse.Namespace:
    """Parse explicit fixture paths for offline, reproducible evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate deterministic matching.")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--write", type=Path, help="Write an intentional result JSON.")
    return parser.parse_args()


def main() -> int:
    """Run an offline matching evaluation over committed fixtures only."""
    args = parse_args()
    profiles = _read_jsonl(args.profiles, MatchProfile)
    predictions = _read_jsonl(args.predictions, Prediction)
    labels = _read_jsonl(args.labels, MatchLabel)
    aggregate, per_profile = calculate_metrics(profiles, predictions, labels)
    result = {
        "taxonomy_version": TAXONOMY_VERSION,
        "metrics": asdict(aggregate),
        "per_profile": {key: asdict(value) for key, value in per_profile.items()},
    }
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
