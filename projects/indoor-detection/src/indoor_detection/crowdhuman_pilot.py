"""Acquire frozen CrowdHuman pilot images from pinned remote ZIP members."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import re
import shutil
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from indoor_detection.compose_dataset import _dhash, _hamming_distance
from indoor_detection.crowdhuman_assessment import _valid_box
from indoor_detection.dataset import DatasetValidationError, sha256_file

REVISION = "d97203da87e348ea69f7a7633a57c21a956120a6"
BASE = f"https://huggingface.co/datasets/sshao0516/CrowdHuman/resolve/{REVISION}"
MAX_READ = 8 * 1024 * 1024


class RangeReader(io.RawIOBase):
    """Bounded seekable HTTP reader; never accept a full-archive response."""

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.position = 0
        self.size = 0
        self.downloaded = 0
        self._fetch(0, 1, probe=True)

    def _fetch(self, start: int, count: int, *, probe: bool = False) -> bytes:
        end = start + count - 1
        request = urllib.request.Request(self.url, headers={
            "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"})
        with urllib.request.urlopen(request, timeout=60) as response:
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",
                                 response.headers.get("Content-Range", ""))
            if (response.status != 206 or match is None
                    or tuple(map(int, match.groups()[:2])) != (start, end)):
                raise DatasetValidationError("Server did not honor bounded HTTP Range")
            total = int(match.group(3))
            if not probe and total != self.size:
                raise DatasetValidationError("Remote archive size changed")
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise DatasetValidationError("Unexpected HTTP content encoding")
            data = response.read(count + 1)
            if len(data) != count:
                raise DatasetValidationError("Truncated or oversized Range response")
            if probe:
                self.size = total
                # Reuse the resolved URL, avoiding repeated redirect requests.
                # Signed URLs stay in memory and must not be logged or persisted.
                self.url = response.geturl()
            self.downloaded += len(data)
            return data

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        origin = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}
        if whence not in origin or origin[whence] + offset < 0:
            raise ValueError("Invalid seek")
        self.position = origin[whence] + offset
        return self.position

    def read(self, size: int = -1) -> bytes:
        count = max(0, self.size - self.position)
        if size >= 0:
            count = min(count, size)
        if count > MAX_READ:
            raise DatasetValidationError("Range read exceeds 8 MiB bound")
        if not count:
            return b""
        data = self._fetch(self.position, count)
        self.position += count
        return data


def load_pilot(plan_path: Path, annotations: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    ids = plan.get("image_ids", [])
    if (not ids or len(ids) != len(set(ids)) or len(ids) != plan.get("sample_size")
            or any(not isinstance(i, str) or not re.fullmatch(r"[\w,.-]+", i)
                   or i in (".", "..") for i in ids)):
        raise DatasetValidationError("Invalid pilot IDs")
    if sha256_file(annotations) != plan.get("annotation_sha256"):
        raise DatasetValidationError("Annotations do not match frozen pilot")
    selected = set(ids)
    rows = {}
    with annotations.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["ID"] in selected:
                if row["ID"] in rows:
                    raise DatasetValidationError("Duplicate pilot annotation")
                rows[row["ID"]] = row
    if set(rows) != selected:
        raise DatasetValidationError("Missing pilot annotations")
    for row in rows.values():
        if any(b["tag"] != "person" or b.get("extra", {}).get("ignore", 0)
               for b in row["gtboxes"]):
            raise DatasetValidationError("Pilot contains body-ignore regions")
    return plan, rows


def acquire(plan_path: Path, annotations: Path, output: Path) -> dict[str, Any]:
    """Write a fresh acquisition directory; incomplete directories are preserved."""
    plan, rows = load_pilot(plan_path, annotations)
    output.mkdir(parents=True, exist_ok=False)
    image_dir = output / "images"
    image_dir.mkdir()
    records = {}
    archives = []
    for part in range(1, 4):
        archive = f"CrowdHuman_train{part:02d}.zip"
        url = f"{BASE}/{archive}"
        with RangeReader(url) as remote, zipfile.ZipFile(remote) as source:
            entries = source.infolist()
            by_name = {}
            for entry in entries:
                # Only exact Images/<ID>.jpg or <ID>.jpg members are candidates.
                if entry.filename.startswith("Images/"):
                    name = entry.filename.removeprefix("Images/")
                else:
                    name = entry.filename
                if name in by_name:
                    raise DatasetValidationError("Duplicate ZIP image name")
                by_name[name] = entry
            for image_id in plan["image_ids"]:
                entry = by_name.get(f"{image_id}.jpg")
                if entry is None:
                    continue
                if image_id in records:
                    raise DatasetValidationError("Pilot image found in multiple archives")
                if entry.file_size > MAX_READ or entry.compress_size > MAX_READ:
                    raise DatasetValidationError("Image exceeds acquisition bound")
                data = source.read(entry)  # zipfile checks CRC before returning.
                image_path = image_dir / f"{image_id}.jpg"
                with image_path.open("xb") as stream:
                    stream.write(data)
                record = {"image_id": image_id, "archive": archive,
                          "member": entry.filename, "archive_size": remote.size,
                          "crc32": f"{entry.CRC:08x}", "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(),
                          "image_path": str(image_path.resolve()), "source_url": url}
                records[image_id] = record
                (output / f"receipt-{image_id}.json").write_text(
                    json.dumps(record, indent=2) + "\n", encoding="utf-8")
            archives.append({"archive": archive, "size": remote.size,
                             "downloaded_bytes": remote.downloaded})
            print(f"{archive}: {len(records)}/{len(rows)} images acquired", flush=True)
    if set(records) != set(rows):
        raise DatasetValidationError("Pilot image members missing from train archives")
    report = {"schema_version": 1, "revision": REVISION,
              "plan_sha256": sha256_file(plan_path),
              "annotation_sha256": plan["annotation_sha256"],
              "training_allowed": False, "status": "ACQUIRED_AWAITING_BOX_REVIEW",
              "archives": archives, "records": [records[i] for i in plan["image_ids"]]}
    (output / "acquisition.json").write_text(json.dumps(report, indent=2) + "\n",
                                            encoding="utf-8")
    (output / "pilot-annotations.json").write_text(
        json.dumps([rows[i] for i in plan["image_ids"]], indent=2) + "\n", encoding="utf-8")
    return report


def render_review(acquisition: Path, output: Path) -> dict[str, Any]:
    """Render both conventions without editing or approving source annotations."""
    report = json.loads((acquisition / "acquisition.json").read_text(encoding="utf-8"))
    rows = json.loads((acquisition / "pilot-annotations.json").read_text(encoding="utf-8"))
    by_id = {row["ID"]: row for row in rows}
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for number, receipt in enumerate(report["records"], 1):
        path = Path(receipt["image_path"])
        if sha256_file(path) != receipt["sha256"]:
            raise DatasetValidationError("Pilot image hash changed")
        with Image.open(path) as original:
            original.load()
            image = original.convert("RGB")
        width, height = image.size
        scale = min(1.0, 1000 / width, 900 / height)
        display = image.resize((round(width * scale), round(height * scale)))
        canvas = Image.new("RGB", (display.width * 2, display.height + 35), "white")
        geometry = {}
        boxes = by_id[receipt["image_id"]]["gtboxes"]
        for column, key in enumerate(("vbox", "fbox")):
            canvas.paste(display, (column * display.width, 35))
            draw = ImageDraw.Draw(canvas)
            draw.text((column * display.width + 5, 8),
                      f"{number:02d} {key} / {len(boxes)} persons", fill="black")
            outside = empty = 0
            for box_number, box in enumerate(boxes, 1):
                if not _valid_box(box.get(key)):
                    raise DatasetValidationError("Invalid pilot body geometry")
                x, y, w, h = box[key]
                outside += int(x < 0 or y < 0 or x + w > width or y + h > height)
                left, top = max(0, x), max(0, y)
                right, bottom = min(width, x + w), min(height, y + h)
                if right <= left or bottom <= top:
                    empty += 1
                    continue
                offset = column * display.width
                rectangle = (left * scale + offset, top * scale + 35,
                             right * scale + offset, bottom * scale + 35)
                draw.rectangle(rectangle, outline="lime" if column == 0 else "orange", width=2)
                draw.text(rectangle[:2], str(box_number), fill="red", stroke_width=1,
                          stroke_fill="white")
            geometry[key] = {"outside_image": outside, "empty_after_clipping": empty}
        overlay = output / f"{number:02d}.jpg"
        canvas.save(overlay, quality=90)
        records.append({"number": number, "image_id": receipt["image_id"],
                        "width": width, "height": height, "person_boxes": len(boxes),
                        "geometry": geometry, "overlay": str(overlay.resolve())})
    bundle = {"training_allowed": False, "status": "AWAITING_VISUAL_REVIEW",
              "acquisition_sha256": sha256_file(acquisition / "acquisition.json"),
              "annotations_sha256": sha256_file(acquisition / "pilot-annotations.json"),
              "display": "Left visible body; right inferred full body; clipped for display only",
              "records": records}
    (output / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return bundle


def audit_exact_overlap(acquisition: Path, registry: Path, output: Path) -> dict[str, Any]:
    """Compare raw file hashes only; no near-duplicate or annotation approval."""
    if output.exists():
        raise FileExistsError(output)
    pilot = json.loads((acquisition / "acquisition.json").read_text(encoding="utf-8"))
    corpus = json.loads(registry.read_text(encoding="utf-8"))
    hashes: dict[str, list[dict[str, Any]]] = {}
    for row in corpus["records"]:
        hashes.setdefault(row["sha256"], []).append(row)
    seen: dict[str, str] = {}
    internal = []
    overlap = []
    for row in pilot["records"]:
        digest = sha256_file(Path(row["image_path"]))
        if digest != row["sha256"]:
            raise DatasetValidationError("Pilot image hash changed")
        if digest in seen:
            internal.append([seen[digest], row["image_id"]])
        seen[digest] = row["image_id"]
        if digest in hashes:
            overlap.append({"image_id": row["image_id"], "sha256": digest,
                            "corpus_matches": hashes[digest]})
    report = {"training_allowed": False, "pilot_images": len(pilot["records"]),
              "corpus_images": len(corpus["records"]), "internal_duplicates": internal,
              "corpus_overlap": overlap,
              "exact_duplicate_gate_passed": not internal and not overlap,
              "registry_sha256": sha256_file(registry),
              "acquisition_sha256": sha256_file(acquisition / "acquisition.json"),
              "limitations": ["Raw file SHA-256 only; recompressed/cropped copies are not detected",
                              "Near-duplicate and visual annotation gates remain pending"]}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    return report


def audit_near_overlap(
    acquisition: Path, registry: Path, output: Path, *, max_distance: int = 5, workers: int = 8
) -> dict[str, Any]:
    """Screen all pilot/corpus pairs using the existing 64-bit dHash convention."""
    if output.exists():
        raise FileExistsError(output)
    if not 0 <= max_distance <= 64:
        raise ValueError("Invalid Hamming distance")
    pilot = json.loads((acquisition / "acquisition.json").read_text(encoding="utf-8"))
    corpus = json.loads(registry.read_text(encoding="utf-8"))
    for row in pilot["records"]:
        if sha256_file(Path(row["image_path"])) != row["sha256"]:
            raise DatasetValidationError("Pilot image hash changed")

    def fingerprint(row: dict[str, Any]) -> dict[str, Any]:
        path = Path(row["path"])
        if sha256_file(path) != row["sha256"]:
            raise DatasetValidationError("Corpus image changed since hash registry")
        return {**row, "dhash": f"{_dhash(path):016x}"}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        fingerprints = list(pool.map(fingerprint, corpus["records"]))
    selected = [{"image_id": row["image_id"],
                 "dhash": f"{_dhash(Path(row['image_path'])):016x}"}
                for row in pilot["records"]]
    matches = []
    internal = []
    for index, row in enumerate(selected):
        value = int(row["dhash"], 16)
        for existing in fingerprints:
            distance = _hamming_distance(value, int(existing["dhash"], 16))
            if distance <= max_distance:
                matches.append({"image_id": row["image_id"], "distance": distance,
                                "corpus": existing})
        for other in selected[:index]:
            distance = _hamming_distance(value, int(other["dhash"], 16))
            if distance <= max_distance:
                internal.append({"image_ids": [other["image_id"], row["image_id"]],
                                 "distance": distance})
    report = {"training_allowed": False, "method": "64-bit dHash, grayscale 9x8 BILINEAR",
              "max_hamming_distance": max_distance, "pilot_images": len(selected),
              "corpus_images": len(fingerprints), "corpus_candidates": matches,
              "internal_candidates": internal, "pilot_fingerprints": selected,
              "corpus_fingerprints": fingerprints, "registry_sha256": sha256_file(registry),
              "acquisition_sha256": sha256_file(acquisition / "acquisition.json"),
              "limitations": ["Candidates require visual adjudication; similarity is not identity",
                              "Not exhaustive for crops, mirrors, edits or same-session frames",
                              "No model scores or holdout performance used"]}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    return report


def freeze_expansion_plan(
    annotations: Path, audit_path: Path, review_path: Path, output: Path,
    *, sample_size: int = 500, seed: int = 43,
) -> dict[str, Any]:
    """Freeze a bounded train-only expansion after conservative head-overlap exclusion."""
    if output.exists():
        raise FileExistsError(output)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if audit["annotation_sha256"] != sha256_file(annotations):
        raise DatasetValidationError("Expansion annotations do not match audit")
    eligible = {row["image_id"] for row in audit["records"] if row["provisionally_eligible"]}
    pilot_ids = {row["image_id"] for row in review["records"]}
    eligible -= pilot_ids
    selected = []
    overlap_excluded = invalid_excluded = 0
    with annotations.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["ID"] not in eligible:
                continue
            heads = [box.get("hbox") for box in row["gtboxes"]]
            if not all(_valid_box(head) for head in heads):
                invalid_excluded += 1
                continue
            suspicious = False
            for index, (x, y, w, h) in enumerate(heads):
                for X, Y, W, H in heads[:index]:
                    intersection = (max(0, min(x + w, X + W) - max(x, X))
                                    * max(0, min(y + h, Y + H) - max(y, Y)))
                    if intersection / min(w * h, W * H) >= 0.5:
                        suspicious = True
                        break
                if suspicious:
                    break
            if suspicious:
                overlap_excluded += 1
            else:
                selected.append(row["ID"])
    if sample_size < 1 or sample_size > len(selected):
        raise DatasetValidationError("Expansion sample size exceeds filtered population")
    ids = random.Random(seed).sample(sorted(selected), sample_size)
    plan = {"schema_version": 1, "training_allowed": False, "seed": seed,
            "sample_size": sample_size, "population_size": len(selected), "image_ids": ids,
            "annotation_sha256": sha256_file(annotations), "audit_sha256": sha256_file(audit_path),
            "pilot_review_sha256": sha256_file(review_path), "revision": REVISION,
            "filter": "No body-ignore/invalid geometry; exclude all pilot IDs; valid hbox; "
                      "whole-image exclusion when head intersection/min(area) >= 0.5",
            "head_overlap_excluded": overlap_excluded, "invalid_head_excluded": invalid_excluded,
            "selection": "Python random.Random(seed).sample from sorted filtered "
                         "original train IDs",
            "visual_spotcheck_ids": random.Random(44).sample(ids, min(30, len(ids))),
            "visual_spotcheck_seed": 44,
            "stop_condition": "Any new systematic box/completeness problem defers joint conversion",
            "limitations": ["Head overlap is a conservative exclusion heuristic, "
                            "not proof of error",
                            "Does not detect every duplicate, graphic, crop or annotation omission",
                            "Acquire, screen overlaps, spot-check and audit before training"]}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(plan, indent=2) + "\n")
    return plan


def convert_reviewed_pilot(acquisition: Path, review_path: Path, output: Path) -> dict[str, Any]:
    """Convert accepted visible-body boxes only; never approve joint training."""
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("box_convention") != "vbox" or not review.get("reviewer"):
        raise DatasetValidationError("Expected reviewed visible-body convention")
    if (review.get("acquisition_sha256") != sha256_file(acquisition / "acquisition.json")
            or review.get("annotations_sha256")
            != sha256_file(acquisition / "pilot-annotations.json")):
        raise DatasetValidationError("Review does not match acquisition/annotations")
    acquired = json.loads((acquisition / "acquisition.json").read_text(encoding="utf-8"))
    annotations = json.loads((acquisition / "pilot-annotations.json").read_text(encoding="utf-8"))
    rows = {row["ID"]: row for row in annotations}
    decisions = {row["image_id"]: row for row in review["records"]}
    ids = {row["image_id"] for row in acquired["records"]}
    if (set(decisions) != ids or len(decisions) != len(review["records"])
            or any(row.get("decision") not in ("ACCEPT", "EXCLUDE")
                   for row in decisions.values())):
        raise DatasetValidationError("Pilot review incomplete or duplicated")
    output.mkdir(parents=True, exist_ok=False)
    images = output / "images" / "train"
    labels = output / "labels" / "train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    records = []
    for receipt in acquired["records"]:
        image_id = receipt["image_id"]
        if decisions[image_id]["decision"] != "ACCEPT":
            continue
        if not re.fullmatch(r"[\w,.-]+", image_id) or image_id in (".", ".."):
            raise DatasetValidationError("Unsafe derivative image ID")
        source = Path(receipt["image_path"])
        if sha256_file(source) != receipt["sha256"]:
            raise DatasetValidationError("Pilot image hash changed")
        with Image.open(source) as image:
            width, height = image.size
        lines = []
        for box in rows[image_id]["gtboxes"]:
            if (box["tag"] != "person" or box.get("extra", {}).get("ignore", 0)
                    or not _valid_box(box.get("vbox"))):
                raise DatasetValidationError("Unsafe accepted annotation")
            x, y, w, h = box["vbox"]
            left, top = max(0, x), max(0, y)
            right, bottom = min(width, x + w), min(height, y + h)
            if right <= left or bottom <= top:
                raise DatasetValidationError("Empty visible body after clipping")
            values = ((left + right) / (2 * width), (top + bottom) / (2 * height),
                      (right - left) / width, (bottom - top) / height)
            lines.append("2 " + " ".join(f"{value:.8f}" for value in values))
        if not lines:
            raise DatasetValidationError("Accepted image has no person boxes")
        image_path = images / f"{image_id}.jpg"
        label_path = labels / f"{image_id}.txt"
        shutil.copyfile(source, image_path)
        label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        records.append({"image_id": image_id, "image_path": str(image_path.resolve()),
                        "label_path": str(label_path.resolve()), "known_classes": ["person"],
                        "source_sha256": receipt["sha256"], "image_sha256": sha256_file(image_path),
                        "label_sha256": sha256_file(label_path), "boxes": len(lines)})
    report = {"training_allowed": False, "status": "CONVERTED_AWAITING_JOINT_INTAKE_GATE",
              "box_convention": "vbox clipped to image", "class_id": 2,
              "review_sha256": sha256_file(review_path), "records": records,
              "images": len(records), "boxes": sum(row["boxes"] for row in records)}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path)
    args = parser.parse_args(argv)
    acquire(args.plan, args.annotations, args.output)
    if args.review_output:
        render_review(args.output, args.review_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
