"""Train the smoke-only Ultralytics model from a versioned YAML config."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a smoke-only YOLO model")
    parser.add_argument("--config", default="configs/train.yaml")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--device", help="Override training device, for example 0 or cpu")
    return parser


def _load_config(path: Path) -> dict[str, Any]:
    import yaml

    if not path.is_file():
        raise FileNotFoundError(f"Training config not found: {path}")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Training config must be a YAML mapping")
    return config


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config).resolve()
    options = _load_config(config_path)
    model_name = str(options.pop("model", "yolo26n.pt"))
    options.pop("task", None)
    options.pop("mode", None)

    project_root = config_path.parent.parent
    data_path = Path(str(options.get("data", "configs/dataset.yaml")))
    if not data_path.is_absolute():
        options["data"] = str((project_root / data_path).resolve())
    project_path = Path(str(options.get("project", "runs/detect")))
    if not project_path.is_absolute():
        options["project"] = str((project_root / project_path).resolve())
    if args.device is not None:
        options["device"] = args.device
    if args.resume:
        options["resume"] = True

    from ultralytics import YOLO

    model = YOLO(model_name)
    model.train(**options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
