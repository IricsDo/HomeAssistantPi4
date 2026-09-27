"""Repeatable single-image latency and memory benchmark."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark a smoke model artifact")
    parser.add_argument("--model", required=True)
    parser.add_argument("--source", required=True, help="Representative input image")
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--confidence", type=float, default=0.20)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--device")
    parser.add_argument("--output", help="Optional benchmark JSON file")
    return parser


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    model_path = Path(args.model)
    source_path = Path(args.source)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Benchmark image not found: {source_path}")
    if args.iterations < 1 or args.warmup < 0:
        raise ValueError("iterations must be positive and warmup must be non-negative")

    import psutil
    from ultralytics import YOLO

    model = YOLO(str(model_path))
    options = {
        "source": str(source_path),
        "imgsz": args.imgsz,
        "conf": args.confidence,
        "verbose": False,
    }
    if args.device is not None:
        options["device"] = args.device

    for _ in range(args.warmup):
        model.predict(**options)

    process = psutil.Process(os.getpid())
    rss_before = process.memory_info().rss
    latencies_ms: list[float] = []
    for _ in range(args.iterations):
        start = time.perf_counter()
        model.predict(**options)
        latencies_ms.append((time.perf_counter() - start) * 1000.0)
    rss_after = process.memory_info().rss

    mean_latency = statistics.fmean(latencies_ms)
    report = {
        "model": str(model_path),
        "source": str(source_path),
        "image_size": args.imgsz,
        "warmup_iterations": args.warmup,
        "measured_iterations": args.iterations,
        "latency_ms_mean": round(mean_latency, 3),
        "latency_ms_p50": round(statistics.median(latencies_ms), 3),
        "latency_ms_p95": round(percentile(latencies_ms, 0.95), 3),
        "fps_from_mean": round(1000.0 / mean_latency, 3),
        "rss_before_mb": round(rss_before / (1024 * 1024), 3),
        "rss_after_mb": round(rss_after / (1024 * 1024), 3),
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{rendered}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
