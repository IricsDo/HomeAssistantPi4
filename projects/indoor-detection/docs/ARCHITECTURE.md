# Architecture

## Boundary

Project sở hữu object detection cho `smoke`, `fire`, `person` từ cùng nguồn ảnh.
Ba task chia sẻ một YOLO26n backbone và một lượt inference nhưng giữ policy độc
lập. Identity, pose, fall detection và multi-camera tracking nằm ngoài boundary.

## Development pipeline

```text
Immutable public/raw data on E:
  -> license + integrity audit
  -> unified labels: smoke=0, fire=1, person=2
  -> annotation-completeness gate
  -> source-aware train/val/test split
  -> YOLO26n training on Windows GPU
  -> per-class calibration and error analysis
  -> locked test evaluation
  -> NCNN export
  -> Raspberry Pi 4 benchmark
```

## Runtime pipeline

```text
Frame
  -> image-quality measurement
  -> one three-class detector pass
  -> per-class confidence filters
  -> independent temporal policies
  -> unified event + annotated frame
```

- Smoke: cửa sổ dài hơn, recall-oriented, ảnh mờ chỉ được gắn cờ.
- Fire: cửa sổ ngắn hơn để giảm detection-to-alert latency.
- Person: hiện diện tức thời; không tự tạo hazard alert.
- Person + smoke/fire: phát `occupied_hazard=true`.

`estimated_origin` là bottom-center của smoke/fire box được chọn, chỉ là heuristic
nguồn nhìn thấy. Person không có estimated origin.

## Model contract

Checkpoint hợp lệ phải chứa đúng một class cho mỗi tên `smoke`, `fire`, `person`.
Class ID được đọc từ metadata model thay vì hard-code. Threshold được calibrate
riêng trên validation data.

## Design constraints

- Raspberry Pi 4 4 GB, ARM64, CPU-only baseline.
- Batch size 1 và một model pass cho cả ba task.
- Domain/policy không import PyTorch hoặc Ultralytics.
- Backend model được nạp lazy.
- Không giữ frame queue; chỉ giữ detection summaries theo cửa sổ nhỏ.
- Dataset, checkpoint, run và report lớn nằm trên ổ E.
- PyTorch checkpoint dùng cho training; NCNN là deployment artifact chính.

## Fallback boundary

Nếu model ba lớp làm một class giảm quá quality gate, project vẫn giữ interface
thống nhất nhưng có thể thay backend bằng hai model. Việc tách backend không được
làm thay đổi event schema hoặc policy API.
