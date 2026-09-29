"""Export a trained indoor detector for edge inference."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a trained indoor detector")
    parser.add_argument("--model", required=True, help="Path to best.pt")
    parser.add_argument("--format", choices=("ncnn", "onnx"), default="ncnn")
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--simplify", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    model_path = Path(args.model)
    if not model_path.is_file():
        raise FileNotFoundError(f"Training checkpoint not found: {model_path}")

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    exported_path = model.export(
        format=args.format,
        imgsz=args.imgsz,
        batch=1,
        device=args.device,
        simplify=args.simplify,
    )
    print(exported_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
