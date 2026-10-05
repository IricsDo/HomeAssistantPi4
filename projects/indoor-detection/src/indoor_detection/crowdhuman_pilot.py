"""Acquire frozen CrowdHuman pilot images from pinned remote ZIP members."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

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
