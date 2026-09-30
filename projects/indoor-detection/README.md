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
- [x] Tạo và audit COCO person subset; dựng index `indoor-v1` ba lớp.
- [x] Quét person candidate trên toàn bộ corpus smoke/fire.
- [x] Xác định partial-label conflict và dừng hướng vẽ lại hàng nghìn box.
- [x] Tải, chuẩn hóa và audit structure/class/duplicate dataset v32 đã gắn đủ
  `smoke/fire/person`.
- [ ] Gỡ blocker duplicate có annotation xung đột và tìm nguồn indoor phù hợp;
  spot-check hiện không đạt data gate. Gói review 59 nhóm duplicate đã tạo
  dưới `E:\HomeAssistantPi4\reports\indoor-joint-v1-audit`.
- [ ] Train, calibrate và đánh giá checkpoint ba lớp.
- [ ] Export NCNN và benchmark trên Pi 4.
- [ ] Tích hợp camera thật.

Các tài liệu và config `smoke` cũ được giữ làm baseline lịch sử, không phải model
deployment cuối cùng. Kết quả khóa nằm trong
[Smoke baseline snapshot](docs/SMOKE_BASELINE_SNAPSHOT.md).
Trạng thái chuẩn bị corpus ba lớp nằm trong
[Indoor v1 dataset preparation](docs/INDOOR_V1_DATASET_PREPARATION.md). Quyết
định chuyển sang dữ liệu đã gắn đủ ba lớp nằm trong
[Joint dataset intake](docs/JOINT_DATASET_INTAKE.md).

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
- unified `person=2` có sẵn trong COCO person subset

Project cho phép ghép nhiều nguồn thành **một model ba lớp**, không bắt buộc mỗi
nguồn đều có đủ `smoke/fire/person`. Tuy nhiên, label YOLO hiện tại không biểu
diễn được trạng thái “chưa biết class này có xuất hiện hay không”: class không có
box sẽ được hiểu là âm tính. Vì vậy, ảnh từ nguồn partial chỉ an toàn để train
khi các class ngoài phạm vi đã được xác minh là không xuất hiện, đã được bổ sung
nhãn, hoặc được xử lý bởi class-masked loss đã triển khai và kiểm thử. Không ghép
thẳng các nguồn partial vào training set.

Pipeline class-masked cho Ultralytics 8.4.163 đã truyền `known_classes` theo từng
ảnh qua train/validation dataloader, mask BCE và bỏ prediction ngoài scope khỏi
validation metrics. Một smoke test một epoch trên bốn ảnh tổng hợp đã đạt. Các
augmentation trộn nhiều ảnh (`mosaic`, `mixup`, `cutmix`, `copy_paste`) bị buộc
về 0 để scope không bị trộn sai; augmentation một ảnh vẫn hoạt động.

Scoped derivative hiện nằm tại
`E:\HomeAssistantPi4\processed\indoor-partial-joint-v2`: 14.900 train, 4.301
validation và 4.297 test. Nó chỉ là index cùng manifest scope trỏ tới ba nguồn
bất biến. Audit đủ 23.498 ảnh đạt structure, label/scope, class distribution và
exact-duplicate gate; hai duplicate conflict ở v1 đã được adjudicate và loại
khỏi index v2, không sửa nguồn. Visual annotation/domain gate vẫn pending nên
chưa được train.

`indoor-prepare-joint` hiện vẫn yêu cầu mỗi nguồn khai báo đủ ba class và mọi ảnh
có label file. Đây là giới hạn hiện tại của tool, không còn là yêu cầu sản phẩm.
Metadata trên E: đã có bốn ứng viên: `indoor-fs-v2` (5.000 ảnh fire/smoke),
`indoor-home-fire-v2` (6.500 ảnh fire/smoke), `coco-person-v1` (12.000 ảnh
person) và `indoor-joint-v1` v32 (9.749 ảnh cả ba class, nhưng indoor gate
failed). Ba nguồn partial đã được ghép thành scoped index để audit, chưa được
train. Bước tiếp theo là chạy toàn bộ data gate trên derivative mới. Tình trạng
license được ghi lại khi intake;
thiếu metadata không tự loại nguồn khỏi khâu đánh giá, nhưng không được xem là
quyền sử dụng đã xác nhận.

Với nguồn đã xác minh đủ nhãn ba lớp, chuẩn hóa thứ tự class bằng:

```powershell
indoor-prepare-joint `
  --dataset-yaml E:\HomeAssistantPi4\raw\fire-smoke-human-v32-clean\data.yaml `
  --output-dir E:\HomeAssistantPi4\processed\indoor-joint-v1 `
  --source-url https://universe.roboflow.com/spyrobot/fire-smoke-and-human-detector/dataset/32 `
  --source-version v32 `
  --source-license "CC BY 4.0" `
  --source-sha256 052078BD4677C6FF4B1D4AF9321B891E0A79AE16F899CED6E45F4BD3A67168A2
```

Tool từ chối dataset không khai báo chính xác ba lớp, yêu cầu label file cho mọi
ảnh, remap `human/person` về `person=2` và ghi provenance vào manifest.
Dataset v32 hiện nằm tại `E:\HomeAssistantPi4\processed\indoor-joint-v1`; audit
cho thấy 100 nhóm ảnh trùng trong cùng split (59 nhóm có label xung đột), dù
không có duplicate xuyên split. Contact sheet cũng cho thấy ảnh fire/smoke chủ
yếu là sự cố ngoài trời. **Chưa train** cho đến khi giải quyết các blocker này.

## Huấn luyện

Config đầu tiên dành cho corpus thống nhất:

```powershell
indoor-train --config configs/train_joint_v1.yaml
```

Mặc định config đọc dữ liệu và ghi runs trên ổ E. Có thể override:

```powershell
indoor-train --config configs/train_joint_v1.yaml `
  --data E:\HomeAssistantPi4\processed\indoor-joint-v1\dataset.yaml `
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
