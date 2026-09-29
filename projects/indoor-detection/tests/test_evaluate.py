from __future__ import annotations

from indoor_detection.evaluate import _json_value, _select_operating_point, build_parser


class Scalar:
    def item(self) -> float:
        return 0.5


def test_json_value_converts_metric_scalars() -> None:
    assert _json_value({"metric": Scalar(), "speed": [Scalar()]}) == {
        "metric": 0.5,
        "speed": [0.5],
    }


def test_evaluate_parser_defaults_to_test_split() -> None:
    args = build_parser().parse_args(
        [
            "--model",
            "best.pt",
            "--data",
            "dataset.yaml",
            "--project",
            "runs",
            "--name",
            "test-eval",
            "--report",
            "report.json",
        ]
    )

    assert args.split == "test"
    assert args.imgsz == 640


def test_selects_highest_confidence_meeting_target_recall() -> None:
    curves = [
        ([0.0, 0.1, 0.2], [[0.2, 0.7, 0.9]], "Confidence", "Precision"),
        ([0.0, 0.1, 0.2], [[1.0, 0.92, 0.8]], "Confidence", "Recall"),
    ]

    point = _select_operating_point(curves, target_recall=0.9)

    assert point == {
        "threshold": 0.1,
        "precision": 0.7,
        "recall": 0.92,
        "target_recall": 0.9,
        "target_met": True,
    }


def test_reports_metrics_at_frozen_threshold() -> None:
    curves = [
        ([0.0, 0.1, 0.2], [[0.2, 0.7, 0.9]], "Confidence", "Precision"),
        ([0.0, 0.1, 0.2], [[1.0, 0.92, 0.8]], "Confidence", "Recall"),
    ]

    point = _select_operating_point(curves, threshold=0.19)

    assert point is not None
    assert point["threshold"] == 0.2
    assert point["precision"] == 0.9
    assert point["recall"] == 0.8
