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
- [x] Tạo scoped joint dataset v2, loại hai duplicate conflict khỏi index và
  hoàn tất automated + visual data gate với các giới hạn miền được ghi rõ.
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
khỏi index v2, không sửa nguồn. Visual gate đã review 390 mẫu phân tầng và đạt
`PASS_WITH_LIMITATIONS`: box trong scope nhìn chung hợp lý, nhưng corpus có cả
ảnh outdoor, staged và synthetic. Artifact nằm tại
`E:/HomeAssistantPi4/reports/indoor-partial-joint-v2-visual-gate`.
Training được phép chỉ qua class-scoped trainer; đánh giá indoor phải được báo
cáo riêng.

`indoor-prepare-joint` hiện vẫn yêu cầu mỗi nguồn khai báo đủ ba class và mọi ảnh
có label file. Đây là giới hạn hiện tại của tool, không còn là yêu cầu sản phẩm.
Metadata trên E: đã có bốn ứng viên: `indoor-fs-v2` (5.000 ảnh fire/smoke),
`indoor-home-fire-v2` (6.500 ảnh fire/smoke), `coco-person-v1` (12.000 ảnh
person) và `indoor-joint-v1` v32 (9.749 ảnh cả ba class, nhưng indoor gate
failed). Ba nguồn partial đã được ghép thành scoped index v2 và đã qua data gate
với các giới hạn nêu trên; bước tiếp theo là train baseline thống nhất. Tình trạng
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

Config đầu tiên dành cho scoped corpus thống nhất:

```powershell
indoor-train --config configs/train_indoor_v1.yaml
```

Mặc định config đọc dữ liệu và ghi runs trên ổ E. Có thể override:

```powershell
indoor-train --config configs/train_indoor_v1.yaml `
  --data E:/HomeAssistantPi4/processed/indoor-partial-joint-v2/dataset.yaml `
  --project E:\HomeAssistantPi4\runs\indoor-detection
```

Run baseline `indoor_partial_joint_yolo26n_v1` đã dừng sớm ở epoch 22 do một
lỗi trong nhánh postprocess tùy chỉnh của validator inline. Vì vậy `best.pt` của
run này không đại diện cho checkpoint tốt nhất. Khi đánh giá lại bằng validator
đã sửa, `last.pt` đạt mAP50 0,799 và mAP50-95 0,503 trên validation set, so với
0,497 và 0,242 của `best.pt`. Một regression smoke run một epoch cho kết quả
inline mAP50/mAP50-95 là 0,804/0,506 và final là 0,803/0,506. Tiếp tục huấn
luyện phải khởi tạo từ `last.pt` của v1 trong một run mới, không resume hoặc ghi
đè run v1.

Config continuation đã sửa validator:

```powershell
indoor-train --config configs/train_indoor_v2.yaml
```

Config v2 khởi tạo trọng số từ `last.pt` của v1 nhưng tạo optimizer mới: AdamW,
learning rate ban đầu 0,001, tối đa 40 epoch và patience 15. Output được ghi vào
run `indoor_partial_joint_yolo26n_v2`; v1 được giữ nguyên để truy vết.

## Kết quả YOLO26n v2

Training hoàn thành đủ 40 epoch. `best.pt` và `last.pt` cho metric validation
giống nhau; `best.pt` được khóa làm checkpoint phát hành. Evaluator dùng scoped
validator để không tính các class ngoài annotation scope thành negative.

| Split | Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---:|---:|---:|---:|
| val | all | 0,883 | 0,783 | 0,846 | 0,565 |
| val | smoke | 0,923 | 0,882 | 0,926 | 0,625 |
| val | fire | 0,922 | 0,914 | 0,941 | 0,641 |
| val | person | 0,805 | 0,553 | 0,671 | 0,428 |
| test | all | 0,865 | 0,750 | 0,818 | 0,535 |
| test | smoke | 0,898 | 0,876 | 0,917 | 0,631 |
| test | fire | 0,895 | 0,816 | 0,868 | 0,547 |
| test | person | 0,803 | 0,556 | 0,670 | 0,429 |

Validation chọn confidence smoke `0,249249` để đạt recall `0,9002`. Threshold
được giữ nguyên trên test, đạt precision `0,8405` và recall `0,8926`. Báo cáo
machine-readable nằm tại
`E:/HomeAssistantPi4/reports/indoor-yolo26n-v2-evaluation`.

### Validation theo source/domain

Các slice dưới đây chỉ dùng validation và cùng class-scope manifest; ảnh không
được sao chép. `indoor-fs-v2` và `indoor-home-fire-v2` là source proxy gần mục
tiêu indoor hơn COCO person, nhưng visual gate đã thấy cả ảnh outdoor, staged và
synthetic. Vì vậy bảng này không phải benchmark indoor thuần đã xác minh.

| Source | Ảnh val | Class được chấm | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---|---:|---:|---:|---:|
| `indoor-fs-v2` | 500 | smoke, fire | 0,911 | 0,913 | 0,937 | 0,669 |
| `indoor-home-fire-v2` | 1.300 | smoke, fire | 0,931 | 0,888 | 0,928 | 0,611 |
| `coco-person-v1` | 2.501 | person | 0,766 | 0,579 | 0,671 | 0,428 |

Source indexes được tạo lại bằng `indoor-build-evaluation-slices`. Báo cáo JSON
nằm cùng thư mục evaluation; test split không được mở lại cho source selection.

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
