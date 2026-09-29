from indoor_detection.domain import BoundingBox, Detection, DetectionClass
from indoor_detection.serialization import decision_to_dict
from indoor_detection.temporal import MultiClassTemporalFilter


def test_event_schema_reports_occupied_hazard() -> None:
    detections = [
        Detection(
            BoundingBox(0, 0, 10, 10),
            confidence=0.9,
            frame_index=0,
            class_id=1,
            target_class=DetectionClass.FIRE,
        ),
        Detection(
            BoundingBox(10, 10, 30, 50),
            confidence=0.9,
            frame_index=0,
            class_id=2,
            target_class=DetectionClass.PERSON,
        ),
    ]
    temporal_filter = MultiClassTemporalFilter()
    temporal_filter.update(frame_index=0, detections=detections)
    decision = temporal_filter.update(frame_index=1, detections=detections)

    event = decision_to_dict(decision, frame_index=1)

    assert event["schema_version"] == 2
    assert event["active_classes"] == ["fire", "person"]
    assert event["hazard_confirmed"] is True
    assert event["person_present"] is True
    assert event["occupied_hazard"] is True
    assert event["classes"]["fire"]["estimated_origin"] == [5.0, 10]
    assert event["classes"]["person"]["estimated_origin"] is None
