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

Kế hoạch tổng thể và checklist cho agent tiếp theo:
[PROJECT_PLAN.md](projects/indoor-detection/PROJECT_PLAN.md).

Đang đánh giá nguồn person bổ sung (indoor hoặc outdoor) cho camera mục tiêu
Raspberry Pi Camera Module 3 Wide IMX708. Sampling là lựa chọn, chưa chốt can thiệp;
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
CrowdHuman đã qua annotation prefilter và domain preview; bước tiếp theo là
pilot 60 ảnh gốc/621 box đã ghép nhãn và có gallery; exact duplicate audit đạt.
Review box/convention và near duplicates còn tiếp tục. Chưa đạt data gate hoặc có training mới; xem
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
