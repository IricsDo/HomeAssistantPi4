# Joint smoke/fire/person dataset intake

Ngày đánh giá: 2026-09-30.

## Vì sao không tiếp tục vẽ box person thủ công

YOLO26n pretrained đã học class `person` từ COCO, và project đã có COCO person
subset 12.000 ảnh. Vấn đề không phải thiếu một model biết nhận diện người mà là
**partial labels** khi trộn nguồn dữ liệu:

- Home-fire và Indoor-FS chỉ cam kết annotation `fire/smoke`.
- Một người nhìn thấy trong các ảnh đó nhưng không có box sẽ được detector học
  như background khi fine-tune ba lớp.
- Pretrained weights giảm chi phí khởi tạo nhưng không ngăn được việc quên class
  hoặc giảm recall khi nhận supervision âm sai trong quá trình fine-tune.

Person candidate review đã chứng minh pseudo-label tự động cũng chưa đủ an toàn:
YOLO detect và pose đều có false positive tương quan trên lửa, bàn tay và vùng
sáng. Tuy nhiên review 5.364 candidate không còn là gate chính vì có thể dùng
dataset đã gắn đầy đủ cả ba target class.

## Nguồn ưu tiên

### 1. Fire Smoke and Human Detector v32

- URL: https://universe.roboflow.com/spyrobot/fire-smoke-and-human-detector/dataset/32
- License công bố: CC BY 4.0.
- 9.749 ảnh: train 8.001, validation 1.017, test 731.
- Classes: `fire`, `smoke`, `human`.
- Resize 640x640, không áp dụng augmentation ở version 32.

Đây là ứng viên intake đầu tiên vì có đủ ba split, dung lượng thực dụng hơn và
không chứa bản sao augmentation do Roboflow sinh như version 23/31. Vì là dữ
liệu cộng đồng, số lượng không đồng nghĩa chất lượng: phải audit label, duplicate,
phân bố class, negative samples và tỷ lệ indoor trước khi train.

### 2. Fire–Smoke–Person Dataset (3-Class)

- Dataset: https://www.kaggle.com/aminafawaz/firesmokeperson-dataset-3-class
- Paper: https://www.techscience.com/CMES/v147n3/67931/html
- License công bố: CC BY 4.0.
- 6.660 ảnh, annotation YOLO thủ công, có background images.
- File công bố khoảng 14,5 GB và Kaggle yêu cầu đăng nhập để tải.
- Chỉ mô tả train/validation, nên cần tự tạo held-out test split sau khi loại
  duplicate nếu chọn nguồn này.

Nguồn này có provenance nghiên cứu tốt hơn nhưng chi phí tải/chuẩn bị lớn hơn.
Nó là lựa chọn thứ hai hoặc nguồn bổ sung sau baseline v32.

## Intake gate

1. Tải archive vào `E:\HomeAssistantPi4\raw`; không commit dữ liệu lớn.
2. Xác minh license, version, URL nguồn, checksum archive và class names.
3. Chạy `indoor-prepare-joint`; tool chỉ chấp nhận đúng ba lớp và yêu cầu label
   file cho mọi ảnh.
4. Chạy structural audit, exact/cross-split duplicate audit và thống kê từng lớp.
5. Sinh contact sheets bằng stratified sample: positive từng lớp, multi-class,
   negative, box nhỏ/lớn và từng split.
6. Chỉ train baseline nếu spot-check không thấy lỗi hệ thống như thiếu class,
   box lệch hàng loạt hoặc leakage giữa split.

Manual annotation chỉ quay lại cho một tập nhỏ các lỗi có giá trị cao hoặc dữ
liệu indoor riêng của camera thật. Không yêu cầu người dùng duyệt toàn bộ 5.364
pseudo-label trước khi có baseline.
