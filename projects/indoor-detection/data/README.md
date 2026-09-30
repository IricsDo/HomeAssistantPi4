# Data directory

Không commit ảnh, label hay archive dataset vào Git. Trên máy phát triển Windows, dữ
liệu nặng được lưu tại `E:\HomeAssistantPi4`:

- `raw/Home-fire-dataset/v1.0.0/`: archive tải từ GitHub Release, giữ nguyên.
- `raw/COCO2017/`: annotation chính thức và cache chỉ các ảnh person đã chọn.
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

Tạo COCO-person subset sau khi tải `annotations_trainval2017.zip` chính thức:

```powershell
indoor-prepare-coco-person `
  --train-annotations E:\HomeAssistantPi4\raw\COCO2017\annotations\instances_train2017.json `
  --train-images E:\HomeAssistantPi4\raw\COCO2017\images\train2017 `
  --val-annotations E:\HomeAssistantPi4\raw\COCO2017\annotations\instances_val2017.json `
  --val-images E:\HomeAssistantPi4\raw\COCO2017\images\val2017 `
  --output-dir E:\HomeAssistantPi4\processed\coco-person-v1 `
  --manifest E:\HomeAssistantPi4\manifests\coco-person-v1.json `
  --download-missing
```

Mặc định chỉ chọn 6.000 positive + 1.000 negative từ train2017. Toàn bộ ảnh hợp
lệ của val2017 được chia cố định 50/50 thành validation và test; crowd-only images
bị loại để không trở thành false negative.

Quét các corpus smoke/fire để tìm người chưa được gán nhãn:

```powershell
indoor-audit-person `
  --data E:\HomeAssistantPi4\interim\indoor-smoke-fire-v1\dataset.yaml `
  --model E:\HomeAssistantPi4\models\pretrained\yolo26n.pt `
  --output-dir E:\HomeAssistantPi4\reports\person-audit-v2
```

Lệnh chỉ tạo `candidates.jsonl` và báo cáo; không sửa label nguồn. Mọi candidate,
kể cả nhóm confidence cao, phải được review. Pseudo-label được chấp nhận phải nằm
trong một derivative mới trước khi compose dataset dùng để train.

Tạo contact sheets và bảng quyết định review:

```powershell
indoor-review-person `
  --candidates E:\HomeAssistantPi4\reports\person-audit-v2\candidates.jsonl `
  --output-dir E:\HomeAssistantPi4\reviews\person-audit-v2
```

Mở các trang JPEG theo nhóm status và điền `accept` hoặc `reject` vào cột
`decision` của `decisions.tsv`; không thay đổi `review_id`.

Có thể dùng một COCO detector mạnh hơn để ưu tiên thứ tự review, nhưng không tự
động chấp nhận nhãn:

```powershell
indoor-verify-person `
  --candidates E:\HomeAssistantPi4\reports\person-audit-v2\candidates.jsonl `
  --verifier-model E:\HomeAssistantPi4\models\pretrained\yolo26m.pt `
  --output-dir E:\HomeAssistantPi4\reports\person-consensus-v1
```

Sau đó truyền `person-consensus-v1\candidates.jsonl` cho
`indoor-review-person`. Nhóm `consensus_high_review` chỉ có nghĩa hai model đồng
thuận, vẫn cần người review trước khi ghi nhãn.

Sau khi mọi candidate row trong `decisions.tsv` đã là `accept` hoặc `reject`, tạo
derivative mới (lệnh sẽ từ chối nếu còn ô trống hoặc có box accept trùng nhau):

```powershell
indoor-apply-person `
  --source-data E:\HomeAssistantPi4\interim\indoor-smoke-fire-v1\dataset.yaml `
  --decisions E:\HomeAssistantPi4\reviews\person-consensus-v3\decisions.tsv `
  --output-dir E:\HomeAssistantPi4\processed\indoor-smoke-fire-person-v1
```

Source images/labels không bị sửa; derivative dùng hardlink khi filesystem hỗ trợ
và lưu checksum bảng quyết định trong manifest.
Đường dẫn `E:` chỉ là cấu hình máy phát triển; khi đưa lên Pi 4, dùng file
`dataset.yaml` được tạo trong thư mục processed hoặc truyền `indoor-train --data ...`.
