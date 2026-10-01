from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from indoor_detection.evaluate import (
    _dataset_class_id,
    _dataset_uses_class_scopes,
    _json_value,
    _per_class_metrics,
    _select_operating_point,
    build_parser,
)


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
    assert args.batch == 24
    assert args.workers == 0
    assert args.class_name == "smoke"


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


def test_selects_operating_point_for_requested_class() -> None:
    curves = [
        (
            [0.0, 0.1, 0.2],
            [[0.2, 0.7, 0.9], [0.3, 0.6, 0.8]],
            "Confidence",
            "Precision",
        ),
        (
            [0.0, 0.1, 0.2],
            [[1.0, 0.92, 0.8], [0.95, 0.85, 0.7]],
            "Confidence",
            "Recall",
        ),
    ]

    point = _select_operating_point(curves, target_recall=0.8, class_index=1)

    assert point is not None
    assert point["threshold"] == 0.1
    assert point["precision"] == 0.6
    assert point["recall"] == 0.85


def test_dataset_class_id_supports_list_and_mapping_names(tmp_path: Path) -> None:
    list_yaml = tmp_path / "list.yaml"
    list_yaml.write_text("names: [smoke, fire, person]\n", encoding="utf-8")
    mapping_yaml = tmp_path / "mapping.yaml"
    mapping_yaml.write_text("names:\n  0: smoke\n  1: fire\n  2: person\n", encoding="utf-8")

    assert _dataset_class_id(list_yaml, "person") == 2
    assert _dataset_class_id(mapping_yaml, "fire") == 1


def test_detects_class_scoped_dataset(tmp_path: Path) -> None:
    scoped_yaml = tmp_path / "scoped.yaml"
    scoped_yaml.write_text(
        "names: [smoke, fire, person]\nclass_scope_manifest: scopes.json\n",
        encoding="utf-8",
    )
    complete_yaml = tmp_path / "complete.yaml"
    complete_yaml.write_text("names: [smoke, fire, person]\n", encoding="utf-8")

    assert _dataset_uses_class_scopes(scoped_yaml)
    assert not _dataset_uses_class_scopes(complete_yaml)


def test_per_class_metrics_uses_model_class_names() -> None:
    metrics = SimpleNamespace(
        names={0: "smoke", 1: "fire", 2: "person"},
        box=SimpleNamespace(
            p=[0.7, 0.8, 0.9],
            r=[0.6, 0.7, 0.8],
            ap50=[0.65, 0.75, 0.85],
            ap=[0.4, 0.5, 0.6],
        ),
    )

    assert _per_class_metrics(metrics) == {
        "smoke": {"precision": 0.7, "recall": 0.6, "map50": 0.65, "map50_95": 0.4},
        "fire": {"precision": 0.8, "recall": 0.7, "map50": 0.75, "map50_95": 0.5},
        "person": {"precision": 0.9, "recall": 0.8, "map50": 0.85, "map50_95": 0.6},
    }
