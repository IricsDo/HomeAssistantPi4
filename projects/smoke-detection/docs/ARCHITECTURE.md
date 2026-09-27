# Architecture

## Boundary

Project này chỉ sở hữu smoke detection. Fire/flame detection, person detection
và orchestration giữa nhiều model là các project khác.

## Development pipeline

```text
Public datasets
  -> license and integrity audit
  -> smoke-only YOLO labels
  -> source-aware train/val/test split
  -> YOLO26n training on Windows
  -> validation and error analysis
  -> NCNN export
  -> Raspberry Pi benchmark
```

## Runtime pipeline

```text
Image or video frame
  -> image-quality measurement
  -> smoke detector
  -> smoke-only class filter
  -> temporal confirmation
  -> bounding boxes + estimated origin + alert state
  -> optional annotated media and JSONL event log
```

`estimated_origin` là bottom-center của detection được chọn trong cửa sổ thời
gian. Đây là heuristic vị trí vùng phát khói nhìn thấy, không phải kết luận vật
thể nào gây cháy.

## Design constraints

- Raspberry Pi 4 4 GB, ARM64, CPU-only baseline.
- Batch size 1 khi inference.
- Không import PyTorch/Ultralytics trong domain logic hoặc unit test.
- Backend model được nạp lazy để CLI `--help` và test không cần khởi tạo model.
- Không giữ frame queue dài; runtime xử lý tuần tự ở Phase 1.
- Detection mờ không bị loại bỏ. Cờ `low_image_quality` đi cùng cảnh báo.
- Artifacts lớn nằm ngoài Git.

## Model contract

Model hợp lệ phải khai báo đúng một class có tên `smoke`. Backend từ chối model
không có class này để tránh vô tình chạy COCO pretrained weights như một smoke
detector.

## Deployment path

PyTorch checkpoint là artifact huấn luyện. NCNN là artifact deployment chính.
ONNX được giữ làm fallback và công cụ đối chiếu. Runtime cuối trên Pi sẽ chỉ giữ
dependency cần cho inference sau khi benchmark xác nhận cách đóng gói phù hợp.
