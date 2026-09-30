"""Download a public Roboflow dataset without exposing the API key in logs."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def _load_api_key(env_file: Path) -> str:
    existing = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if existing:
        return existing
    if not env_file.is_file():
        raise FileNotFoundError(f"Environment file not found: {env_file}")
    for raw_line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "ROBOFLOW_API_KEY":
            key = value.strip().strip("'\"")
            if key:
                return key
    raise ValueError("ROBOFLOW_API_KEY is missing or empty")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download a Roboflow dataset version")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--format", default="yolov8")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {args.output_dir}")

    api_key = _load_api_key(args.env_file)
    try:
        from roboflow import Roboflow

        roboflow = Roboflow(api_key=api_key)
        project = roboflow.workspace(args.workspace).project(args.project)
        project.version(args.version).download(
            args.format,
            location=str(args.output_dir),
            overwrite=False,
        )
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        message = str(exc).replace(api_key, "***")
        message = re.sub(r"(?i)(api_key=)[^&\s]+", r"\1***", message)
        summary = {
            "error_type": type(exc).__name__,
            "http_status": status,
            "message": message,
        }
        print(json.dumps(summary))
        return 1

    print(
        json.dumps(
            {
                # The SDK return type differs between roboflow package versions.
                # The requested output path and CLI arguments are the stable record.
                "location": str(args.output_dir.resolve()),
                "version": args.version,
                "format": args.format,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
