from __future__ import annotations

import csv
import json

import pytest

from indoor_detection.scoped_visual_gate import finalize_scoped_visual_gate


def _write_inputs(tmp_path):
    data = tmp_path / "dataset.yaml"
    data.write_text("names: [smoke, fire, person]\n", encoding="utf-8")
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"automated_gates_passed": True}), encoding="utf-8")
    review = tmp_path / "review.csv"
    fields = ["review_id", "source", "review_status", "review_notes"]
    with review.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {"review_id": "one", "source": "fire", "review_status": "pending", "review_notes": ""}
        )
        writer.writerow(
            {
                "review_id": "two",
                "source": "person",
                "review_status": "screened_no_clear_fire_smoke",
                "review_notes": "screened",
            }
        )
    return data, audit, review


def test_finalize_scoped_visual_gate_preserves_source_and_resolves_pending(tmp_path) -> None:
    data, audit, review = _write_inputs(tmp_path)

    decision = finalize_scoped_visual_gate(
        review_csv=review,
        automated_audit=audit,
        dataset_yaml=data,
        output_dir=tmp_path / "out",
        contact_sheets_reviewed=True,
    )

    assert decision["training_allowed"]
    assert decision["sample"]["status_counts"]["screened_in_scope_annotation"] == 1
    assert "pending" in review.read_text(encoding="utf-8-sig")
    assert "pending" not in (tmp_path / "out" / "review-v2.csv").read_text(encoding="utf-8-sig")


def test_finalize_requires_explicit_visual_confirmation(tmp_path) -> None:
    data, audit, review = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="explicit confirmation"):
        finalize_scoped_visual_gate(
            review_csv=review,
            automated_audit=audit,
            dataset_yaml=data,
            output_dir=tmp_path / "out",
            contact_sheets_reviewed=False,
        )
