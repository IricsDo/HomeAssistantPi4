# HomeAssistantPi4 workspace

Repository này chứa các project AI chạy tại nhà, phát triển trên Windows 11 và
hướng tới triển khai tiết kiệm tài nguyên trên Raspberry Pi 4 4 GB.

## Projects

- [Indoor Detection](projects/indoor-detection/README.md) -- project đang phát
  triển: một YOLO26n phát hiện `smoke`, `fire`, `person` trong nhà và export NCNN
  cho Pi 4.
- [Neko AI Voice Assistant](projects/ai-voice-assistant/README.md) -- prototype
  trợ lý giọng nói đã lưu trữ; trạng thái tại thời điểm tách project nằm trong
  [PROJECT_STATUS.md](projects/ai-voice-assistant/PROJECT_STATUS.md).

## Trạng thái hiện tại

**Đánh giá resolution/baseline COMPLETED**, đủ sáu cấu hình square 512/640/768.
V6-768 sau exact hazard calibration đạt ba gate validation: smoke/fire recall
.900932/.900158; person F1/recall .652182/.621743.
Test cuối đã hoàn tất: smoke/person PASS, **fire recall84,99% FAIL → NO_RELEASE**.
Regression smoke cùng slice PASS; chưa train mới, không còn job.
Xem [Protocol và checklist](projects/indoor-detection/docs/RESOLUTION_BASELINE_EVALUATION.md); log/status trên E:
`reports/indoor-resolution-baseline-square-v2`. Kết quả/ngưỡng mới tại
[Exact calibration](projects/indoor-detection/docs/V6_EXACT_HAZARD_CALIBRATION.md).
Protocol/readiness test cuối đã khóa; xem [Final test](projects/indoor-detection/docs/V6_FINAL_TEST.md).
Chẩn đoán fire trên train/validation đã hoàn tất: recall theo nguồn 83,95% và
91,90%; giảm threshold làm tăng đáng kể false positives. Xem
[Fire recovery](projects/indoor-detection/docs/FIRE_RECOVERY_PLAN.md). Đề xuất v7 ở 768, tối đa 12 epoch,
chưa chạy. Tiếp theo đánh giá nguồn cho
[holdout độc lập](projects/indoor-detection/docs/INDEPENDENT_HOLDOUT_PLAN.md) và readiness;
[Recent-source review](projects/indoor-detection/docs/RECENT_HOLDOUT_SOURCE_REVIEW.md): ưu tiên nguồn
trong 5 năm; hoãn FURG cũ. Zenodo2025 pilot không được nhận do cảnh trùng;
Detectium IoT đã tải/audit pilot12 cặp, chưa nhận vào holdout.
Class nguồn đã xác nhận là fire/flame; hoãn Detectium làm holdout chính do
thiếu phiên quay và coverage. Tiếp theo kiểm tra FASDD CV và SCOUT; xem
[Provenance decision](projects/indoor-detection/docs/DETECTIUM_PROVENANCE_DECISION.md).
Chưa có holdout admission; smoke/person và independence gate còn thiếu. Lịch 60 epoch vẫn hoãn, export đóng,
chưa phát hành. Camera dự kiến cao~4m trở lên;
ưu tiên người trong phòng/khu vực cửa, chưa chốt minimum size/ROI/góc chúc xuống.


Kế hoạch tổng thể và checklist cho agent tiếp theo:
[PROJECT_PLAN.md](projects/indoor-detection/PROJECT_PLAN.md).

V5 đã train đủ 12 epoch và đánh giá validation ở 512 px. **Person vẫn FAIL**:
explicit F1/recall 0,6415/0,5717; smoke/fire recall 0,9172/0,9073 đạt mục tiêu.
Test/export vẫn đóng; v6 đã hoàn tất và đánh giá validation, person vẫn FAIL.
Vòng bổ sung dữ liệu ưu tiên người nhỏ đã hoàn tất. Joint v3 trước đó có
24.046 ảnh, data gate PASS_WITH_LIMITATIONS. Xem
[V5 decision](projects/indoor-detection/docs/V5_EVALUATION_DECISION.md).
P1b đã audit pool và tải pilot 60 ảnh: 615/1.430 box nhỏ (43,01%). Review và
duplicate screening đã hoàn tất; xem
[Small-person intake](projects/indoor-detection/docs/SMALL_PERSON_INTAKE.md).
Review đã xong: nhận30/loại30, phần nhận có47,61% box nhỏ; duplicate screening
không có match/candidate. Expansion CrowdHuman hoãn do annotation mơ hồ; đã
review pilot COCO train60 ảnh: nhận24/loại36, phần nhận có81,41% box nhỏ;
exact/near screening không có match/candidate. Không mở expansion tự động.
Đã freeze đề xuất chỉ dùng54 ảnh đã review (COCO24+CrowdHuman30); cross-pilot
screening không có match/candidate. Đã chuyển54 ảnh/553 box và tạo joint v4:
24.100 ảnh, data gate PASS_WITH_LIMITATIONS, giữ nguyên holdout và rehearsal.
Config/preflight v6 đã đạt; người dùng cho phép khởi chạy ngày 2026-10-06.
**V6 đã hoàn tất 12 epoch**, 19:13–19:51 giờ Việt Nam; best epoch10.
Xem [V6 preparation](projects/indoor-detection/docs/V6_TRAINING_PREPARATION.md).
Trạng thái/log: `E:/HomeAssistantPi4/reports/indoor-partial-joint-v4-audit/`
`v6-execution-status.json`, `v6-training.stdout.log`, `v6-training.stderr.log`.
Không khởi chạy lại. Validation square512 đã xong: person F1/recall **0,6375/0,5618 FAIL**;
smoke/fire recall **0,9138/0,9049 PASS**. Không còn job; test/export đóng.
Báo cáo: `E:/HomeAssistantPi4/reports/indoor-yolo26n-v6-evaluation`.
Xem [V6 decision](projects/indoor-detection/docs/V6_EVALUATION_DECISION.md). Lịch60 epoch/patience15 là đề xuất lịch sử; ưu tiên đánh giá resolution/baseline.
Camera mục tiêu là Raspberry Pi Camera Module 3 Wide IMX708;
xem [chiến lược dữ liệu](projects/indoor-detection/docs/PERSON_DATA_STRATEGY.md).

Scoped joint dataset v2 gồm 23.498 ảnh đã đạt automated và visual data gate với
các giới hạn mixed-domain được ghi rõ. Baseline continuation YOLO26n v2 đã train
đủ 40 epoch và checkpoint `best.pt` được khóa bằng validation set.

| Split | mAP50 | mAP50-95 |
|---|---:|---:|
| validation | 0,846 | 0,565 |
| test | 0,818 | 0,535 |

Trên test, mAP50/mAP50-95 theo lớp là smoke `0,917/0,631`, fire
`0,868/0,547`, person `0,670/0,429`. Confidence smoke `0,249249` được chọn chỉ
từ validation để đạt recall 0,900; khi khóa trên test, precision/recall là
`0,840/0,893`.

Validation theo source đã hoàn tất bằng class-scoped validator. Hai source
hazard đạt mAP50 `0,937` (`indoor-fs-v2`) và `0,928`
(`indoor-home-fire-v2`); source COCO person đạt mAP50 `0,671`, recall `0,579`.
Tên source được dùng như provenance proxy; visual gate đã xác nhận corpus vẫn
có ảnh outdoor, staged và synthetic nên chưa được xem là benchmark indoor thuần.

V3 đã fine-tune đủ 20 epoch ở 416 px và cải thiện rõ hazard gate. Smoke đạt
P/R/F1 `0,770/0,911/0,835`, fire đạt `0,866/0,906/0,886`. Person vẫn là blocker:
F1/recall chỉ `0,616/0,518` ở 416, `0,634/0,575` ở 512 và `0,647/0,586` ở 640.
NCNN export vẫn bị khóa; test không được mở lại trong quyết định này.

- Dataset: `E:\HomeAssistantPi4\processed\indoor-partial-joint-v2`
- Run: `E:\HomeAssistantPi4\runs\indoor-detection\indoor_partial_joint_yolo26n_v3_416`
- Reports: `E:\HomeAssistantPi4\reports\indoor-yolo26n-v3-evaluation`

V4 đã hoàn tất 12 epoch ở 512 px. Person sau calibration đạt F1 `0,6356`,
recall `0,5625`; explicit error matching cho F1/recall `0,6292/0,5593`, nên
export vẫn bị khóa. Smoke/fire đạt recall mục tiêu trên validation.
Xem [V4 evaluation decision](projects/indoor-detection/docs/V4_EVALUATION_DECISION.md).
Reports: `E:\HomeAssistantPi4\reports\indoor-yolo26n-v4-evaluation`.

Bộ control v2 tại 512 px cũng không đạt person gate: explicit F1/recall
`0,6351/0,5432`. V4 tăng recall người nhỏ nhưng có nhiều false alarm hơn.
Mining lỗi trên 7.000 ảnh training có scope person đã xong. Hàng đợi 105 ảnh
tại `E:\HomeAssistantPi4\reports\indoor-person-train-mining-v1\review-queue.json`
đã được review ảnh gốc: 56 ảnh có người và 35 ảnh âm được nhận để chuẩn bị
sampling plan; 14 ảnh mơ hồ không được tăng trọng số. Manifest lưu hash ảnh,
nhãn và membership của các split. Review box vẫn dở; sampling chỉ là lựa chọn.
CrowdHuman pilot đã review đủ 60 ảnh: nhận 49, loại 11; chọn vbox và chuyển
49 ảnh/507 box sang YOLO. Exact/near duplicate screening không xác nhận overlap.
Đã tải đủ expansion 500 ảnh/5.313 box trên E:, kiểm tra decode/geometry và exact
overlap đạt. Đã xem 22 near-hash candidates, đều khác cảnh. Gallery 30 ảnh annotation
đã review: nhận 29/loại 1 ảnh đồ họa. Expansion chuyển 499 ảnh/5.303 box;
470 ảnh chỉ auto-screen. Joint v3 thêm 548 ảnh person, giữ nguyên holdout và mọi
hazard rehearsal, data gate đạt với giới hạn; v5 đã train nhưng chưa đạt person gate. Xem
[assessment](projects/indoor-detection/docs/CROWDHUMAN_ASSESSMENT.md).
Benchmark Pi 4 và camera thật chờ phần cứng.

## AI Agent Collaboration

This repository is designed to support collaborative development by multiple
AI coding agents, including Claude Code and OpenAI Codex.

### Instruction Files

| File | Purpose |
|---|---|
| `AGENTS.md` | Shared repository-wide rules for all AI coding agents |
| `CLAUDE.md` | Claude Code-specific instructions |
| `CHANGES.log` | Shared handover and agent-state log |
| `README.md` | Human-facing project documentation |

### Recommended Workflow

```text
Agent A
  |
  | implement
  v
validate
  |
  v
update CHANGES.log
  |
  v
handover
  |
  v
Agent B
  |
  | read AGENTS.md + CHANGES.log
  v
continue work
  |
  v
validate
```

`Git` remains the source of truth for the actual code history.
`CHANGES.log` is the coordination and handover state between agents.

## Development

```powershell
cd projects/indoor-detection
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Project hỗ trợ Python 3.12 đến 3.14. Máy hiện tại có Python 3.14. Large artifacts
được đặt tại `E:\HomeAssistantPi4` để không chiếm dung lượng ổ C và không được
commit.

## Project Structure

```text
HomeAssistantPi4/
├── AGENTS.md
├── CLAUDE.md
├── CHANGES.log
├── README.md
└── projects/
    ├── .env                         # local secret, ignored by Git
    ├── ai-voice-assistant/          # archived project
    └── indoor-detection/
        ├── configs/
        ├── docs/
        ├── models/
        ├── scripts/
        ├── src/indoor_detection/
        └── tests/
```

## Contributing

Before changing code:

1. Read `AGENTS.md`.
2. Read the latest entries in `CHANGES.log`.
3. Check `git status`.
4. Identify task ownership.
5. Make focused changes.
6. Run relevant validation.
7. Update the handover log when necessary.

## Security

Never commit:

- API keys
- passwords
- private credentials
- production secrets
- authentication tokens
- sensitive `.env` values

See `AGENTS.md` for the complete collaboration and safety rules.
