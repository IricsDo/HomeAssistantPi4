# Model artifacts

Không commit checkpoint hoặc exported model lớn vào Git.

- `checkpoints/`: PyTorch training artifacts.
- `exported/`: NCNN/ONNX artifacts dành cho benchmark và deployment.

Mỗi model phát hành cần đi kèm metadata: source checkpoint, dataset version,
training config, metrics, export format và checksum.
