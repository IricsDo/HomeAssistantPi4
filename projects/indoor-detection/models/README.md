# Model artifacts

Không commit checkpoint hoặc exported model lớn vào Git.

- `checkpoints/`: PyTorch training artifacts.
- `exported/`: NCNN/ONNX artifacts dành cho benchmark và deployment.

Mỗi model phát hành cần đi kèm metadata: source checkpoint, dataset version,
training config, metrics, export format và checksum.

Baseline smoke-only Phase 3 được giữ làm mốc so sánh, không phải unified model:

- Artifact: `E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_homefire_v1_baseline.pt`
- Metadata: `models/baseline-yolo26n-homefire-v1.json`
- Trạng thái: research baseline, chưa đạt test recall và chưa được duyệt deployment.
