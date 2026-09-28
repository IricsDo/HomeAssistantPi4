# Smoke Detection

Hệ thống phát hiện và khoanh vùng khói trong môi trường trong nhà. Project được
phát triển trên Windows 11, sau đó export sang NCNN để chạy độc lập trên
Raspberry Pi 4 4 GB.

## Phạm vi

- Chỉ phát hiện class `smoke`.
- Hỗ trợ ảnh và video ghi sẵn trong giai đoạn phát triển.
- Trả về bounding box, confidence và trạng thái cảnh báo theo chuỗi frame.
- Ước lượng vị trí nguồn khói bằng điểm đáy của vùng khói được chọn.
- Ưu tiên recall; ảnh mờ có thể vẫn phát cảnh báo và được gắn cờ chất lượng thấp.

Fire/flame detection, person detection, camera thật và việc điều phối nhiều model
không thuộc phạm vi project này.

## Trạng thái

Phase 3 - baseline training và đánh giá độc lập.

- [x] Cấu trúc package và cấu hình smoke-only.
- [x] Temporal confirmation và blur quality flag.
- [x] Backend Ultralytics được nạp lazy.
- [x] CLI inference ảnh/video.
- [x] Script train, export NCNN và benchmark.
- [x] Unit test cho logic không phụ thuộc model.
- [x] Tải, kiểm tra và chuẩn hóa Home-fire v1.0.0 (6.500 ảnh).
- [x] Huấn luyện và đánh giá checkpoint YOLO26n baseline đầu tiên.
- [ ] Cải thiện test recall từ 0,823 lên >= 0,90 mà không làm precision sụt mạnh.
- [ ] Export và benchmark trên Raspberry Pi 4.
- [ ] Tích hợp camera.

## Cài đặt trên Windows 11

Project sử dụng virtual environment riêng. Máy phát triển hiện tại dùng Python
3.14; source vẫn giữ mức cú pháp tương thích Python 3.12:

```powershell
cd projects/smoke-detection
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip install --upgrade --force-reinstall `
  torch==2.14.0 torchvision==0.29.0 `
  --index-url https://download.pytorch.org/whl/cu130
```

Lệnh cuối thay PyTorch CPU-only bằng bản CUDA phù hợp RTX 5070. Các phiên bản đã
kiểm thử được ghi trong `requirements-windows-gpu.txt`.

Kiểm tra:

```powershell
python -m pytest
smoke-detect --help
smoke-train --help
smoke-export --help
smoke-benchmark --help
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Dataset

Dataset chuẩn có cấu trúc:

```text
smoke-home-fire-v1/
|-- images/
|   |-- train/
|   |-- val/
|   `-- test/
`-- labels/
    |-- train/
    |-- val/
    `-- test/
```

Mỗi annotation dùng YOLO format và chỉ được chứa class `0` (`smoke`). Dataset
không được commit vào Git. Dữ liệu phát triển hiện nằm tại
`E:\HomeAssistantPi4\processed\smoke-home-fire-v1`; chi tiết tái tạo và audit nằm
trong [Phase 2 dataset report](docs/PHASE_2_DATASET.md).

## Huấn luyện

```powershell
smoke-train --config configs/train.yaml `
  --data E:\HomeAssistantPi4\processed\smoke-home-fire-v1\dataset.yaml `
  --model E:\HomeAssistantPi4\models\pretrained\yolo26n.pt `
  --project E:\HomeAssistantPi4\runs\smoke-detection `
  --name yolo26n_baseline_640
```

Checkpoint baseline ổn định nằm ngoài repo tại
`E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_homefire_v1_baseline.pt`.
Kết quả đầy đủ và các giới hạn hiện tại nằm trong
[Phase 3 baseline report](docs/PHASE_3_BASELINE.md).

Đánh giá tái tạo được:

```powershell
python -m smoke_detection.evaluate `
  --model E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_homefire_v1_baseline.pt `
  --data E:\HomeAssistantPi4\processed\smoke-home-fire-v1\dataset.yaml `
  --split test --imgsz 640 --device 0 `
  --project E:\HomeAssistantPi4\runs\smoke-detection\evaluation `
  --name yolo26n_baseline_640_test `
  --report E:\HomeAssistantPi4\reports\yolo26n_baseline_640_test.json
```

## Inference

Sau khi có checkpoint smoke:

```powershell
smoke-detect `
  --model E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_homefire_v1_baseline.pt `
  --source path\to\sample.mp4 `
  --output outputs\sample-annotated.mp4
```

Ảnh đơn tự động dùng một frame để xác nhận. Video mặc định yêu cầu phát hiện ở
3 trong 5 frame gần nhất.

## Export cho Raspberry Pi

```powershell
smoke-export `
  --model runs/detect/smoke_yolo26n/weights/best.pt `
  --format ncnn `
  --imgsz 416
```

Benchmark một ảnh đại diện:

```powershell
smoke-benchmark --model models/exported/smoke_ncnn_model --source sample.jpg
```

## Tài liệu

- [Architecture](docs/ARCHITECTURE.md)
- [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Đây là lớp cảnh báo bổ sung bằng camera, không thay thế đầu báo khói hoặc đầu báo
nhiệt đạt chuẩn.
