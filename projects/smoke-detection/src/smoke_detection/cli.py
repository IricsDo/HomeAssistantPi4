"""Command-line smoke inference for images and recorded video."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from smoke_detection.detector import UltralyticsSmokeDetector
from smoke_detection.quality import is_low_quality
from smoke_detection.rendering import annotate_frame
from smoke_detection.serialization import decision_to_dict
from smoke_detection.temporal import TemporalSmokeFilter

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect smoke in an image or recorded video")
    parser.add_argument("--model", required=True, help="Smoke-only .pt/.onnx or NCNN model path")
    parser.add_argument("--source", required=True, help="Input image or recorded video path")
    parser.add_argument("--output", help="Optional annotated image or video path")
    parser.add_argument("--events", help="Optional JSONL event output path")
    parser.add_argument("--confidence", type=float, default=0.20)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--minimum-positive-frames", type=int, default=3)
    parser.add_argument("--blur-threshold", type=float, default=80.0)
    parser.add_argument("--device", help="Ultralytics device, for example 0 or cpu")
    return parser


def _write_event(stream: Any, event: dict[str, Any]) -> None:
    line = json.dumps(event, ensure_ascii=False)
    print(line)
    if stream is not None:
        stream.write(f"{line}\n")
        stream.flush()


def _process_image(
    source: Path,
    output: Path | None,
    detector: UltralyticsSmokeDetector,
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
    temporal_filter = TemporalSmokeFilter(
        window_size=1,
        minimum_positive_frames=1,
        confidence_threshold=detector.confidence_threshold,
    )
    decision = temporal_filter.update(
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
    detector: UltralyticsSmokeDetector,
    *,
    blur_threshold: float,
    window_size: int,
    minimum_positive_frames: int,
    event_stream: Any,
) -> None:
    import cv2

    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {source}")

    writer = _video_writer(output, capture) if output is not None else None
    temporal_filter = TemporalSmokeFilter(
        window_size=window_size,
        minimum_positive_frames=minimum_positive_frames,
        confidence_threshold=detector.confidence_threshold,
    )

    frame_index = 0
    previous_alert_state = False
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

            if decision.confirmed != previous_alert_state:
                _write_event(event_stream, decision_to_dict(decision, frame_index=frame_index))
                previous_alert_state = decision.confirmed

            if writer is not None:
                writer.write(
                    annotate_frame(frame, detections, decision, blur_score=blur_score)
                )
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

    detector = UltralyticsSmokeDetector(
        args.model,
        confidence_threshold=args.confidence,
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
                window_size=args.window,
                minimum_positive_frames=args.minimum_positive_frames,
                event_stream=event_stream,
            )
    finally:
        if event_stream is not None:
            event_stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
