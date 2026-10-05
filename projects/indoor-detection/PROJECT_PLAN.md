# Kế hoạch hoàn thành Indoor Detection

Ngày cập nhật: **2026-10-05**. Agent cập nhật: **OpenAI Codex**.
Owner hiện tại: **OpenAI Codex**. Task kỹ thuật: **IN_PROGRESS**.

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
| P1 | Đánh giá nguồn bổ sung, review box và chốt can thiệp | IN_PROGRESS | Can thiệp dữ liệu hoặc sampling có provenance và data gate đạt |
| P2 | Fine-tune có kiểm soát | PLANNED | Run mới hoàn tất, checkpoint/log/config truy vết được |
| P3 | Calibration, quality gate và khóa ứng viên | PLANNED | Cả ba class đạt gate ở đúng resolution, test dùng đúng protocol |
| P4 | Export NCNN và kiểm tra tương đương | PLANNED | Artifact, preprocessing, output và chất lượng sau export được kiểm tra |
| P5 | Benchmark và camera trên Pi thật | BLOCKED | Có phần cứng, đo performance/latency/soak và kiểm tra miền thật |
| P6 | Đóng gói vận hành và nghiệm thu | PLANNED | Hướng dẫn tái lập, cấu hình phát hành và bàn giao đầy đủ |

**Còn 6 công đoạn lớn P1–P6**, trong đó P1 đang làm. P2–P3 có thể cần lặp
nếu chưa đạt chất lượng; đây không phải sáu lần chạy cố định hay phần trăm hoàn thành.
P5 bị chặn bởi phần cứng. Có thể chuẩn bị tài liệu P6 trước, nhưng chưa nghiệm thu
deployment đầy đủ nếu P5 chưa có kết quả.

### Bằng chứng hiện tại

- Dataset: `E:\HomeAssistantPi4\processed\indoor-partial-joint-v2\dataset.yaml`.
  14.900 train / 4.301 validation / 4.297 test; tổng 23.498 ảnh.
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
  ảnh qua prefilter không body-ignore. Chọn tiến tới labelled pilot, chưa đạt data
  gate. Xem [assessment](docs/CROWDHUMAN_ASSESSMENT.md); các nguồn khác còn metadata.
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
- [ ] Review nhãn vbox/fbox của pilot, ignore/completeness và scale/pose. Chốt convention;
  audit duplicate với corpus/holdout trước quyết định chuyển đổi.
- [ ] Chọn nguồn bằng bằng chứng; ghi provenance/metadata thiếu. Nếu bổ sung data,
  tạo derivative mới, scope person, giữ rehearsal hazard; kiểm tra augmentation
  families/video sessions và exact/near duplicate với corpus/holdout hiện tại.
- [ ] Chốt hướng bổ sung dữ liệu, sampling có review hoặc kết hợp có lý do trước P2.
  Các checklist sampling bên dưới chỉ áp dụng nếu chọn hướng sampling.
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
- [ ] Giữ train index unique; không nhân dòng trong `train.txt` để né duplicate gate.
- [ ] Đối chiếu hash ảnh/nhãn với manifest của can thiệp và giữ membership validation/test.
- [ ] Audit structure, duplicate/conflict, class distribution và annotation của
  can thiệp; ghi rõ giới hạn của near-duplicate/domain audit nếu có.
- [ ] Ghi quyết định data gate cho can thiệp; chỉ khi đạt mới mở P2.

**Đầu ra:** quyết định nguồn và can thiệp; review box/sampling nếu áp dụng,
manifest can thiệp và báo cáo data gate trên E:; config/code và quyết định trong Git.

### P2 — Fine-tune và theo dõi run mới

- [ ] Chọn checkpoint khởi tạo có lý do từ control/validation hiện có; v2/v4
  đều chưa được duyệt deployment. Không mặc định đổi initialization là đủ sửa gate.
- [ ] Tạo config/run mới: ghi input size, seed, optimizer, LR, epochs/patience,
   sampler version nếu dùng, dataset/manifest hash và checkpoint đầu vào.
- [ ] Xác minh data gate P1 và môi trường GPU trước khi chạy.
- [ ] Chạy một thí nghiệm có giới hạn; giữ class masking và tắt augmentation trộn ảnh.
- [ ] Ghi log đầy đủ, kiểm tra lỗi/NMS warnings và kết quả inline/final validator.
- [ ] Lưu checkpoint/hash và báo cáo thời gian, trạng thái hoàn tất/dừng.

**Đầu ra:** run/checkpoint riêng trên E:, config và báo cáo quyết định trong Git.
Không ghi đè v1–v4; không tự mở hàng loạt thử nghiệm khi một run thất bại.

### P3 — Quality gate và khóa ứng viên

- [ ] Calibrate riêng từng class trên validation ở đúng input size deployment.
- [ ] Chấm bằng class-scoped validator; error matching dùng square preprocessing
  nhất quán (`rect=False`), warmup trước ảnh được chấm và protocol được ghi rõ.
- [ ] Báo cáo per-class P/R/F1, mAP50/mAP50-95, confusion, small-person recall,
  negative-image false alarms và source/domain slices có giới hạn rõ.
- [ ] Kiểm tra cả smoke/fire khi cải thiện person; không chọn bằng aggregate mAP alone.
- [ ] Đạt các ngưỡng hiện hành trong [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md):
  smoke recall >= 0,90; fire recall >= 0,90; person validation F1 >= 0,65
  **và** recall >= 0,60 ở đúng resolution. Báo cáo calibration và explicit matching
  riêng, ghi protocol quyết định; không chọn con số thuận lợi giữa các protocol.
- [ ] Kiểm tra smoke không giảm recall quá 0,03 so với baseline trên **cùng** test
  slice/protocol. Nếu không có slice tương đương, ghi chưa thể xác minh; không so
  hai metric khác dataset và tuyên bố gate đạt.
- [ ] Nếu chưa đạt: ghi failure, quay về P1/P2 theo bằng chứng; không hạ gate
  hoặc đổi kiến trúc chỉ để có artifact phát hành.
- [ ] Khi validation đạt, khóa checkpoint hash, thresholds, resolution và preprocessing
  trước đánh giá test cuối. Test v2 đã dùng trước đây: công khai lịch sử đó, không
  gọi nó là holdout hoàn toàn chưa từng thấy; không mở lại để chọn epoch/threshold.
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
2. Tiếp tục **P1: labelled CrowdHuman pilot** theo CROWDHUMAN_ASSESSMENT.md và
   PERSON_DATA_STRATEGY.md. Annotation prefilter/preview không phải data gate.
   60 ảnh gốc/621 box đã ghép; gallery trên E: tại
   `reports/crowdhuman-pilot-box-review-v1`. Notes 3/60 còn tạm;
   tiếp tục review 04–60 và chốt convention trước conversion/near-duplicate gate.
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
