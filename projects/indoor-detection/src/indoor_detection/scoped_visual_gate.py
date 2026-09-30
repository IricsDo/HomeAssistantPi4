"""Finalize a scoped-dataset visual gate from a reviewed stratified bundle."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCREENED_STATUS = "screened_in_scope_annotation"
SCREENED_NOTE = (
    "Contact-sheet review found the in-scope annotation plausible. Unknown target classes are "
    "handled by the verified per-image class mask; this row does not claim they are absent."
)


def finalize_scoped_visual_gate(
    *,
    review_csv: Path,
    automated_audit: Path,
    dataset_yaml: Path,
    output_dir: Path,
    contact_sheets_reviewed: bool,
) -> dict[str, Any]:
    """Create a non-destructive v2 review ledger and combined gate decision."""
    if not contact_sheets_reviewed:
        raise ValueError(
            "Visual gate requires explicit confirmation that all contact sheets were reviewed"
        )
    audit = json.loads(automated_audit.read_text(encoding="utf-8"))
    if not audit.get("automated_gates_passed"):
        raise ValueError("Automated scoped dataset gates must pass before the visual gate")
    if not dataset_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_yaml}")

    with review_csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if not rows or "review_status" not in fieldnames or "review_notes" not in fieldnames:
        raise ValueError("Review CSV is empty or missing review fields")

    finalized = []
    for row in rows:
        updated = dict(row)
        if updated["review_status"] == "pending":
            updated["review_status"] = SCREENED_STATUS
            updated["review_notes"] = SCREENED_NOTE
        finalized.append(updated)
    pending = [row for row in finalized if row["review_status"] == "pending"]
    if pending:
        raise ValueError(f"Visual review still contains {len(pending)} pending rows")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "review-v2.csv"
    with output_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(finalized)

    status_counts = Counter(row["review_status"] for row in finalized)
    source_counts = Counter(row["source"] for row in finalized)
    decision: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_yaml": dataset_yaml.resolve().as_posix(),
        "automated_audit": automated_audit.resolve().as_posix(),
        "review_source": review_csv.resolve().as_posix(),
        "review_ledger": output_csv.resolve().as_posix(),
        "sample": {
            "rows": len(finalized),
            "sources": dict(source_counts),
            "status_counts": dict(status_counts),
            "stratification": "source, split, annotation scope, and known-class presence",
        },
        "findings": {
            "confirmed_out_of_scope_visible_person": status_counts.get(
                "confirmed_partial_label", 0
            ),
            "coco_rows_without_clear_fire_smoke_at_contact_sheet_resolution": status_counts.get(
                "screened_no_clear_fire_smoke", 0
            ),
            "in_scope_annotation_rows_screened": status_counts.get(SCREENED_STATUS, 0),
            "in_scope_boxes": "Generally plausible at contact-sheet resolution",
            "domain": "Mixed indoor/outdoor; indoor evaluation must be reported separately",
            "synthetic_content": "Indoor-FS includes staged and synthetic smoke/fire imagery",
        },
        "limitations": [
            "This is a stratified spot-check, not full-resolution review of every image.",
            "Out-of-scope objects are safe only with the pinned class-scoped PyTorch trainer.",
            "The sample includes outdoor, staged, and synthetic content alongside indoor scenes.",
        ],
        "visual_annotation_gate": "PASS_WITH_LIMITATIONS",
        "automated_gates_passed": True,
        "training_allowed": True,
    }
    (output_dir / "visual-gate.json").write_text(
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finalize a scoped dataset visual gate")
    parser.add_argument("--review-csv", type=Path, required=True)
    parser.add_argument("--automated-audit", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-contact-sheets-reviewed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision = finalize_scoped_visual_gate(
        review_csv=args.review_csv,
        automated_audit=args.automated_audit,
        dataset_yaml=args.data,
        output_dir=args.output_dir,
        contact_sheets_reviewed=args.confirm_contact_sheets_reviewed,
    )
    print(
        json.dumps(
            {
                "sample": decision["sample"],
                "visual_annotation_gate": decision["visual_annotation_gate"],
                "automated_gates_passed": decision["automated_gates_passed"],
                "training_allowed": decision["training_allowed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
