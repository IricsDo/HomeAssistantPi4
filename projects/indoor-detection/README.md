# Indoor Detection

Một detector YOLO26n thống nhất cho ba lớp `smoke`, `fire`, `person` trong môi
trường trong nhà. Project phát triển trên Windows 11 và export NCNN để chạy một
lượt inference trên Raspberry Pi 4 4 GB.

## Phạm vi

- Phát hiện bounding box cho `smoke`, `fire`, `person`.
- Dùng confidence threshold và temporal policy độc lập cho từng lớp.
- Smoke ưu tiên recall và không bị loại bỏ chỉ vì ảnh mờ.
- Fire xác nhận nhanh hơn smoke.
- Person là trạng thái hiện diện; chỉ tăng ưu tiên khi đồng thời có hazard.
- Không bao gồm nhận diện danh tính, pose, fall detection hay tracking dài hạn.

Đây là lớp cảnh báo bổ sung bằng camera, không thay thế đầu báo khói hoặc đầu báo
nhiệt đạt chuẩn.

## Trạng thái

- [x] Baseline smoke-only và checkpoint tham chiếu đã được khóa.
- [x] Package, domain, detector và event schema đã generalize cho ba lớp.
- [x] Dataset converters giữ lại cả smoke và fire.
- [x] Class-specific confidence/temporal policy.
- [ ] Bổ sung và audit annotation person trên toàn bộ training corpus.
- [ ] Train, calibrate và đánh giá checkpoint ba lớp.
- [ ] Export NCNN và benchmark trên Pi 4.
- [ ] Tích hợp camera thật.

Các tài liệu và config `smoke` cũ được giữ làm baseline lịch sử, không phải model
deployment cuối cùng. Kết quả khóa nằm trong
[Smoke baseline snapshot](docs/SMOKE_BASELINE_SNAPSHOT.md).

## Cài đặt trên Windows 11

```powershell
cd projects/indoor-detection
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Máy phát triển có thể cài PyTorch CUDA theo
`requirements-windows-gpu.txt`. Source hỗ trợ Python 3.12 đến 3.14.

```powershell
python -m pytest
indoor-detect --help
indoor-train --help
indoor-export --help
indoor-benchmark --help
```

## Model contract

Model runtime phải khai báo đúng ba lớp, thứ tự có thể khác nhau:

```yaml
names:
  0: smoke
  1: fire
  2: person
```

Runtime đọc mapping thực tế từ model và từ chối checkpoint thiếu/thừa class.

## Dữ liệu

Artifacts lớn nằm tại `E:\HomeAssistantPi4` và không được commit. Hai nguồn
fire/smoke hiện có được tái tạo với mapping:

- source `fire=0` -> unified `fire=1`
- source `smoke=1` -> unified `smoke=0`
- unified `person=2` được bổ sung từ dữ liệu person và annotation audit

Không được train model ba lớp cho đến khi ảnh fire/smoke đã được kiểm tra người
không gán nhãn. Một người xuất hiện nhưng thiếu box sẽ bị học như background.

## Huấn luyện

Config đầu tiên dành cho corpus thống nhất:

```powershell
indoor-train --config configs/train_indoor_v1.yaml
```

Mặc định config đọc dữ liệu và ghi runs trên ổ E. Có thể override:

```powershell
indoor-train --config configs/train_indoor_v1.yaml `
  --data E:\HomeAssistantPi4\datasets\indoor-v1\dataset.yaml `
  --project E:\HomeAssistantPi4\runs\indoor-detection
```

## Inference

```powershell
indoor-detect `
  --model E:\HomeAssistantPi4\models\checkpoints\indoor_yolo26n_v1.pt `
  --source path\to\sample.mp4 `
  --output outputs\sample-annotated.mp4 `
  --events outputs\sample-events.jsonl
```

Event schema v2 cung cấp `active_classes`, `hazard_confirmed`, `person_present`,
`occupied_hazard` và chi tiết riêng của từng lớp.

## Export cho Raspberry Pi

```powershell
indoor-export `
  --model E:\HomeAssistantPi4\models\checkpoints\indoor_yolo26n_v1.pt `
  --format ncnn --imgsz 416
```

Xem [Architecture](docs/ARCHITECTURE.md) và
[Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md).
