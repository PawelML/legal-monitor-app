"""Offline evaluation of approved golden labels and analysis predictions."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from legal_monitor.analysis.taxonomy import TAGS_V1, TAXONOMY_VERSION

DEFAULT_LABELS = Path("evals/golden/v1/labels.jsonl")
DEFAULT_PREDICTIONS = Path("evals/golden/v1/predictions.jsonl")
DEFAULT_BASELINE = Path("evals/results/baseline-v1.json")


class GoldenLabel(BaseModel):
    """Human-reviewed expected classification for one public act."""

    model_config = ConfigDict(extra="forbid")

    act_eli: str = Field(min_length=1)
    business_relevant: bool
    tags: list[str]
    rationale: str = Field(min_length=5, max_length=1000)
    reviewed_by: str = Field(min_length=1)
    taxonomy_version: str = TAXONOMY_VERSION


class Prediction(BaseModel):
    """Minimal evaluated projection of a persisted analysis output."""

    model_config = ConfigDict(extra="forbid")

    act_eli: str = Field(min_length=1)
    business_relevant: bool
    tags: list[str]


@dataclass(frozen=True, slots=True)
class Metrics:
    """Metrics kept deliberately small and legible for the first golden set."""

    relevance_precision: float
    relevance_recall: float
    tag_micro_precision: float
    tag_micro_recall: float
    tag_macro_precision: float
    tag_macro_recall: float
    sample_count: int


def _read_jsonl[ModelT: BaseModel](path: Path, model: type[ModelT]) -> list[ModelT]:
    """Read a compact, versionable JSONL fixture with strict schema checks."""
    if not path.exists():
        return []
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


def calculate_metrics(
    labels: list[GoldenLabel], predictions: list[Prediction]
) -> Metrics:
    """Calculate relevance and tag precision/recall for aligned act IDs."""
    labels_by_eli = {label.act_eli: label for label in labels}
    predictions_by_eli = {prediction.act_eli: prediction for prediction in predictions}
    if len(labels_by_eli) != len(labels) or len(predictions_by_eli) != len(predictions):
        raise ValueError(
            "golden labels and predictions must have unique act_eli values"
        )
    if labels_by_eli.keys() != predictions_by_eli.keys():
        raise ValueError(
            "golden labels and predictions must cover identical act_eli values"
        )
    for label in labels:
        _validate_tags(label.tags)
    for prediction in predictions:
        _validate_tags(prediction.tags)

    relevance_true_positive = sum(
        label.business_relevant and predictions_by_eli[eli].business_relevant
        for eli, label in labels_by_eli.items()
    )
    relevance_predicted_positive = sum(
        prediction.business_relevant for prediction in predictions
    )
    relevance_actual_positive = sum(label.business_relevant for label in labels)

    predicted_tags = {
        (prediction.act_eli, tag)
        for prediction in predictions
        for tag in prediction.tags
    }
    expected_tags = {(label.act_eli, tag) for label in labels for tag in label.tags}
    tag_true_positive = len(predicted_tags.intersection(expected_tags))

    per_tag_precision: list[float] = []
    per_tag_recall: list[float] = []
    for tag in sorted(TAGS_V1):
        tag_predicted = {item for item in predicted_tags if item[1] == tag}
        tag_expected = {item for item in expected_tags if item[1] == tag}
        if tag_predicted or tag_expected:
            per_tag_precision.append(
                _safe_ratio(
                    len(tag_predicted.intersection(tag_expected)), len(tag_predicted)
                )
            )
            per_tag_recall.append(
                _safe_ratio(
                    len(tag_predicted.intersection(tag_expected)), len(tag_expected)
                )
            )

    return Metrics(
        relevance_precision=_safe_ratio(
            relevance_true_positive, relevance_predicted_positive
        ),
        relevance_recall=_safe_ratio(
            relevance_true_positive, relevance_actual_positive
        ),
        tag_micro_precision=_safe_ratio(tag_true_positive, len(predicted_tags)),
        tag_micro_recall=_safe_ratio(tag_true_positive, len(expected_tags)),
        tag_macro_precision=round(sum(per_tag_precision) / len(per_tag_precision), 4)
        if per_tag_precision
        else 0.0,
        tag_macro_recall=round(sum(per_tag_recall) / len(per_tag_recall), 4)
        if per_tag_recall
        else 0.0,
        sample_count=len(labels),
    )


def metric_diff(current: Metrics, baseline: Metrics | None) -> dict[str, float]:
    """Return a concise zero-based diff when a reviewed baseline exists."""
    current_values = asdict(current)
    baseline_values = asdict(baseline) if baseline else {}
    return {
        key: round(value - baseline_values.get(key, value), 4)
        for key, value in current_values.items()
        if key != "sample_count"
    }


def parse_args() -> argparse.Namespace:
    """Parse explicit paths so CI remains offline and non-mutating."""
    parser = argparse.ArgumentParser(description="Evaluate Phase 1 golden labels.")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument(
        "--write", type=Path, help="Write an intentional result JSON file."
    )
    return parser.parse_args()


def main() -> int:
    """Evaluate fixture-backed outputs without calling a network or LLM."""
    args = parse_args()
    labels = _read_jsonl(args.labels, GoldenLabel)
    predictions = _read_jsonl(args.predictions, Prediction)
    if not labels and not predictions:
        print("Eval pending: no human-reviewed golden set has been added yet.")
        return 0
    if labels and not predictions:
        print(
            "Eval pending: reviewed seed labels exist, but no complete matching "
            "prediction set has been added yet."
        )
        return 0
    metrics = calculate_metrics(labels, predictions)
    baseline: Metrics | None = None
    if args.baseline.exists():
        baseline = Metrics(
            **json.loads(args.baseline.read_text(encoding="utf-8"))["metrics"]
        )
    result = {"taxonomy_version": TAXONOMY_VERSION, "metrics": asdict(metrics)}
    result["diff_from_baseline"] = metric_diff(metrics, baseline)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
