"""Command-line indoor inference for images and recorded video."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from indoor_detection.detector import UltralyticsIndoorDetector
from indoor_detection.domain import DetectionClass
from indoor_detection.quality import is_low_quality
from indoor_detection.rendering import annotate_frame
from indoor_detection.serialization import decision_to_dict
from indoor_detection.temporal import MultiClassTemporalFilter, TemporalPolicy

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect smoke, fire and people in an image or recorded video"
    )
    parser.add_argument("--model", required=True, help="Three-class .pt/.onnx or NCNN model")
    parser.add_argument("--source", required=True, help="Input image or recorded video path")
    parser.add_argument("--output", help="Optional annotated image or video path")
    parser.add_argument("--events", help="Optional JSONL event output path")
    parser.add_argument("--smoke-confidence", type=float, default=0.20)
    parser.add_argument("--fire-confidence", type=float, default=0.25)
    parser.add_argument("--person-confidence", type=float, default=0.35)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--smoke-window", type=int, default=5)
    parser.add_argument("--smoke-minimum-positive-frames", type=int, default=3)
    parser.add_argument("--fire-window", type=int, default=3)
    parser.add_argument("--fire-minimum-positive-frames", type=int, default=2)
    parser.add_argument("--blur-threshold", type=float, default=80.0)
    parser.add_argument("--device", help="Ultralytics device, for example 0 or cpu")
    return parser


def _write_event(stream: Any, event: dict[str, Any]) -> None:
    line = json.dumps(event, ensure_ascii=False)
    print(line)
    if stream is not None:
        stream.write(f"{line}\n")
        stream.flush()


def _instant_filter(detector: UltralyticsIndoorDetector) -> MultiClassTemporalFilter:
    return MultiClassTemporalFilter(
        {
            target_class: TemporalPolicy(
                window_size=1,
                minimum_positive_frames=1,
                confidence_threshold=threshold,
            )
            for target_class, threshold in detector.confidence_thresholds.items()
        }
    )


def _process_image(
    source: Path,
    output: Path | None,
    detector: UltralyticsIndoorDetector,
    *,
    blur_threshold: float,
    event_stream: Any,
) -> None:
    import cv2

    frame = cv2.imread(str(source))
    if frame is None:
        raise ValueError(f"Could not read image: {source}")

    low_quality, blur_score = is_low_quality(frame, blur_threshold=blur_threshold)
    detections = detector.predict(frame, frame_index=0)
    decision = _instant_filter(detector).update(
        frame_index=0,
        detections=detections,
        low_image_quality=low_quality,
    )
    _write_event(event_stream, decision_to_dict(decision, frame_index=0))

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        annotated = annotate_frame(frame, detections, decision, blur_score=blur_score)
        if not cv2.imwrite(str(output), annotated):
            raise OSError(f"Could not write image: {output}")


def _video_writer(output: Path, capture: Any) -> Any:
    import cv2

    output.parent.mkdir(parents=True, exist_ok=True)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise OSError(f"Could not open video writer: {output}")
    return writer


def _process_video(
    source: Path,
    output: Path | None,
    detector: UltralyticsIndoorDetector,
    *,
    blur_threshold: float,
    smoke_window: int,
    smoke_minimum_positive_frames: int,
    fire_window: int,
    fire_minimum_positive_frames: int,
    event_stream: Any,
) -> None:
    import cv2

    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {source}")

    writer = _video_writer(output, capture) if output is not None else None
    thresholds = detector.confidence_thresholds
    temporal_filter = MultiClassTemporalFilter(
        {
            DetectionClass.SMOKE: TemporalPolicy(
                smoke_window,
                smoke_minimum_positive_frames,
                thresholds[DetectionClass.SMOKE],
            ),
            DetectionClass.FIRE: TemporalPolicy(
                fire_window,
                fire_minimum_positive_frames,
                thresholds[DetectionClass.FIRE],
            ),
            DetectionClass.PERSON: TemporalPolicy(
                1,
                1,
                thresholds[DetectionClass.PERSON],
            ),
        }
    )

    frame_index = 0
    previous_active_classes: frozenset[DetectionClass] = frozenset()
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            low_quality, blur_score = is_low_quality(frame, blur_threshold=blur_threshold)
            detections = detector.predict(frame, frame_index=frame_index)
            decision = temporal_filter.update(
                frame_index=frame_index,
                detections=detections,
                low_image_quality=low_quality,
            )

            if decision.active_classes != previous_active_classes:
                _write_event(event_stream, decision_to_dict(decision, frame_index=frame_index))
                previous_active_classes = decision.active_classes

            if writer is not None:
                writer.write(annotate_frame(frame, detections, decision, blur_score=blur_score))
            frame_index += 1
    finally:
        capture.release()
        if writer is not None:
            writer.release()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.source)
    if not source.is_file():
        raise FileNotFoundError(f"Input source not found: {source}")

    detector = UltralyticsIndoorDetector(
        args.model,
        confidence_thresholds={
            DetectionClass.SMOKE: args.smoke_confidence,
            DetectionClass.FIRE: args.fire_confidence,
            DetectionClass.PERSON: args.person_confidence,
        },
        iou_threshold=args.iou,
        image_size=args.imgsz,
        device=args.device,
    )

    output = Path(args.output) if args.output else None
    event_path = Path(args.events) if args.events else None
    if event_path is not None:
        event_path.parent.mkdir(parents=True, exist_ok=True)

    event_stream = event_path.open("w", encoding="utf-8") if event_path else None
    try:
        if source.suffix.lower() in IMAGE_SUFFIXES:
            _process_image(
                source,
                output,
                detector,
                blur_threshold=args.blur_threshold,
                event_stream=event_stream,
            )
        else:
            _process_video(
                source,
                output,
                detector,
                blur_threshold=args.blur_threshold,
                smoke_window=args.smoke_window,
                smoke_minimum_positive_frames=args.smoke_minimum_positive_frames,
                fire_window=args.fire_window,
                fire_minimum_positive_frames=args.fire_minimum_positive_frames,
                event_stream=event_stream,
            )
    finally:
        if event_stream is not None:
            event_stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
