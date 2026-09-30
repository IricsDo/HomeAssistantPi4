from __future__ import annotations

import pytest

from indoor_detection.train import _uses_class_scopes, build_parser


def test_train_parser_accepts_phase3_overrides() -> None:
    args = build_parser().parse_args(
        [
            "--model",
            "yolo26n.pt",
            "--project",
            "E:/runs",
            "--name",
            "sanity",
            "--epochs",
            "2",
            "--fraction",
            "0.05",
        ]
    )

    assert args.model == "yolo26n.pt"
    assert args.project == "E:/runs"
    assert args.name == "sanity"
    assert args.epochs == 2
    assert args.fraction == pytest.approx(0.05)


def test_detects_class_scope_manifest_in_dataset_yaml(tmp_path) -> None:
    dataset = tmp_path / "dataset.yaml"
    dataset.write_text("class_scope_manifest: scopes.json\n", encoding="utf-8")

    assert _uses_class_scopes(dataset)
