"""Evaluate the frozen candidate once, without selecting thresholds on test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import traceback
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from indoor_detection.error_analysis import _summarize, analyze_errors
from indoor_detection.evaluate import _json_value, _per_class_metrics
from indoor_detection.partial_label_training import SquareClassScopedDetectionValidator
from indoor_detection.test_protocol import test_quality_decision


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def verify(protocol: dict[str, Any]) -> None:
    for path, digest in protocol["bindings"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Frozen binding changed: {path}")


def source_summaries(report: dict[str, Any]) -> dict[str, Any]:
    grouped = defaultdict(list)
    for row in report["records"]:
        parts = Path(row["image_path"]).parts
        index = max(i for i, part in enumerate(parts) if part.lower() == "images")
        grouped[parts[index - 1]].append(row)
    summaries = {}
    for name, records in grouped.items():
        sizes = defaultdict(Counter)
        for row in records:
            for target in row["ground_truth"]:
                sizes[target["size_bucket"]]["fn" if target["missed"] else "tp"] += 1
        summaries[name] = _summarize(records, sizes)
    return summaries


def fingerprint(report: dict[str, Any]) -> list[Any]:
    return [
        (r["image_path"], r["width"], r["height"], [g["xyxy"] for g in r["ground_truth"]])
        for r in report["records"]
    ]


def run(path: Path) -> None:
    protocol = json.loads(path.read_text())
    verify(protocol)
    root = Path(protocol["test_root"])
    root.mkdir(exist_ok=False)
    status = {
        "status": "IN_PROGRESS",
        "pid": os.getpid(),
        "completed": [],
        "started_at": datetime.now(UTC).isoformat(),
        "protocol_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    write(root / "execution-status.json", status)
    try:
        candidate = protocol["candidate"]
        metrics = YOLO(candidate["model"]).val(
            data=protocol["data"],
            split="test",
            imgsz=768,
            rect=False,
            batch=20,
            workers=0,
            device="0",
            conf=0.001,
            max_det=100,
            validator=SquareClassScopedDetectionValidator,
            plots=True,
            project=str(root / "validation-runs"),
            name="locked-test",
            exist_ok=False,
        )
        write(
            root / "ap-metrics.json",
            {
                "per_class_metrics": _per_class_metrics(metrics),
                "metrics": _json_value(metrics.results_dict),
                "operating_points_selected": False,
                "note": "AP/default summary diagnostics; fixed-threshold matching decides gates",
            },
        )
        reports = {}
        for name in ("smoke", "fire", "person", "baseline-smoke"):
            baseline = name == "baseline-smoke"
            print("START", name, flush=True)
            report = analyze_errors(
                model_path=Path(protocol["baseline_model"] if baseline else candidate["model"]),
                data_path=Path(protocol["data"]),
                split="test",
                imgsz=768,
                device="0",
                batch=16,
                operating_confidence=(
                    protocol["baseline_threshold"] if baseline else candidate["thresholds"][name]
                ),
                class_name="smoke" if baseline else name,
                candidate_confidence=0.001,
                iou_threshold=0.5,
                max_det=100,
                gallery_size=12,
                output_dir=root / name,
            )
            reports[name] = report
            expected = protocol["preparation"]["test_counts"]["smoke" if baseline else name]
            overall = report["summary"]["overall"]
            if (
                len(report["records"]) != expected["images"]
                or overall["true_positives"] + overall["false_negatives"] != expected["targets"]
            ):
                raise ValueError("Test scope or target counts differ from readiness")
            status["completed"].append(name)
            write(root / "execution-status.json", status)
            print("DONE", name, overall, flush=True)
        if fingerprint(reports["smoke"]) != fingerprint(reports["baseline-smoke"]):
            raise ValueError("Regression image membership/ground truth mismatch")
        source = {name: source_summaries(report) for name, report in reports.items()}
        delta = {
            "all": reports["smoke"]["summary"]["overall"]["recall"]
            - reports["baseline-smoke"]["summary"]["overall"]["recall"]
        }
        for name, value in source["smoke"].items():
            delta[name] = (
                value["overall"]["recall"] - source["baseline-smoke"][name]["overall"]["recall"]
            )
        fixed = {name: reports[name]["summary"]["overall"] for name in ("smoke", "fire", "person")}
        gates = test_quality_decision(fixed, delta)
        verify(protocol)
        write(
            root / "summary.json",
            {
                "status": "COMPLETED",
                "fixed_threshold_metrics": fixed,
                "baseline_smoke": reports["baseline-smoke"]["summary"],
                "smoke_recall_delta": delta,
                "gates": gates,
                "quality_candidate_accepted": all(gates.values()),
                "sources": source,
                "prior_test_use": protocol["preparation"]["prior_test_use"],
                "thresholds_changed": False,
                "training_started": False,
                "export_authorized": False,
                "pi_verified": False,
            },
        )
        status.update(status="COMPLETED", exit_code=0)
    except BaseException as exc:
        status.update(status="FAILED", exit_code=1, error=str(exc))
        traceback.print_exc()
        raise
    finally:
        status["finished_at"] = datetime.now(UTC).isoformat()
        write(root / "execution-status.json", status)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    run(parser.parse_args().protocol)


if __name__ == "__main__":
    main()
