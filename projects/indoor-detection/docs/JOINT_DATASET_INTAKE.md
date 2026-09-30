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

## Kết quả audit v32 (2026-09-30)

- Processed dataset:
  `E:\HomeAssistantPi4\processed\indoor-joint-v1`
- Audit report và contact sheets:
  `E:\HomeAssistantPi4\reports\indoor-joint-v1-audit`
- Structural audit: PASS. Có đủ image/label cho cả ba split; không có ảnh hỏng,
  label thiếu/thừa, box row sai định dạng hoặc box vượt biên ảnh.
- Exact duplicate: 100 nhóm trong cùng split; không có nhóm exact duplicate
  xuyên split. So sánh label theo từng nhóm cho thấy 59 nhóm có annotation khác
  nhau, nên không được tự động bỏ một bản sao.
- Roboflow near-duplicate cross-split exclusions: 0.
- Class totals:

| Split | Images | Smoke boxes | Fire boxes | Person boxes | Negative images |
|---|---:|---:|---:|---:|---:|
| train | 8,001 | 6,032 | 9,439 | 4,436 | 819 |
| validation | 1,017 | 800 | 1,627 | 455 | 74 |
| test | 731 | 611 | 954 | 370 | 3 |

- Polygon conversion: một segmentation polygon được đổi thành enclosing YOLO
  bounding box; manifest ghi nhận phép đổi này.
- Visual spot-check theo class và split cho thấy annotation thường phủ đúng vùng
  target, nhưng phần lớn ảnh fire/smoke là cháy rừng hoặc sự cố ngoài trời. Data
  gate **FAILED** về mức phù hợp với môi trường indoor; duplicate có label xung
  đột cũng chưa được giải quyết.

Không train từ dataset này. Bước tiếp theo là tìm/thu thập nguồn fully labeled
phù hợp indoor, đồng thời adjudicate duplicate groups có nhãn khác nhau; sau đó
tạo lại processed dataset và chạy toàn bộ gate trước khi train.

### Gói review duplicate (2026-09-30)

Audit tạo gói adjudication tại
`E:\HomeAssistantPi4\reports\indoor-joint-v1-audit`:

- `duplicate-conflicts/duplicate-001.jpg` đến `duplicate-059.jpg`: ảnh exact
  duplicate đặt cạnh nhau với annotation của từng bản để soát bằng mắt.
- `duplicate-adjudication.csv`: một dòng cho mỗi ảnh trong 59 nhóm, có cột
  `decision` và `review_notes` để người review ghi quyết định.

Không gộp hay xóa nhãn tự động. Ví dụ nhóm đầu có 7 và 9 box trên cùng ảnh;
khác biệt này cần xem từng box để phân biệt annotation thiếu với annotation sai.

### Nguồn indoor đang xem xét

[Indoor Fire Smoke Dataset trên Zenodo](https://zenodo.org/records/15826133)
mô tả 5.000 ảnh indoor và box cho `fire`/`smoke`, chia train/validation/test.
Metadata hiện công bố không liệt kê annotation `person`, nên không được ghép vào
dataset ba lớp cho đến khi person được rà soát và gắn đầy đủ trên toàn bộ ảnh.
Trang Zenodo đang để trống trường rights/license; cần làm rõ quyền sử dụng trước
khi tải để dùng trong project. Chưa đưa vào processed dataset.

### Tiếp tục rà soát nguồn và duplicate (2026-09-30)

Phân tích đủ 59 nhóm conflict cho thấy:

- 22 nhóm có cùng số box theo class nhưng khác tọa độ.
- 29 nhóm có cùng class hiện diện nhưng số box khác nhau.
- 8 nhóm còn khác cả class hiện diện.

Vì vậy không thể giải quyết bằng quy tắc gộp tự động. Đã rà soát cả 59 contact
sheets: 49 nhóm là cảnh ngoài trời/ngoại thất và được ghi
`exclude_group_outdoor` vào CSV. Mười nhóm còn lại có bối cảnh trong nhà hoặc
chưa đủ rõ để phân loại (`018`, `019`, `022`, `023`, `030`, `031`, `048`, `050`,
`051`, `054`); cần soát annotation kỹ hơn. Ảnh/nhãn nguồn không bị sửa.

Đã kiểm tra thêm hai dataset Roboflow có đủ ba class: [fire-person-dataset
(Yolo Training)](https://universe.roboflow.com/yolo-training-8hmw2/fire-person-dataset)
và [Person-Fire-Smoke-New](https://universe.roboflow.com/whales-workspace-weuke/person-fire-smoke-new).
Cả hai công bố CC BY 4.0, nhưng không có mô tả chứng minh indoor relevance.
Dataset thứ nhất còn có một version ghi 23.882 ảnh do augmentation tạo ra; cần
loại trừ augmentation/duplicate leakage khi đánh giá. Chưa tải vì metadata hiện
chưa đủ để xác nhận phù hợp.

Một bài báo mô tả dataset 5.000 ảnh với fire/smoke/person, nhưng nói ảnh lấy từ
nhiều miền (forest, industrial, urban, indoor, vehicle) và data chỉ được cấp từ
tác giả tương ứng theo yêu cầu. Không có archive công khai để kiểm tra trực tiếp;
không thể dùng làm nguồn đã xác minh.
