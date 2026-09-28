from __future__ import annotations

import pytest

from smoke_detection.train import build_parser


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
