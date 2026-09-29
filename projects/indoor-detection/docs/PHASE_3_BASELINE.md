# Phase 3 baseline training report

## Kết luận

YOLO26n baseline đã được huấn luyện đủ 100 epoch và đánh giá độc lập trên test
split. Model nhỏ, chạy nhanh trên GPU phát triển và đạt mAP khá, nhưng **chưa đạt
điều kiện test recall >= 0,90**. Checkpoint hiện chỉ là research baseline, chưa
được duyệt export/deployment lên Raspberry Pi 4.

## Kiến trúc và môi trường

- Model: YOLO26n pretrained, smoke-only (`nc=1`).
- Fused model: 2.375.031 parameters, 5,3 GFLOPs.
- Artifact: 5.370.757 bytes (khoảng 5,12 MiB), dưới mục tiêu 25 MB.
- Training: Windows 11, Python 3.14.7, PyTorch 2.14.0+cu130,
  Ultralytics 8.4.163, RTX 5070 Laptop 8 GB.
- Data: Home-fire v1.0.0 smoke-only; 3.900 train / 1.300 val / 1.300 test.
- Config: 100 epoch, image size 640, auto-batch chọn 12, AMP, AdamW auto,
  seed 42, deterministic, cache tắt.
- Thời gian huấn luyện: 66,31 phút.

YOLO26n được chọn làm baseline vì đây là biến thể nano, phù hợp hướng deployment
edge. Việc benchmark NCNN/CPU trên Pi 4 vẫn thuộc phase sau; tốc độ GPU dưới đây
không được dùng để suy diễn FPS trên Pi.

## Kết quả

Checkpoint tốt nhất được chọn ở epoch 75 bằng validation fitness:

| Split / operating point | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| Validation, best epoch | 0,917 | 0,897 | 0,937 | 0,608 |
| Test, Ultralytics F1 point | 0,909 | 0,823 | 0,875 | 0,552 |
| Test, confidence 0,20 | 0,787 | 0,858 | — | — |
| Test, validation-calibrated confidence 0,4004 | 0,895 | 0,833 | — | — |

Validation calibration chọn confidence `0,4004` để đạt recall `0,9001` với
precision `0,9129`. Khi giữ nguyên threshold đó trên test, recall chỉ còn
`0,8331`. Đây là distribution/generalization gap, không phải lỗi có thể sửa bằng
threshold tuning.

Chẩn đoán trên test cho thấy phải hạ confidence đến khoảng `0,006` mới đạt
recall `0,9028`, nhưng precision giảm còn `0,3662`. Ngưỡng này **không được dùng
làm cấu hình**, vì được suy ra từ test và tạo quá nhiều false positive.

Test inference trên RTX 5070 ở image size 640 đo được khoảng 1,4–2,6 ms/image
cho riêng forward pass sau warm-up. Con số này chỉ mô tả môi trường Windows GPU.

## Artifact và provenance

- Stable checkpoint:
  `E:\HomeAssistantPi4\models\checkpoints\smoke_yolo26n_homefire_v1_baseline.pt`
- SHA-256:
  `b0b654362ec469aa086827dc8415f2fd9028011bd283b6f63527b01efa694d3b`
- Full run:
  `E:\HomeAssistantPi4\runs\smoke-detection\yolo26n_baseline_640`
- Machine-readable reports: `E:\HomeAssistantPi4\reports\yolo26n_baseline_640_*.json`
- Lightweight metadata committed at `models/baseline-yolo26n-homefire-v1.json`.

Model binary, optimizer state, plots và dataset không được commit vào Git.

## Khoảng trống trước khi deployment

- Test recall còn thiếu khoảng 7,7 điểm phần trăm tại F1 point.
- Chưa có source/video-group metadata để loại trừ hoàn toàn leakage theo chuỗi
  frame; exact duplicate giữa split đã được loại trừ ở Phase 2.
- Chưa có evaluation slice riêng cho kitchen, steam, blur, low-light và smoke nhỏ.
- Chưa đo false alarms/video-hour vì chưa có video/camera phù hợp.
- Chưa đánh giá image size 416 hoặc NCNN trên Raspberry Pi 4.

## Hướng lặp tiếp theo

Ưu tiên vòng cải thiện dựa trên dữ liệu trước khi tăng kích thước model:

1. Phân tích false negative/false positive trên test theo kích thước box và điều
   kiện ảnh, nhưng không dùng test để chọn hyperparameter.
2. Bổ sung/chuẩn hóa dữ liệu indoor smoke, đặc biệt smoke nhỏ, mờ, low-light,
   kitchen steam và hard negatives không có smoke.
3. Tạo validation slices và nếu có thể tách lại theo source/video group.
4. Thử augmentation có kiểm soát trên train, chốt bằng validation, sau đó chỉ
   đánh giá test một lần cho candidate mới.
5. Chỉ cân nhắc P2 head hoặc model lớn hơn nếu lỗi chủ yếu đến từ smoke rất nhỏ;
   mọi thay đổi phải giữ mục tiêu tài nguyên Pi 4.
