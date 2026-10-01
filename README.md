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

Calibration/error analysis đã hoàn tất ở 640 và resolution triển khai 416. V2
chưa đạt gate 416: smoke cần threshold `0,033` với precision `0,581`, còn person
chỉ đạt recall `0,480` và F1 `0,597`. NCNN export được giữ lại cho đến sau một
vòng fine-tune khớp resolution; test không được mở lại trong quyết định này.

- Dataset: `E:\HomeAssistantPi4\processed\indoor-partial-joint-v2`
- Run: `E:\HomeAssistantPi4\runs\indoor-detection\indoor_partial_joint_yolo26n_v2`
- Reports: `E:\HomeAssistantPi4\reports\indoor-yolo26n-v2-evaluation`

Bước tiếp theo là chạy config `train_indoor_v3_416.yaml` từ v2 `best.pt`, đánh
giá lại validation gate rồi mới export NCNN. Benchmark Pi 4 và camera thật chờ
phần cứng.

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
