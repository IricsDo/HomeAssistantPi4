# Data directory

Không commit ảnh, label hay archive dataset vào Git. Trên máy phát triển Windows, dữ
liệu nặng được lưu tại `E:\HomeAssistantPi4`:

- `raw/Home-fire-dataset/v1.0.0/`: archive tải từ GitHub Release, giữ nguyên.
- `processed/smoke-home-fire-v1/`: dataset YOLO smoke-only dùng cho train/val/test.
- `manifests/`: checksum, nguồn, license và thống kê chuyển đổi.
- `reports/`: kết quả audit ảnh, annotation và duplicate giữa các split.

Chuẩn bị và audit dữ liệu:

```powershell
.venv\Scripts\python.exe -m smoke_detection.dataset prepare `
  --raw-dir E:\HomeAssistantPi4\raw\Home-fire-dataset\v1.0.0 `
  --output-dir E:\HomeAssistantPi4\processed\smoke-home-fire-v1 `
  --manifest E:\HomeAssistantPi4\manifests\home-fire-v1.0.0.json

.venv\Scripts\python.exe -m smoke_detection.dataset audit `
  --dataset-root E:\HomeAssistantPi4\processed\smoke-home-fire-v1 `
  --report E:\HomeAssistantPi4\reports\smoke-home-fire-v1.audit.json
```

Mapping Home-fire: class nguồn `0=fire` bị loại bỏ; class nguồn `1=smoke` được đổi
thành class đích `0=smoke`. Ảnh không còn box smoke được giữ làm negative sample.
Đường dẫn `E:` chỉ là cấu hình máy phát triển; khi đưa lên Pi 4, dùng file
`dataset.yaml` được tạo trong thư mục processed hoặc truyền `smoke-train --data ...`.
