# Data directory

Không commit dataset vào Git.

- `raw/`: dữ liệu tải về, giữ nguyên theo nguồn.
- `interim/`: dữ liệu đang chuyển đổi hoặc audit.
- `processed/smoke/`: dataset YOLO smoke-only dùng cho train/val/test.

Mỗi dataset phải có manifest gồm nguồn, license, ngày tải, checksum và mapping
từ annotation gốc sang class `smoke`.
