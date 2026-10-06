"""Run one frozen v6 hazard calibration; large outputs belong on E:."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from indoor_detection.error_analysis import analyze_errors
from indoor_detection.threshold_calibration import calibrate_exact_recall


def sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def fingerprint(report: dict[str, Any]) -> list[Any]:
    return [(r["image_path"], r["width"], r["height"],
             [g["xyxy"] for g in r["ground_truth"]]) for r in report["records"]]


def verify_bindings(protocol: dict[str, Any]) -> None:
    for path, digest in protocol["bindings"].items():
        if sha(path) != digest:
            raise ValueError(f"Frozen binding changed: {path}")
    manifest = json.loads(Path(protocol["comparison_manifest"]).read_text())
    for entry in manifest["files"]:
        if sha(entry["path"]) != entry["sha256"]:
            raise ValueError(f"Comparison artifact changed: {entry['path']}")
    preparation = json.loads(Path(protocol["preparation_manifest"]).read_text())
    for entry in preparation["files"]:
        if sha(entry["path"]) != entry["sha256"]:
            raise ValueError(f"Preparation artifact changed: {entry['path']}")


def run(protocol_path: Path, root: Path) -> None:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    root.mkdir(parents=True, exist_ok=True)
    status = {"status": "IN_PROGRESS", "pid": os.getpid(),
              "started_at": datetime.now(UTC).isoformat(),
              "protocol_sha256": sha(protocol_path), "completed": []}
    with (root / "execution-status.json").open("x", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2)
    try:
        verify_bindings(protocol)
        rows = {}
        for name in ("smoke", "fire"):
            folder = root / name
            folder.mkdir(exist_ok=False)
            reference = json.loads(Path(protocol["references"][name]).read_text())
            threshold = reference["settings"]["operating_confidence"]
            args = dict(model_path=Path(protocol["model"]), data_path=Path(protocol["data"]),
                        split="val", imgsz=768, device="0", batch=16,
                        class_name=name, candidate_confidence=.001, iou_threshold=.5,
                        max_det=100)
            cached = protocol.get("candidate_sources", {}).get(name)
            if cached:
                print("REUSE frozen candidate extraction", name, cached, flush=True)
                candidates = json.loads(Path(cached).read_text())
            else:
                print("START candidate extraction", name, flush=True)
                candidates = analyze_errors(**args, operating_confidence=.001,
                                            gallery_size=0, output_dir=folder / "candidates")
            if (candidates["settings"]["imgsz"] != 768
                    or candidates["settings"]["max_det"] != 100
                    or candidates["class_name"] != name):
                raise ValueError("Candidate protocol mismatch")
            if fingerprint(candidates) != fingerprint(reference):
                raise ValueError("Reference image membership/ground truth drift")
            curve = calibrate_exact_recall(candidates, reference_threshold=threshold)
            old = reference["summary"]["overall"]
            if any(curve["reference"][k] != old[k]
                   for k in ("true_positives", "false_positives", "false_negatives")):
                raise ValueError("Fresh candidates fail to reproduce original operating counts")
            old_negative = reference["summary"]["false_alarm_breakdown"]
            if (curve["reference"]["negative_images_with_predictions"]
                    != old_negative["negative_images_with_predictions"]):
                raise ValueError("Reference negative alarms not reproduced")
            write(folder / "calibration-curve.json", curve)
            point = curve["selected"]
            if point is None:
                raise ValueError(f"{name} target recall unattainable at candidate floor")
            print("CONFIRM", name, point, flush=True)
            confirmation = analyze_errors(**args, operating_confidence=point["threshold"],
                                          gallery_size=12, output_dir=folder / "confirmation")
            if fingerprint(confirmation) != fingerprint(candidates):
                raise ValueError("Confirmation image membership/ground truth drift")
            actual = confirmation["summary"]["overall"]
            if any(actual[k] != point[k]
                   for k in ("true_positives", "false_positives", "false_negatives")):
                raise ValueError("Independent prediction confirmation differs from curve")
            negative = confirmation["summary"]["false_alarm_breakdown"]
            if (negative["negative_images_with_predictions"]
                    != point["negative_images_with_predictions"]):
                raise ValueError("Confirmation negative alarms differ from curve")
            reference_point = curve["reference"]
            delta_precision = point["precision"] - reference_point["precision"]
            delta_alarm = (point["negative_image_false_alarm_rate"]
                           - reference_point["negative_image_false_alarm_rate"])
            within_guardrails = (delta_precision >= -protocol["max_precision_drop"]
                                 and delta_alarm <= protocol["max_negative_rate_increase"])
            rows[name] = {"selected": point, "reference": reference_point,
                          "delta_precision": delta_precision,
                          "delta_negative_image_alarm_rate": delta_alarm,
                          "intervention_guardrails_passed": within_guardrails,
                          "confirmation": confirmation["summary"]}
            write(folder / "result.json", rows[name])
            status["completed"].append(name)
            write(root / "execution-status.json", status)
            if not within_guardrails:
                raise ValueError(f"{name} calibration exceeds frozen intervention guardrails")
        verify_bindings(protocol)
        person = json.loads(Path(protocol["person_result"]).read_text())["classes"]["person"]
        write(root / "summary.json", {
            "status": "COMPLETED", "protocol_sha256": sha(protocol_path),
            "classes": rows, "person_unchanged": person,
            "validation_quality_passed": person["gate_passed"]
            and all(r["selected"]["recall"] >= .9 for r in rows.values()),
            "test_opened": False, "training_started": False, "export_authorized": False,
            "deployment_resolution_locked": False,
            "calibration_protocol": "empirical square matching, not interpolated validator",
        })
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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.protocol, args.output)


if __name__ == "__main__":
    main()
