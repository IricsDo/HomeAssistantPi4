# Acceptance criteria

## Functional

- Phát hiện class `smoke` trên ảnh và video.
- Trả về bounding box, confidence, frame index và estimated origin.
- Video chỉ phát cảnh báo sau khi thỏa temporal confirmation.
- Ảnh mờ vẫn có thể phát cảnh báo và phải có `low_image_quality=true`.
- Lưu được ảnh/video annotated và event log để xem lại.

## Model quality

- Smoke recall trên test set >= 0.90.
- Báo cáo precision, mAP50, mAP50-95 và false alarms per video hour.
- Test split không chứa frame cùng video/source với train split.
- Có test slice riêng cho indoor, kitchen, low light, blur và steam.

## Raspberry Pi 4

- Chạy trên Raspberry Pi OS 64-bit.
- Batch size 1.
- Model artifact ưu tiên dưới 25 MB.
- RSS của smoke service mục tiêu dưới 600 MB.
- Tốc độ mục tiêu >= 3 FPS ở input size được chọn.
- Detection-to-alert latency <= 2 giây với cấu hình temporal mặc định.
- Không crash hoặc tăng RAM liên tục trong soak test 8 giờ.

Các ngưỡng hiệu năng là mục tiêu ban đầu và chỉ được chốt sau benchmark thực tế
trên Pi 4 4 GB.
