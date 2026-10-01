from __future__ import annotations

from pathlib import Path

import pytest

from indoor_detection.train import _load_config, _uses_class_scopes, build_parser


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


def test_v3_config_is_resolution_matched_and_preserves_safe_augmentations() -> None:
    config = _load_config(Path("configs/train_indoor_v3_416.yaml"))

    assert config["imgsz"] == 416
    assert config["epochs"] == 20
    assert config["patience"] == 8
    assert config["lr0"] == pytest.approx(0.0003)
    assert config["exist_ok"] is False
    assert config["name"] == "indoor_partial_joint_yolo26n_v3_416"
    assert config["model"].endswith("indoor_partial_joint_yolo26n_v2/weights/best.pt")
    for augmentation in ("mosaic", "mixup", "cutmix", "copy_paste"):
        assert config[augmentation] == 0.0
