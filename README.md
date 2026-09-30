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

Mốc implementation trước handover là commit `b07a200`, cung cấp pipeline intake
dataset YOLO đã gắn đủ cả ba lớp. Dataset Roboflow
`fire-smoke-and-human-detector` v32 đã được tải về ổ E và giải nén đủ:

| Split | Images | Labels |
|---|---:|---:|
| train | 8.001 | 8.001 |
| valid | 1.017 | 1.017 |
| test | 731 | 731 |
| **Tổng** | **9.749** | **9.749** |

- Archive:
  `E:\HomeAssistantPi4\raw\downloads\fire-smoke-human-v32.zip`
- SHA-256:
  `052078BD4677C6FF4B1D4AF9321B891E0A79AE16F899CED6E45F4BD3A67168A2`
- Raw extraction hoàn chỉnh:
  `E:\HomeAssistantPi4\raw\fire-smoke-human-v32-clean`
- Processed dataset `E:\HomeAssistantPi4\processed\indoor-joint-v1` chưa được tạo.

Bước tiếp theo là chuẩn hóa split paths trong `data.yaml`, chạy joint intake,
audit duplicate/class distribution/negative samples, rồi spot-check annotation.
Chưa bắt đầu train checkpoint ba lớp. Xem `CHANGES.log` để có handover mới nhất.

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
