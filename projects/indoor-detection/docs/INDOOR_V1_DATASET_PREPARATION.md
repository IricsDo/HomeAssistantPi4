# Indoor v1 dataset preparation

Ngày ghi nhận: 2026-09-30.

## Kết quả đã khóa

COCO 2017 person subset được tạo với seed 42 và mapping thống nhất
`smoke=0`, `fire=1`, `person=2`:

| Split | Images | Positive | Negative | Person boxes |
| --- | ---: | ---: | ---: | ---: |
| train | 7.000 | 6.000 | 1.000 | 23.611 |
| val | 2.501 | 1.347 | 1.154 | 5.335 |
| test | 2.499 | 1.346 | 1.153 | 5.442 |

Audit không tìm thấy exact duplicate hoặc cross-split duplicate. Manifest:
`E:\HomeAssistantPi4\processed\coco-person-v1\manifest.json`, SHA-256
`e03c62e8e34e44556495db097243eb596a3736a49bb23cde4a3e1b96fe6d89c6`.

Index tạm `E:\HomeAssistantPi4\datasets\indoor-v1` đã compose từ Home-fire,
Indoor-FS và COCO person:

| Split | Images |
| --- | ---: |
| train | 14.900 |
| val | 4.301 |
| test | 4.299 |

Manifest index có SHA-256
`9548c53c111033c53213cdc9b2a37e6ee41ac7f20fc46e9cae668918bd876d68`.

## Person annotation gate

YOLO26n COCO pretrained, SHA-256
`9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef`,
đã quét toàn bộ 11.500 ảnh smoke/fire tại confidence 0,20 và input 640:

- 2.360 ảnh có candidate, tổng cộng 3.887 person boxes.
- 898 ảnh chỉ có candidate confidence từ 0,65 trở lên; đây vẫn là nhóm cần review,
  không phải auto-accept.
- 1.462 ảnh có ít nhất một candidate cần manual review.
- Phân bố: train 1.628, val 433, test 299 ảnh có candidate.

Audit v2 thay thế semantics `auto_accept` không an toàn của v1. Artifacts chuẩn
nằm trong `E:\HomeAssistantPi4\reports\person-audit-v2`:

- `report.json` SHA-256
  `8de5e3726ea93e053a0625e69deb8c6ac93933f80da7c90507c644fc6bc1c187`.
- `candidates.jsonl` SHA-256
  `15007ff76ade5ecfa8acf42f33c568f4742863754888eb66c6c800134cdf5e1d`.

Review bundle nằm trong `E:\HomeAssistantPi4\reviews\person-audit-v2`, gồm 57
trang high-confidence review và 92 trang manual review, mỗi trang 16 ảnh.
`decisions.tsv` ban đầu có SHA-256
`2d52a9dec5ad1dcf2a1a84616fe91ce5a0c2998ea5fa97ec5be9906768da7937`.
Quan sát mẫu cho thấy false positive trên bàn tay/ngọn lửa ngay cả ở nhóm
confidence cao, vì vậy không candidate nào được tự động chấp nhận.

## Cross-model consensus review

YOLO26m COCO pretrained được dùng làm verifier offline trên laptop, không phải
model deployment. Checkpoint có SHA-256
`401cea9ab23ad19246ff7744859816bc599f350e93c9dd30367b6f0a0745d0b7`.
Với verifier confidence 0,10, strong confidence 0,50 và IoU 0,50:

- 914 ảnh thuộc `consensus_high_review`.
- 711 ảnh thuộc `consensus_mixed_review`.
- 735 ảnh thuộc `disagreement_review`.
- Verifier đề xuất thêm 1.477 box không có trong candidate YOLO26n.

Artifacts consensus nằm trong
`E:\HomeAssistantPi4\reports\person-consensus-v1`; `report.json` có SHA-256
`7ed6868f4daf0b32058d24628a76ab5784d5b80cf4d064fb309ead4f5cb0eb1e`,
`candidates.jsonl` có SHA-256
`f8590a84b21221d762bca948cfc2f2d5457c18f524f3f2e18e64eede6e0677d1`.

Review bundle chuẩn hiện tại là
`E:\HomeAssistantPi4\reviews\person-consensus-v3`: 149 contact sheets và 5.364
candidate rows. Mỗi box có `candidate_id` cùng integrity check riêng. File
`decisions.tsv` ban đầu có SHA-256
`c7ff8515edff54cf1d44a0ed8f5d0dade4de4edd935605675fc393289c993430`.
Validation gate đã được chạy trên file thật và từ chối tạo derivative vì cả 5.364
quyết định vẫn đang trống. Không có output dở dang được tạo.

## Pose verifier experiment

YOLO26m-pose, SHA-256
`2fbf16367022256a226035695c5c389384c6706e8bb8ab8fcd0e7976f05443c4`,
được thử với keypoint confidence 0,50 và yêu cầu ít nhất 4/17 keypoints:

- 657 ảnh `consensus_high_review`.
- 441 ảnh `consensus_mixed_review`.
- 1.262 ảnh `disagreement_review`.
- 915 pose-only boxes.

Report `E:\HomeAssistantPi4\reports\person-pose-consensus-v2\report.json` có
SHA-256 `eb1a987d56924d347db09de090ca5ab77603c3c1aa39a14f4fb3c6e83c2b0365`.
Candidate JSONL có SHA-256
`b682535d5406747da7b34f9fffac55c87f1e1f2e9c00477fdc3725968fbb5587`.
Kiểm tra contact sheet vẫn thấy pose hallucinate người/keypoints trên một số vùng
lửa. Vì vậy kết quả này chỉ dùng để ưu tiên review, không thay thế canonical
consensus v3 và không tự động tạo quyết định.

Source labels chưa bị sửa. `indoor-v1` hiện là index kiểm kê, **chưa phải corpus
được phép train**.

## Thay đổi chiến lược ngày 2026-09-30

Review 5.364 person candidate không còn là gate chính. Project chuyển sang ưu
tiên một dataset đã gắn đầy đủ `smoke/fire/person`, bắt đầu với Fire Smoke and
Human Detector v32. Pipeline review và các artifacts hiện có được giữ làm bằng
chứng về partial-label conflict và làm fallback, không bị xóa.

Gate tiếp theo là tải nguồn joint dataset vào ổ E, chuẩn hóa bằng
`indoor-prepare-joint`, audit cấu trúc/duplicate, rồi spot-check một mẫu phân tầng.
Chi tiết tại [Joint dataset intake](JOINT_DATASET_INTAKE.md).
