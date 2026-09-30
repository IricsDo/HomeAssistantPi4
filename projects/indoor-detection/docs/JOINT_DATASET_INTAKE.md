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

### Cập nhật chính sách intake (2026-09-30)

Mục tiêu sản phẩm vẫn là một model với ba class `smoke`, `fire`, `person` và
một lượt inference. Không còn yêu cầu một nguồn đơn lẻ phải cung cấp cả ba
class; nhiều nguồn có thể được hợp nhất sau khi class ID được chuẩn hóa.

Nguồn partial-label chỉ được dùng an toàn nếu, với từng ảnh, các class ngoài
phạm vi đã được xác minh là không xuất hiện, được bổ sung nhãn, hoặc được xử lý
bằng class-masked loss đã triển khai và kiểm chứng. YOLO label format đang dùng
không biểu diễn trạng thái “unknown”: class không có box bị xem như âm tính.
Do đó không được ghép trực tiếp fire/smoke-only images có người chưa gắn nhãn
vào training set ba class.

Tool `indoor-prepare-joint` hiện vẫn yêu cầu mỗi nguồn khai báo cả ba class và
label file cho mọi ảnh. Đây là giới hạn hiện tại của implementation; cần sửa
tool/manifest và thêm validation trước khi nhập nguồn partial-label. Trong lúc
chưa có hỗ trợ đó, chỉ dùng nguồn đã gắn đủ class hoặc curate/augment nhãn sao
cho mọi class có thể xuất hiện đều được kiểm soát.

Thứ tự ưu tiên nguồn: (1) có annotation sẵn, (2) đại diện cho môi trường/camera
indoor mục tiêu, (3) nhãn đủ chính xác và có split/provenance hữu ích. Ghi rõ
license và tình trạng xác minh khi intake; thiếu metadata không tự loại nguồn
khỏi nghiên cứu/đánh giá, nhưng không được coi license chưa rõ là đã cấp quyền.
Trước khi chia sẻ dataset/model ra ngoài hoặc dùng theo phạm vi có yêu cầu rõ
ràng, cần xem lại quyền sử dụng tương ứng.

### Ứng viên đã có trên ổ E:

| Nguồn derivative | Ảnh | Annotation scope trong manifest | License/provenance ghi trong manifest | Trạng thái |
|---|---:|---|---|---|
| `processed/indoor-fs-v2` | 5.000 | `smoke`, `fire` | CC-BY-4.0; Hugging Face commit được ghi | Ứng viên indoor; cần kiểm tra annotation và xử lý nhãn person chưa biết |
| `processed/indoor-home-fire-v2` | 6.500 | `smoke`, `fire` | CC-BY-NC-4.0; repo/release/DOI được ghi | Ứng viên home-fire; cần kiểm tra annotation và xử lý nhãn person chưa biết |
| `processed/coco-person-v1` | 12.000 | `person` | COCO annotation CC-BY-4.0; ảnh giữ license Flickr theo từng ảnh | Person source; mức đại diện indoor và fire/smoke absence cần đánh giá |
| `processed/indoor-joint-v1` (Roboflow v32) | 9.749 | `smoke`, `fire`, `person` | CC BY 4.0 theo manifest | Annotation đủ scope nhưng audit indoor/domain và duplicate hiện chưa đạt |

Các số và trạng thái license ở bảng được đọc từ manifest hiện có; đây chưa phải
chứng nhận độc lập về quyền sử dụng hay độ đầy đủ annotation. Các nguồn partial
không được ghép thẳng bằng pipeline hiện tại.

Data gate mới vẫn kiểm tra cấu trúc, annotation, duplicate/leakage, phân phối
class và mức đại diện indoor. Gate nhãn được đánh giá theo class scope từng
ảnh/nguồn, không theo điều kiện mọi nguồn phải có cùng danh sách class. Gate
này chưa đạt cho đến khi pipeline có cách xử lý nhãn partial an toàn.

### Sàng lọc thiếu nhãn chéo (2026-09-30)

Đã tạo sample phân tầng 390 ảnh trên E: tại
`E:\HomeAssistantPi4\reports\partial-label-audit-v1`: 120 Indoor-FS, 180
Home-fire và 90 COCO person. Mẫu lấy seed 42, tối đa 15 ảnh cho mỗi nhóm nhãn
đã biết trong từng split. Contact sheets, `review.csv`, số population/sample
theo stratum và ghi chú review nằm trong cùng thư mục.

Đã xác nhận bằng mắt 15 ảnh có người nhưng không có person label (13 Home-fire,
2 Indoor-FS); các ảnh này đến từ fire-only, smoke-only và một số ảnh rỗng nhãn
fire/smoke. 285 dòng fire/smoke còn lại giữ pending, vì thumbnail screening
không đủ để tuyên bố từng ảnh không có người. Trong 90 ảnh COCO person, không
thấy fire/smoke rõ ở contact-sheet resolution; đây chỉ là screening, không
chứng minh toàn bộ 12.000 ảnh không có hai lớp đó.

Đối chiếu sample với person-audit-v2 cũ cho thấy detector có candidate trên
58/300 ảnh fire/smoke sample (39/180 Home-fire; 19/120 Indoor-FS). Audit cũ
quét đủ 11.500 ảnh fire/smoke và có candidate ở 2.360 ảnh / 3.887 box. Đây là
triage không có auto-acceptance, không phải nhãn đã xác nhận; pseudo-label từng
có false positives tương quan.

Kết luận: nguồn fire/smoke không an toàn để dùng trực tiếp như ảnh âm tính của
person trong training ba lớp. Prototype per-image class-masked classification
loss đã được cài cho Ultralytics 8.4.163: loss chỉ tính BCE của các class được
khai báo là đã biết trên từng ảnh, và từ chối batch có ground-truth class nằm
ngoài scope. Bảy test synthetic đạt, gồm một synthetic forward/backward trên
YOLO26n thật; chưa dùng ảnh hoặc nhãn dataset thật.

Prototype đã được nối vào dataloader/trainer cho cả train và validation. Metrics
validation bỏ prediction thuộc class unknown của từng ảnh. Multi-image
augmentation (`mosaic`, `mixup`, `cutmix`, `copy_paste`) bị vô hiệu hóa; các
biến đổi một ảnh giữ nguyên scope. Synthetic trainer smoke test một epoch trên
bốn ảnh 64x64 đã đạt, không dùng pretrained weights hay dữ liệu project thật.

Derivative `E:\HomeAssistantPi4\processed\indoor-partial-joint-v2` đã được tạo
từ Home-fire, Indoor-FS và COCO-person, gồm 14.900/4.301/4.297 ảnh cho
train/val/test và `class_scope_manifest.json` theo từng ảnh. Audit đầy đủ 23.498
ảnh/label đạt structure, label/scope, distribution và duplicate machine gates:
0 lỗi, 0 path overlap, 0 exact duplicate. Hai bản duplicate có box fire lệch nhẹ
trong v1 đã được adjudicate: giữ `test_1240` thay `test_584`, giữ `test_696`
thay `test_967`; source không bị sửa. Report nằm tại
`E:\HomeAssistantPi4\reports\indoor-partial-joint-v2-audit\index-audit.json`.
Visual annotation/domain gate vẫn pending. Chưa train baseline.

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

### Adjudication update (2026-09-30)

Review ở độ phân giải đầy đủ đã tăng quyết định loại ngoại thất lên 55/59 nhóm.
Ở group `duplicate-054`, đã chọn annotation của bản thứ hai: lửa/khói giống nhau,
box của hai người chặt và tách rõ hơn. Còn ba nhóm (`019`, `050`, `051`) chưa
đủ cơ sở để chọn nhãn dứt khoát; chúng vẫn được giữ trong ledger là chưa xử lý.
Xem quyết định và lý do từng ảnh trong
`E:\HomeAssistantPi4\reports\indoor-joint-v1-audit\duplicate-adjudication.csv`.
Không có annotation nguồn nào bị sửa.

### Rà soát tiếp theo (2026-09-30)

Độ phân giải đầy đủ cho `duplicate-019` cho thấy hai bộ nhãn giống nhau ngoài
box người: bản thứ hai bám sát hơn vào dáng người nhìn thấy. Ledger chọn bản
thứ hai làm annotation giữ lại; bản đầu là duplicate cần bỏ khi tái tạo dataset.
`duplicate-050` vẫn chưa adjudicate được: một bản có thêm nhiều box smoke trên
các vùng khói mờ, nhưng ảnh không cho cơ sở chắc chắn để xác định box nào là
đúng. `duplicate-051` cũng giữ pending: bản thứ hai có thêm một box person rõ
ràng, nhưng còn nhiều lính cứu hỏa nhìn thấy ở phần dưới ảnh không được gắn nhãn.
Không sửa nhãn nguồn.

Tìm nguồn công khai bổ sung chưa tìm được dataset đủ điều kiện: [ISFire-4 trên
Hugging Face](https://huggingface.co/datasets/shahriar-5/ISFire-4) có 7.370 ảnh
indoor nhưng bốn class là các biến thể màu của fire/smoke, không có person.
Zenodo Indoor Fire Smoke có mô tả box fire/smoke cho 5.000 ảnh nhưng không có
person và metadata license còn trống. Cả hai đều chưa được nhập. Data gate vẫn
FAILED; không train.
