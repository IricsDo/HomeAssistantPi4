# Data directory

Không commit ảnh, label hay archive dataset vào Git. Trên máy phát triển Windows, dữ
liệu nặng được lưu tại `E:\HomeAssistantPi4`:

- `raw/Home-fire-dataset/v1.0.0/`: archive tải từ GitHub Release, giữ nguyên.
- `processed/indoor-home-fire-v2/`: derivative giữ cả smoke và fire.
- `datasets/indoor-v1/`: index cuối cho smoke, fire và person sau annotation audit.
- `manifests/`: checksum, nguồn, license và thống kê chuyển đổi.
- `reports/`: kết quả audit ảnh, annotation và duplicate giữa các split.

Chuẩn bị và audit dữ liệu:

```powershell
.venv\Scripts\python.exe -m indoor_detection.dataset prepare `
  --raw-dir E:\HomeAssistantPi4\raw\Home-fire-dataset\v1.0.0 `
  --output-dir E:\HomeAssistantPi4\processed\indoor-home-fire-v2 `
  --manifest E:\HomeAssistantPi4\manifests\indoor-home-fire-v2.json

.venv\Scripts\python.exe -m indoor_detection.dataset audit `
  --dataset-root E:\HomeAssistantPi4\processed\indoor-home-fire-v2 `
  --report E:\HomeAssistantPi4\reports\indoor-home-fire-v2.audit.json
```

Mapping Home-fire: `0=fire -> 1=fire`, `1=smoke -> 0=smoke`; class đích
`2=person` dành cho corpus person và annotation enrichment. Không train corpus
thống nhất nếu ảnh fire/smoke có người chưa được gán box.
Đường dẫn `E:` chỉ là cấu hình máy phát triển; khi đưa lên Pi 4, dùng file
`dataset.yaml` được tạo trong thư mục processed hoặc truyền `indoor-train --data ...`.
