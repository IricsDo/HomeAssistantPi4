"""Train an Ultralytics indoor detector from a versioned YAML config."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a smoke/fire/person YOLO model")
    parser.add_argument("--config", default="configs/train_indoor_v1.yaml")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--device", help="Override training device, for example 0 or cpu")
    parser.add_argument("--data", help="Override dataset YAML (useful for data on another drive)")
    parser.add_argument("--model", help="Override pretrained model or model YAML")
    parser.add_argument("--project", help="Override output project directory")
    parser.add_argument("--name", help="Override run name")
    parser.add_argument("--epochs", type=int, help="Override number of epochs")
    parser.add_argument("--fraction", type=float, help="Fraction of training data to use")
    return parser


def _load_config(path: Path) -> dict[str, Any]:
    import yaml

    if not path.is_file():
        raise FileNotFoundError(f"Training config not found: {path}")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Training config must be a YAML mapping")
    return config


def _uses_class_scopes(data_path: Path) -> bool:
    """Return whether a dataset opts into partial-label class masking."""
    import yaml

    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset config not found: {data_path}")
    data = yaml.safe_load(data_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Dataset config must be a YAML mapping")
    return bool(data.get("class_scope_manifest"))


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
    if args.data is not None:
        options["data"] = str(Path(args.data).resolve())
    if args.model is not None:
        model_name = args.model
    if args.project is not None:
        options["project"] = str(Path(args.project).resolve())
    if args.name is not None:
        options["name"] = args.name
    if args.epochs is not None:
        options["epochs"] = args.epochs
    if args.fraction is not None:
        if not 0 < args.fraction <= 1:
            raise ValueError("--fraction must be in the interval (0, 1]")
        options["fraction"] = args.fraction
    if args.resume:
        options["resume"] = True

    from ultralytics import YOLO

    model = YOLO(model_name)
    data_config = Path(str(options["data"]))
    if _uses_class_scopes(data_config):
        from indoor_detection.partial_label_training import ClassScopedDetectionTrainer

        model.train(trainer=ClassScopedDetectionTrainer, **options)
    else:
        model.train(**options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
