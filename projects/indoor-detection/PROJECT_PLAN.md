# Kế hoạch hoàn thành Indoor Detection

Ngày cập nhật: **2026-10-06**. Agent cập nhật: **OpenAI Codex**.
Owner hiện tại: **OpenAI Codex**. **Resolution/baseline stage1 COMPLETED; P1c IN_PROGRESS**. P1b preparation hoàn tất; **v6 training/evaluation COMPLETED; person512 FAIL, person768 PASS**.
V5 đã train đủ 12 epoch và đánh giá validation. Person vẫn FAIL; test/export đóng.
V6, sáu cấu hình đánh giá và exact hazard calibration đã hoàn tất. Một lượt test
cuối cố định đang chạy theo protocol đã khóa; không train mới hoặc export.
Ứng viên validation768 đạt ba class: smoke/fireR .900932/.900158;personF1/R
.652182/.621743. Readiness/protocol test cuối và smoke regression cùng slice đã
PASS/freeze; xem V6_FINAL_TEST.md, lịch60 epoch tạm hoãn. P1b đã audit pool, freeze/tải 60 ảnh/1.430 box, trong đó
615 box nhỏ (43,01%). Review/duplicate đã xong: 30 ACCEPT/30 EXCLUDE, phần nhận
có 189/397 box nhỏ (47,61%). CrowdHuman expansion hoãn; pilot COCO train chưa
dùng đã tải/review: 60 ảnh/415 box,342 nhỏ; nhận24/loại36, accepted127/156 nhỏ
(81,41%). Exact/near screening không có match/candidate. Không mở expansion tự
động do vấn đề annotation/completeness/representation. Bước tiếp theo: đánh giá
reviewed-only proposal54 ảnh (COCO24+CrowdHuman30) đã freeze, cross-pilot duplicate
không có match/candidate. Đã chốt policy, chuyển54 ảnh/553 box và tạo joint v4
24.100 ảnh; full data gate PASS_WITH_LIMITATIONS. Config/preflight v6 đã xong;
**đã được người dùng cho phép và khởi chạy lúc19:13 ngày2026-10-06**. Xem [V6 preparation](docs/V6_TRAINING_PREPARATION.md).
Xem [Small-person intake](docs/SMALL_PERSON_INTAKE.md) và [V5 decision](docs/V5_EVALUATION_DECISION.md).

Đây là checklist tổng thể để các agent tiếp tục project. `AGENTS.md` quy định
cách làm việc; `CHANGES.log` ghi lịch sử, kết quả thực chạy và bàn giao từng phiên.
Khi có khác biệt về trạng thái, kiểm tra entry mới nhất trong `CHANGES.log` và Git,
rồi cập nhật kế hoạch này theo bằng chứng. Không sửa lịch sử để khớp kế hoạch.

## 1. Đích đến và các quyết định đã chốt

- Một YOLO26n, một lượt inference cho `smoke=0`, `fire=1`, `person=2`.
- Phát triển/train trên Windows; triển khai NCNN trên Raspberry Pi 4 4 GB.
- Camera mục tiêu: Raspberry Pi Camera Module 3 Wide, IMX708 ~12 MP, autofocus;
  FoV 120° diagonal / 102° horizontal / 67° vertical. Chưa chốt vị trí/khoảng cách
  lắp đặt; chưa xác nhận phần cứng sẵn sàng để benchmark. Xem
  [Person data strategy](docs/PERSON_DATA_STRATEGY.md) và nguồn thông số chính thức.
- Dùng confidence và temporal policy riêng cho mỗi class; smoke không bị loại
  chỉ vì ảnh mờ. Xuất annotated media và event JSONL schema v2.
- Có thể ghép nhiều nguồn partial-label vào **một model** bằng class-masked
  training/validation. Mỗi ảnh phải có scope rõ; class ngoài scope là chưa biết,
  không phải negative. Giữ augmentation trộn ảnh bằng 0.
- Ưu tiên dataset đã có nhãn phù hợp. Ghi provenance, license hoặc tình trạng
  thiếu thông tin; không cần đợi một dataset “hoàn hảo”. Không suy ra quyền sử
  dụng đã xác nhận nếu metadata còn thiếu.
- Corpus hiện mixed-domain: indoor/outdoor/staged/synthetic. Không gọi metric
  tổng hợp là benchmark indoor thuần. Đánh giá miền mục tiêu phải tách riêng.
- Dữ liệu, run, checkpoint, gallery và report lớn ở `E:\HomeAssistantPi4`.
  Venv ở `projects/indoor-detection/.venv` trên C:, không đặt trên E:.
- Không đọc/in/commit `projects/.env`. Giữ nguyên nguồn dữ liệu và work chưa commit.
- Chưa làm camera thật hoặc benchmark Pi thật cho đến khi người dùng có phần cứng.
  Không đổi sang nhiều model nếu chưa được người dùng cho phép.

## 2. Tổng quan tiến độ

| ID | Công đoạn | Trạng thái | Điều kiện kết thúc |
|---|---|---|---|
| P0 | Stack, downloader, chuẩn hóa và baseline | COMPLETED | Có scoped corpus đã audit và báo cáo v1–v4 |
| P1 | Đánh giá nguồn bổ sung, review box và chốt can thiệp | COMPLETED | Joint v3 data gate PASS_WITH_LIMITATIONS, đã khóa evidence |
| P2 | Fine-tune có kiểm soát | COMPLETED | V6 đủ12 epoch, best10; chưa có run tiếp theo |
| P3 | Calibration, quality gate và khóa ứng viên | IN_PROGRESS | Validation768 PASS; ứng viên/ngưỡng đã khóa, một lượt test cuối đang chạy; export đóng |
| P4 | Export NCNN và kiểm tra tương đương | PLANNED | Artifact, preprocessing, output và chất lượng sau export được kiểm tra |
| P5 | Benchmark và camera trên Pi thật | BLOCKED | Có phần cứng, đo performance/latency/soak và kiểm tra miền thật |
| P6 | Đóng gói vận hành và nghiệm thu | PLANNED | Hướng dẫn tái lập, cấu hình phát hành và bàn giao đầy đủ |

**Còn 4 công đoạn đích P3–P6**, cùng vòng can thiệp person quay lại P1/P2.
P1/P2 đã hoàn tất cho v5 nhưng P3 chưa đạt. Các vòng train không có số lần cố định
hay phần trăm hoàn thành đảm bảo trước khi đạt quality gate.
P5 bị chặn bởi phần cứng. Có thể chuẩn bị tài liệu P6 trước, nhưng chưa nghiệm thu
deployment đầy đủ nếu P5 chưa có kết quả.

### Bằng chứng hiện tại

- V6 đã hoàn tất12 epoch, best10; joint v4 gồm24.100 ảnh. Scoped square512
  person F1/recall0.6375/0.5618 FAIL; small recall0.2729,negative alarms12.56%.
  Smoke/fire recall0.9138/0.9049 PASS. Test/export đóng; không còn job.
  Xem [V6 decision](docs/V6_EVALUATION_DECISION.md). Next: chuẩn bị một đề xuất
  lịch60 epoch/patience15 trên cùngjoint v4,khởi tạo v2; chưa config/run/launch.

**Bằng chứng v5 và các vòng trước (lịch sử):**

- Dataset mới: `E:\HomeAssistantPi4\processed\indoor-partial-joint-v3\dataset.yaml`.
  15.448 train / 4.301 validation / 4.297 test; tổng 24.046 ảnh, thêm 548 ảnh
  person/5.810 box từ pilot + expansion. Base v2 và holdout giữ nguyên.
- Gate/preflight: `E:/HomeAssistantPi4/reports/indoor-partial-joint-v3-audit`:
  data-gate.json PASS_WITH_LIMITATIONS; train-readiness.json là snapshot trước train,
  không phải trạng thái execution hiện tại. Verifier sẽ từ chối run đã tồn tại.
  Config `configs/train_indoor_v5_512.yaml`, checkpoint v2, 512 px/max 12 epoch,
  seed 42, LR 0.00015. V5 đã chạy đủ 12 epoch, best epoch 7; batch 18/workers 2
  sau resume vì RAM. Explicit person F1/recall 0.6415/0.5717 FAIL; smoke/fire
  recall 0.9172/0.9073 PASS. Không test/export. Báo cáo:
  `E:/HomeAssistantPi4/reports/indoor-yolo26n-v5-evaluation` và V5 decision.
- Automated data gate đạt; visual gate `PASS_WITH_LIMITATIONS` về mixed-domain.
  Dataset v32 đã tải/chuẩn hóa/audit nhưng không phải corpus deployment được chọn.
- Package detector, class scopes, masked loss/validator, policy và JSONL đã có.
- V4 hoàn tất 12 epoch ở 512 px; person calibration F1/recall
  **0,6356/0,5625**, vẫn dưới gate. V2 control 512 cũng không đạt.
- Đã mine 7.000 ảnh training có person scope, review 105 ảnh gốc: nhận
  56 positive + 35 negative; 14 ảnh bị loại khỏi phần tăng trọng số.
- Manifest review checks đạt; **`training_allowed=false`**. Review box có notes
  tạm cho 42/56 ảnh, chưa hoàn tất hoặc duyệt tăng trọng số. Không xóa 14 ảnh khỏi
  dataset nguồn. Sampling chưa triển khai và không còn là bước bắt buộc.
- Người dùng cho phép chọn nguồn person phù hợp, kể cả outdoor/public area;
  dataset Leo Ueno chỉ tham khảo. Ưu tiên khảo sát nguồn mới trước chọn can thiệp;
  CrowdHuman đã audit annotation train và xem 10 domain previews; 2.875/15.000
  ảnh qua prefilter không body-ignore. Pilot 60 đã chốt 49 ACCEPT/11 EXCLUDE;
  derivative 49 ảnh/507 box đã chuyển, freeze expansion 500/spot-check 30 theo seed.
  Expansion đã tải đủ 500 ảnh/5.313 box, decode/geometry/exact checks đạt; 22
  near-hash candidates đều khác cảnh sau review. Review 30: nhận 29/loại 1 ảnh
  đồ họa; không thấy lỗi box hệ thống mới. 499 ảnh/5.303 box chuyển YOLO, 470 ảnh
  chỉ auto-screen, không claim từng ảnh đã review. Joint v3 gate đã mở với giới hạn;
  quality/export gate vẫn đóng. Xem [V5 preparation](docs/V5_TRAINING_PREPARATION.md).
- Checkpoint/metric lịch sử: [V4 decision](docs/V4_EVALUATION_DECISION.md),
  [V3 decision](docs/V3_EVALUATION_DECISION.md), [V2 decision](docs/V2_EVALUATION_DECISION.md).
  Queue lịch sử vẫn `REVIEW_REQUIRED`; quyết định nằm trong file review riêng.

## 3. Checklist thực thi

### P1 — Review annotation và chốt can thiệp dữ liệu

- [x] Ghi nhận Camera Module 3 Wide và quyết định cho phép nguồn person outdoor.
- [x] Lập shortlist, tiêu chí và protocol tại
  [PERSON_DATA_STRATEGY.md](docs/PERSON_DATA_STRATEGY.md); chưa chọn/tải nguồn mới.
- [x] Khảo sát CrowdHuman annotation/access policy, audit 15.000 train annotation
  records và review 10 domain previews; so sơ bộ semantics với Roboflow tham khảo.
  Preview chưa ghép annotation nên không thay thế visual box gate.
- [x] Freeze 60 IDs seed 42 trong 2.875 ứng viên; tải đúng training image members,
  ghép annotation và tạo gallery vbox/fbox. Exact SHA-256 overlap với 23.498 ảnh
  hiện có đạt; giữ nguyên split fingerprints. Chưa đạt visual/near-duplicate gate.
- [x] Review đủ 60 pilot và crop trường hợp nghi lỗi; nhận 49/loại 11, chọn vbox
  clipped. Chuyển 49 ảnh/507 box sang YOLO person=2; exact/near screening và
  adjudication pilot hoàn tất với giới hạn dHash. Chưa duyệt toàn bộ nguồn.
- [x] Tải bounded expansion 500 IDs seed 43 đã freeze từ 2.334 ứng viên sau lọc
  head-overlap; decode/geometry/exact checks toàn bộ, near-screen/adjudication
  với corpus + 49 pilot và kiểm tra split giữ nguyên. Chưa duyệt source/joint gate.
- [x] Review 30 IDs seed 44 và flagged cases, không bắt buộc xem cả 500.
  Ghi quyết định nguồn trước compose; dừng nếu có lỗi nhãn hệ thống mới.
- [x] Chọn nguồn bằng bằng chứng; ghi provenance/metadata thiếu. Nếu bổ sung data,
  tạo derivative mới, scope person, giữ rehearsal hazard; kiểm tra augmentation
  families/video sessions và exact/near duplicate với corpus/holdout hiện tại.
- [x] Chốt hướng bổ sung dữ liệu, sampling có review hoặc kết hợp có lý do trước P2.
  Các checklist sampling bên dưới chỉ áp dụng nếu chọn hướng sampling.

**Can thiệp đã chọn: bổ sung CrowdHuman, uniform sampling hiện có. Checklist
box-review/reweighting/sampler cũ dưới đây không áp dụng cho v5, không chặn P1.**
- [x] Mining chỉ trên train, không dùng ảnh lỗi validation/test làm training examples.
- [x] Review 105 ảnh gốc và lưu quyết định riêng.
- [x] Freeze 91 ảnh được nhận: hash ảnh/nhãn, scope, split fingerprints;
  kiểm tra label syntax và exact duplicate với holdout.
- [ ] Review box của 56 ảnh positive ở độ phân giải gốc; ghi rõ tiny/occluded,
  annotation ambiguity và genuine miss. Prediction không phải ground truth.
- [ ] Lưu kết quả review box và provenance riêng trên E:. Nếu cần sửa annotation,
  tạo derivative có review; không sửa nguồn âm thầm.
- [ ] Chốt sampling plan trước run: image weights/cap, seed, epoch size, phạm vi
  ảnh được tăng trọng số và cách giữ đầy đủ rehearsal smoke/fire.
- [ ] Triển khai và test sampling với class-scoped trainer hiện có; kiểm tra
  tái lập, mapping weight đúng ảnh, scope không mất và validation không bị reweight.
  Sampler hiện **chưa được triển khai**; không coi manifest là config training.
- [x] Giữ train index unique; không nhân dòng trong `train.txt` để né duplicate gate.
- [x] Đối chiếu hash ảnh/nhãn với manifest của can thiệp và giữ membership validation/test.
- [x] Audit structure, duplicate/conflict, class distribution và annotation của
  can thiệp; ghi rõ giới hạn của near-duplicate/domain audit nếu có.
- [x] Ghi quyết định data gate cho can thiệp; chỉ khi đạt mới mở P2.

**Đầu ra:** quyết định nguồn và can thiệp; review box/sampling nếu áp dụng,
manifest can thiệp và báo cáo data gate trên E:; config/code và quyết định trong Git.

### P1b — Vòng tiếp theo sau v5 (READY_FOR_REVIEW; v6 train/evaluation xong)

- [x] Audit annotation pool còn lại theo kích thước box, mật độ và scope; ưu tiên
  dữ liệu đã gắn nhãn small/occluded person, không lấy error ảnh holdout vào train.
- [x] Freeze bounded IDs/size strata/seed và visual stop condition trước download.
  Pilot 60 seed45/quotas30-20-10 đã tải và decode; 615/1.430 box nhỏ. Proxy trước
  tải không phải kích thước ảnh thật. Xem SMALL_PERSON_INTAKE.md cho paths/hashes.
- [x] Review toàn bộ 60 pilot, exact/near duplicate với joint v3; tính coverage
  sau loại ảnh. Không mở expansion nếu accepted small-box share <30% hoặc lỗi
  annotation hệ thống mới. Đã xem60 gallery/21 crop, nhận30/loại30; accepted small
  share47,61%. Zero exact/near candidates với24.046 ảnh. Expansion hoãn do các
  assignment dày/partial còn mơ hồ; không claim mọi nhãn bị loại đều sai.
- [x] Audit metadata nguồn COCO train chưa dùng; freeze pilot60 seed46,
  30 ảnh3-6 người +30 ảnh7-15 người, 342/415 box nhỏ theo metadata trước tải.
- [x] Acquire/review pilot COCO đã freeze; kiểm tra actual size, scope/duplicate
  và chốt no automatic expansion. 60 gallery/25 crop; nhận24/loại36,127/156 nhỏ.
  Exact/near với24.046 ảnh không có match/candidate; nguồn/joint cũ giữ nguyên.
- [x] Freeze reviewed-only proposal54 (COCO24+CrowdHuman30); cross-pilot all60COCO
  x30acceptedCrowdHuman exact/near không có match/candidate. Artifact/hash trên E:.
- [x] Chốt provenance/annotation policy; separate derivative decision cho đúng54
  ảnh, giữ convention COCO bbox/CrowdHuman vbox. Không duyệt toàn bộ source.
- [x] Tạo derivative mới, giữ rehearsal hazard và holdout; joint v4 automated,
  conversion parity và inherited/new visual data gate PASS_WITH_LIMITATIONS.
- [x] Chốt run v6 với initialization/retention rationale, resource config và
  read-only readiness PASS. Người dùng đã cho phép; v6 đã hoàn tất.
  Không auto nhiều retry hoặc hạ gate. Xem V5 decision cho coverage census:
  bộ bổ sung chỉ có 701/5,810 box nhỏ (<1% diện tích), COCO có 10,846/23,611.

### P1c — Resolution, baseline và phạm vi person (IN_PROGRESS)

- [x] Khóa protocol và hash v6/pretrained/dataset; giữ gate/scope/holdout.
- [x] Ánh xạ pretrained person0->canonical2 chỉ cho đánh giá; tests đạt.
- [x] Khởi chạy chuỗi6 cấu hình square; revalidate512 để thống nhất calibration.
- [x] Hoàn tất v6/pretrained tại512/640/768, kiểm tra log/hashes (81 artifact bindings).
- [x] So sánh full metrics, fixed512/native height bins, tiny/negative/hazard và
  Windows batch1/resource reports; không tuyên bố Pi performance.
- [x] Người dùng chốt ưu tiên người trong phòng/khu vực cửa; không cần rất xa ngoài cửa sổ.
- [ ] Chốt numeric minimum/ROI/khoảng cách bằng camera thật; dự kiến lắp cao~4m
  trở lên, exact height/tilt/distance chờ triển khai thực tế.
  Chưa bỏ tiny labels hoặc đổi gate để đạt metric.
- [x] Chọn can thiệp tiếp theo: calibration smoke/fire exact square ở768 trước train mới.
- [x] Freeze protocol/output riêng; giữ checkpoint/person threshold, tìm highest
  threshold đạt empirical recall >=.90, báo precision/negative alarms; không hạ gate.
- [x] Hoàn tất calibration/confirmation tại reports/indoor-v6-768-exact-hazard-calibration-v2;
  v1 lỗi check zero-width predictions đã được chẩn đoán, giữ cached smoke và báo cáo cũ.
  Test/export vẫn đóng. Xem [Resolution protocol](docs/RESOLUTION_BASELINE_EVALUATION.md).
  Kết quả: validation gates PASS; xem [Exact calibration](docs/V6_EXACT_HAZARD_CALIBRATION.md).

### P2 — Fine-tune và theo dõi run mới (v5/v6 COMPLETED)

- [x] Chọn checkpoint khởi tạo có lý do từ control/validation hiện có; v2/v4
  đều chưa được duyệt deployment. Không mặc định đổi initialization là đủ sửa gate.
- [x] Tạo config/run mới: ghi input size, seed, optimizer, LR, epochs/patience,
   sampler version nếu dùng, dataset/manifest hash và checkpoint đầu vào.
- [x] Xác minh data gate P1 và môi trường GPU trước khi chạy.
- [x] Chạy một thí nghiệm có giới hạn; giữ class masking và tắt augmentation trộn ảnh.
- [x] V6: đã kiểm tra log/lỗi và inline/final validator; đủ12 epoch,exit0.
- [x] V6: đã lưu checkpoint/hash/thời gian và quyết định NO_RELEASE.
- [ ] Vòng tiếp: chỉ chọn lịch/resolution fine-tune sau P1c; đề xuất60 epoch
  tạm hoãn. Chưa tự khởi chạy hoặc resume v6.

**Đầu ra:** run/checkpoint riêng trên E:, config và báo cáo quyết định trong Git.
Không ghi đè v1–v4; không tự mở hàng loạt thử nghiệm khi một run thất bại.

### P3 — Quality gate và khóa ứng viên

- [x] Calibrate riêng từng class trên validation ở đúng input size deployment.
- [x] Chấm bằng class-scoped validator; error matching dùng square preprocessing
  nhất quán (`rect=False`), warmup trước ảnh được chấm và protocol được ghi rõ.
- [x] Báo cáo per-class P/R/F1, mAP50/mAP50-95, confusion, small-person recall,
  negative-image false alarms và source/domain slices có giới hạn rõ.
- [x] Kiểm tra cả smoke/fire khi cải thiện person; không chọn bằng aggregate mAP alone.
- [x] Đạt các ngưỡng validation hiện hành trong [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md):
  smoke recall >= 0,90; fire recall >= 0,90; person validation F1 >= 0,65
  **và** recall >= 0,60 ở đúng resolution. Báo cáo calibration và explicit matching
  riêng, ghi protocol quyết định; không chọn con số thuận lợi giữa các protocol.
  V6-768 sau calibration empirical đã PASS; chưa chứng minh test/camera/Pi.
- [ ] Kiểm tra smoke không giảm recall quá 0,03 so với baseline trên **cùng** test
  slice/protocol. Nếu không có slice tương đương, ghi chưa thể xác minh; không so
  hai metric khác dataset và tuyên bố gate đạt.
- [x] Nếu chưa đạt: ghi failure, quay về P1/P2 theo bằng chứng; không hạ gate
  hoặc đổi kiến trúc chỉ để có artifact phát hành.
- [x] Khi validation đạt, khóa checkpoint hash, thresholds, resolution và preprocessing
  trước đánh giá test cuối. Test v2 đã dùng trước đây: công khai lịch sử đó, không
  gọi nó là holdout hoàn toàn chưa từng thấy; không mở lại để chọn epoch/threshold.
- [x] Readiness:1.798 smoke test khớp ảnh/nhãn test baseline, không overlap hash
  với train/val baseline;2 negative cũ ngoài membership hiện tại đã ghi rõ.
- [x] Freeze test protocol trước kết quả; mở một lượt test cố định theo yêu cầu
  tiếp tục của người dùng. Xem [Final test](docs/V6_FINAL_TEST.md); không launch lại.
- [ ] Đánh giá test theo protocol đã khóa và ghi quyết định release/no-release.
  Nếu kết quả buộc thiết kế lại, đóng ứng viên và lập protocol holdout cho vòng mới.

**Đầu ra:** model selection decision, checkpoint/threshold lock và quality reports.
NCNN cuối chỉ được mở khi quality gate đạt, không vì train đã chạy xong.

### P4 — Export NCNN và kiểm tra artifact

- [ ] Export từ checkpoint đã khóa ở đúng resolution; lưu tool/package versions,
  args, artifact/hash, mapping class và preprocessing contract.
- [ ] Kiểm tra backend load và một inference pass cho cả ba class, batch size 1.
- [ ] Định nghĩa tolerance trước khi so PyTorch/NCNN: class, box, confidence,
  postprocessing và metric drift; kiểm tra trên mẫu cố định và validation phù hợp.
- [ ] Kiểm tra event policy/JSONL/annotated output với artifact export.
- [ ] Nếu parity hoặc quality giảm không đạt: giữ artifact experimental, ghi nguyên
  nhân và quay lại bước phù hợp. Không âm thầm đổi threshold bằng test set.

**Đầu ra:** NCNN artifact trên E:, báo cáo parity/quality và hướng dẫn tái lập export.
Kết quả trên Windows chưa chứng minh Pi đạt latency/RAM.

### P5 — Pi 4 và camera thật (chờ người dùng cung cấp phần cứng)

- [ ] Chuẩn bị Raspberry Pi OS 64-bit và môi trường NCNN theo stack đã chọn.
- [ ] Đo batch 1: artifact ưu tiên < 25 MB, RSS mục tiêu < 600 MB, >= 3 FPS.
- [ ] Đo detection-to-alert: fire <= 1 giây, smoke <= 2 giây; tách inference time
  và độ trễ do capture/temporal confirmation. Khóa ngưỡng performance sau đo thật.
- [ ] Tích hợp nguồn camera; kiểm tra mất kết nối, frame lỗi, shutdown và recovery.
- [ ] Với Camera Module 3 Wide: chốt capture mode/crop, focus/exposure và aspect
  ratio; đo người ở xa/mép ảnh sau resize, low light và lens distortion thực tế.
- [ ] Kiểm tra người/negative indoor thật và low light, blur, steam, reflection,
  poster/TV. Ghi phương pháp kiểm tra thực địa; không coi COCO là bằng chứng indoor.
- [ ] Soak test 8 giờ: không crash, không tăng RAM liên tục; lưu log trên storage
  runtime phù hợp và chuyển report lớn về E: khi tổng hợp ở Windows.
- [ ] Chốt resolution/performance và quyết định có cần quay lại P2–P4.

**Đầu ra:** hardware benchmark, camera integration report và deployment decision.
Không đánh dấu PASS bằng benchmark CPU Windows hay thời gian GPU training.

### P6 — Đóng gói và bàn giao

- [ ] Hoàn thiện config phát hành: model/hash, class map, thresholds, temporal policy,
  nguồn ảnh, output paths và cách khởi động/dừng theo runtime thực đã kiểm tra.
- [ ] Kiểm tra chức năng ảnh/video, JSONL schema v2, blur flag, `person_present`,
  `hazard_confirmed`, `occupied_hazard`; reuse code hiện có, sửa theo test cụ thể.
- [ ] Viết hướng dẫn Windows dev và Pi runtime, install/export/run/benchmark,
  troubleshoot, provenance và giới hạn sử dụng/miền đã xác minh.
- [ ] Tạo release manifest trỏ tới artifact lớn ngoài Git; không đưa weights/data
  hoặc secret vào repository.
- [ ] Chạy tests/lint; ghi Build/Typecheck là không áp dụng nếu chưa được cấu hình.
- [ ] Kiểm tra Git, cập nhật kế hoạch và append CHANGES; commit/push milestone.
- [ ] Chỉ đánh dấu project COMPLETED khi P1–P6 đạt và limitations được bàn giao.
  Nếu phần cứng chưa có, bàn giao phần mềm với P5 còn BLOCKED và project chưa hoàn tất.

## 4. Điểm bắt đầu cho agent tiếp theo

1. Đọc đầy đủ `AGENTS.md`, `CLAUDE.md`, entry mới nhất `CHANGES.log`, README và
   file này; chạy `git status`/`git log`. Xác định owner, giữ dirty work.
2. **V5 đã hoàn tất, person FAIL.** Đọc V5_EVALUATION_DECISION.md và bắt đầu P1b
   reviewed-only proposal tại SMALL_PERSON_INTAKE.md. CrowdHuman/COCO pilot review
   đã xong; expansion tự động đều đóng. COCO nhận24, CrowdHuman nhận30;
   cross-pilot/data gate đã đạt, derivative54/joint v4 đã tạo. Config/preflight v6
   đã PASS trước khi người dùng cho phép khởi chạy ngày2026-10-06.
   V6 COMPLETED: validation square512 person FAIL. Đọc V6_EVALUATION_DECISION.md
   và reports/indoor-yolo26n-v6-evaluation trên E:. Không còn job.
   Tiếp tục P1c: reports/indoor-resolution-baseline-square-v2 trên E: đã COMPLETED.
   Không còn job, không launch lại. Đọc RESOLUTION_BASELINE_EVALUATION.md và manifest.
   V6-768 person PASS nhưng smoke/fire FAIL; baseline person tốt hơn ở cả ba input.
   Exact hazard calibration v2 đã COMPLETED; validation-only candidate768 đạt ba class.
   Bước tiếp theo: chuẩn bị protocol test cuối/smoke regression cùng slice, giữ
   checkpoint/thresholds/preprocessing trong validation-candidate.json. Chưa chạy test.
   Đọc V6_EXACT_HAZARD_CALIBRATION.md; không rerun calibration hoặc train mới.
   Không resume/relaunch v6 hoặc tự mở series retry.
   Không lặp acquisition đã hoàn tất. Không resume run hoàn tất, không
   chạy lại config v5 hoặc verifier pre-run để bỏ qua target đã tồn tại. Không test
   hoặc export khi person gate chưa đạt. Không lặp intake artifact đã hoàn tất.
   Bằng chứng lịch sử **P1: labelled CrowdHuman pilot** tại CROWDHUMAN_ASSESSMENT.md và
   PERSON_DATA_STRATEGY.md. Annotation prefilter/preview không phải data gate.
   60 ảnh gốc/621 box đã ghép; gallery trên E: tại
   `reports/crowdhuman-pilot-box-review-v1`. Review đã chốt 49 ACCEPT/11 EXCLUDE,
   vbox clipped, near-hash candidate false positive. Derivative 49 ảnh/507 box tại
   `processed/crowdhuman-reviewed-pilot-v1`, đã được đưa vào training v5.
   Expansion 500 đã acquire/audit/review 30 frozen IDs; xem
   tại `reports/crowdhuman-expansion-500-review-v1/gallery/bundle.json` trên E:;
   22 near candidates đã adjudicate, không có overlap xác nhận. 499 đã chuyển,
   joint v3 đã audit với hazard rehearsal và scope, gate PASS_WITH_LIMITATIONS.
   Giữ tiến độ review box 42/56 và kiểm tra source annotation khi quay lại review;
   chọn can thiệp theo bằng chứng. Không bắt buộc sampling trước intake nguồn mới.
   Không chạy lại mining, không train/export ngay từ manifest hiện tại.
3. Đọc các artifact ở `E:\HomeAssistantPi4\reports\indoor-person-train-mining-v1`:
   `review-queue.json`, `review-results-v1.json`, `review-manifest-v1.json`.
   Hash chuẩn và command tái lập nằm ở CHANGES/README; dùng output mới khi tái lập.
4. Code liên quan: `src/indoor_detection/training_review.py`,
   `partial_label_training.py`, `scoped_dataset_audit.py`, `scoped_visual_gate.py`,
   `train.py`, `error_analysis.py`. Cấu hình v4 là tham chiếu, không phải run mới.
5. Kiểm tra dependencies và CLI hiện có trước viết code/lệnh; không đoán flag.
   Các path code/config trong mục này tính từ `projects/indoor-detection`.

### Hướng mở rộng sau scope hiện tại

- Người dùng đề xuất head/face model bổ sung nếu can thiệp person chưa đủ hiệu quả.
  Đây là fallback có điều kiện, chưa đổi kiến trúc hoặc quality gate. Phân biệt
  head/body boxes, presence fusion và person metric; cần so sánh lợi ích và tổng
  latency/RAM trên Pi trước quyết định. Xem PERSON_DATA_STRATEGY.md.
- Người dùng muốn fall detection sau khi project này hoàn tất. Lập task/video
  protocol riêng cho temporal/pose/tracking, phân biệt ngã với ngồi/nằm/cúi;
  chưa thêm vào điều kiện hoàn thành P1-P6 và chưa chọn model/framework.

### Quy tắc cập nhật kế hoạch sau mỗi milestone

- Đánh dấu `[x]` chỉ khi có bằng chứng; cập nhật status và ngày/agent ở đầu file.
- Append CHANGES: việc đã làm, unfinished/blockers, artifact paths/hashes,
  validation thực chạy, branch/commit, dirty files và lệnh tiếp theo.
- Khi có nhánh thử nghiệm mới, ghi mục tiêu và stop condition trước khi chạy;
  giữ checklist P1–P6 làm đích chung. Không xóa thử nghiệm thất bại khỏi lịch sử.
- Sau milestone, từ project chạy `.venv\Scripts\python.exe -m pytest` và
  `.venv\Scripts\python.exe -m ruff check .`, kiểm tra diff, commit/push các file
  đúng phạm vi. Windows temp ACL workaround dùng thư mục tạm mới khi cần;
  ghi rõ command/result, không reuse thư mục temp có dữ liệu cần giữ.
