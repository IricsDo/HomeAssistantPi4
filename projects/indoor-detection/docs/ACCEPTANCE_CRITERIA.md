# Acceptance criteria

## Functional

- Phát hiện `smoke`, `fire`, `person` trên ảnh và video.
- Trả về bounding box, confidence, frame index và class.
- Threshold và temporal confirmation độc lập theo class.
- Ảnh mờ không tự động suppress smoke; event có `low_image_quality=true`.
- `occupied_hazard=true` chỉ khi person và ít nhất một hazard đã xác nhận.
- Lưu được annotated media và JSONL schema v2.

## Dataset gates

- Mọi ảnh training được audit annotation completeness cho cả ba target class.
- Không có exact/near duplicate xuyên train, validation và test.
- Split theo source/video trước khi augment.
- Test split không được dùng để chọn epoch, threshold hoặc augmentation.
- Báo cáo phân bố box, image và co-occurrence theo class/source/split.

## Model quality

- Smoke recall không giảm quá 0,03 so với smoke baseline trên cùng test slice.
- Smoke recall mục tiêu >= 0,90.
- Fire và person có target riêng sau khi validation corpus được khóa.
- Báo cáo per-class precision, recall, mAP50, mAP50-95 và confusion matrix.
- Negative slices: steam/blur cho smoke; warm light/reflection cho fire; poster/TV
  cho person.

## Raspberry Pi 4

- Raspberry Pi OS 64-bit, batch size 1.
- Một unified artifact ưu tiên dưới 25 MB.
- RSS service mục tiêu dưới 600 MB.
- Tốc độ mục tiêu >= 3 FPS tại input size được chọn.
- Fire detection-to-alert mục tiêu <= 1 giây; smoke <= 2 giây.
- Không crash hoặc tăng RAM liên tục trong soak test 8 giờ.

Các ngưỡng performance cuối được khóa sau benchmark thực tế trên Pi 4 4 GB.
