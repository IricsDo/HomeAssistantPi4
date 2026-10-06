"""Read training labels and cached validation predictions; never open test."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from indoor_detection.error_analysis import (
    Detection,
    _filter_images_for_class_scope,
    _load_ground_truth,
    _resolve_dataset_split,
    _summarize,
)
from indoor_detection.fire_diagnostics import fire_box_geometry
from indoor_detection.threshold_calibration import calibrate_exact_recall

ROOT = Path("E:/HomeAssistantPi4/reports/indoor-v6-fire-diagnosis-v1")
CAL = Path("E:/HomeAssistantPi4/reports/indoor-v6-768-exact-hazard-calibration-v2")
DATA = Path("E:/HomeAssistantPi4/processed/indoor-partial-joint-v4/dataset.yaml")


def source(path: Path) -> str:
    i = max(i for i, p in enumerate(path.parts) if p.lower() == "images")
    return path.parts[i - 1]


def main() -> None:
    ROOT.mkdir(exist_ok=False)
    manifest = json.loads((CAL / "artifact-manifest.json").read_text())
    for entry in manifest["files"]:
        assert hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    paths = [CAL / "fire/candidates/error-analysis.json",
             CAL / "fire/confirmation/error-analysis.json", DATA, DATA.parent / "train.txt",
             DATA.parent / "val.txt", DATA.parent / "class_scope_manifest.json",
             CAL / "artifact-manifest.json", Path(__file__),
             Path("projects/indoor-detection/src/indoor_detection/fire_diagnostics.py"),
             Path("projects/indoor-detection/src/indoor_detection/threshold_calibration.py")]
    bindings = {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    protocol = {"owner": "OpenAI Codex", "status": "FROZEN_BEFORE_DIAGNOSIS",
                "bindings": bindings, "splits": ["train", "val"],
                "validation_recall_probes": [.90, .92, .95],
                "role": "diagnostic tradeoffs only, not new operating-point selection",
                "training": False, "test_inference": False, "export": False}
    (ROOT / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    candidates = json.loads(paths[0].read_text())
    confirmation = json.loads(paths[1].read_text())
    assert candidates["split"] == confirmation["split"] == "val"
    train = _filter_images_for_class_scope(DATA, _resolve_dataset_split(DATA, "train"), 1)[0]
    census = defaultdict(Counter)
    for path in train:
        with Image.open(path) as image:
            width, height = image.size
        boxes = _load_ground_truth(path, width, height, 1)
        row = census[source(path)]
        row["images"] += 1
        row["negative_images"] += not boxes
        row.update(fire_box_geometry(boxes, width, height))
    groups = defaultdict(list)
    for row in candidates["records"]:
        groups[source(Path(row["image_path"]))].append(row)
    probes = {}
    for group, records in {"all": candidates["records"], **groups}.items():
        probes[group] = {}
        for target in protocol["validation_recall_probes"]:
            report = {**candidates, "records": records}
            result = calibrate_exact_recall(report, target_recall=target,
                                            reference_threshold=.42607951164245605)
            probes[group][str(target)] = result["selected"]
    slices = defaultdict(list)
    geometry = defaultdict(Counter)
    for row in confirmation["records"]:
        group = source(Path(row["image_path"]))
        boxes = [Detection(tuple(g["xyxy"])) for g in row["ground_truth"]]
        geometry[group].update(fire_box_geometry(boxes, row["width"], row["height"]))
        for dimension in ("brightness_bucket", "sharpness_bucket"):
            slices[f"{group}/{dimension}/{row[dimension]}"].append(row)
    summaries = {group: _summarize(records, {}) for group, records in slices.items()}
    output = {"status": "COMPLETED", "train_annotation_census": dict(census),
              "validation_annotation_geometry": dict(geometry),
              "validation_threshold_tradeoffs": probes, "validation_conditions": summaries,
              "validation_current_summary": confirmation["summary"],
              "test_used": False, "labels_changed": False, "new_candidate_selected": False}
    for path, digest in bindings.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    (ROOT / "diagnosis.json").write_text(json.dumps(output, indent=2) + "\n")
    files = list(ROOT.iterdir())
    (ROOT / "artifact-manifest.json").write_text(json.dumps({"files": [
        {"path": p.as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in files]}, indent=2) + "\n")
    print(json.dumps({k: output[k] for k in (
        "train_annotation_census", "validation_annotation_geometry",
        "validation_threshold_tradeoffs")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
