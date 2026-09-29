"""Ultralytics adapter constrained to the unified three-class contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from indoor_detection.domain import SUPPORTED_CLASSES, BoundingBox, Detection, DetectionClass


class InvalidDetectionModelError(ValueError):
    """Raised when a model does not expose smoke, fire and person exactly once."""


class UltralyticsIndoorDetector:
    """Lazy Ultralytics backend supporting PyTorch, ONNX and NCNN artifacts."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        confidence_thresholds: Mapping[DetectionClass | str, float] | None = None,
        iou_threshold: float = 0.45,
        image_size: int = 416,
        device: str | None = None,
    ) -> None:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Indoor detection model not found: {path}")

        from ultralytics import YOLO

        self._model = YOLO(str(path))
        self.class_map = self._validate_model_names(self._model.names)
        self.confidence_thresholds = self._normalize_thresholds(confidence_thresholds)
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self.device = device

    @staticmethod
    def _validate_model_names(
        names: dict[int, str] | list[str],
    ) -> dict[int, DetectionClass]:
        normalized = dict(enumerate(names)) if isinstance(names, list) else dict(names)
        try:
            class_map = {
                int(class_id): DetectionClass(str(class_name).strip().lower())
                for class_id, class_name in normalized.items()
            }
        except ValueError as exc:
            raise InvalidDetectionModelError(
                "Expected exactly the classes 'smoke', 'fire' and 'person'; "
                f"received {normalized}"
            ) from exc

        if len(class_map) != 3 or set(class_map.values()) != SUPPORTED_CLASSES:
            raise InvalidDetectionModelError(
                "Expected exactly the classes 'smoke', 'fire' and 'person'; "
                f"received {normalized}"
            )
        return class_map

    @staticmethod
    def _normalize_thresholds(
        values: Mapping[DetectionClass | str, float] | None,
    ) -> dict[DetectionClass, float]:
        thresholds = {
            DetectionClass.SMOKE: 0.20,
            DetectionClass.FIRE: 0.25,
            DetectionClass.PERSON: 0.35,
        }
        if values:
            for key, value in values.items():
                target_class = key if isinstance(key, DetectionClass) else DetectionClass(key)
                if not 0.0 <= value <= 1.0:
                    raise ValueError("Confidence thresholds must be between 0 and 1")
                thresholds[target_class] = float(value)
        return thresholds

    def predict(self, frame: Any, *, frame_index: int) -> list[Detection]:
        predict_options: dict[str, Any] = {
            "source": frame,
            "conf": min(self.confidence_thresholds.values()),
            "iou": self.iou_threshold,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device is not None:
            predict_options["device"] = self.device

        result = self._model.predict(**predict_options)[0]
        boxes = result.boxes
        if boxes is None:
            return []

        detections: list[Detection] = []
        for xyxy, confidence, raw_class_id in zip(
            boxes.xyxy.cpu().tolist(),
            boxes.conf.cpu().tolist(),
            boxes.cls.cpu().tolist(),
            strict=True,
        ):
            class_id = int(raw_class_id)
            target_class = self.class_map.get(class_id)
            if target_class is None or confidence < self.confidence_thresholds[target_class]:
                continue
            detections.append(
                Detection(
                    box=BoundingBox(*map(float, xyxy)),
                    confidence=float(confidence),
                    frame_index=frame_index,
                    class_id=class_id,
                    target_class=target_class,
                )
            )
        return detections
