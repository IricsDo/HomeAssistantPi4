# Phase 2 dataset report

## Kết quả

Home-fire dataset release `v1.0.0` đã được tải từ GitHub Release, giữ nguyên tại
`E:\HomeAssistantPi4\raw\Home-fire-dataset\v1.0.0`, rồi chuyển thành dataset
YOLO một lớp tại `E:\HomeAssistantPi4\processed\smoke-home-fire-v1`.

Mapping đã được kiểm tra bằng annotation và ảnh mẫu:

- class nguồn `0=fire`: loại box;
- class nguồn `1=smoke`: đổi thành class đích `0=smoke`;
- ảnh không có box smoke sau chuyển đổi: giữ lại làm negative sample.

| Split | Images | Positive | Negative | Smoke boxes |
|---|---:|---:|---:|---:|
| train | 3.900 | 1.717 | 2.183 | 1.834 |
| val | 1.300 | 574 | 726 | 617 |
| test | 1.300 | 618 | 682 | 689 |
| **Total** | **6.500** | **2.909** | **3.591** | **3.140** |

Audit ngày 2026-09-28 đạt các kiểm tra cấu trúc cơ bản:

- 6.500/6.500 ảnh có label tương ứng;
- không có ảnh hỏng, label lỗi, class ngoài phạm vi hoặc tọa độ không hợp lệ;
- có 2 nhóm ảnh negative trùng exact trong test (`1240/584` và `696/967`);
- không có ảnh trùng exact đi xuyên qua train/val/test.

Hai nhóm trùng nội bộ không gây leakage giữa split nhưng cần được xem xét trước
training chính thức. Báo cáo máy-local đầy đủ nằm tại
`E:\HomeAssistantPi4\reports\smoke-home-fire-v1.audit.json`.

## Khả năng tái tạo

Metadata nguồn, kích thước và SHA-256 của ba archive được commit tại
`data/manifests/home-fire-v1.0.0.json`. Pipeline chuyển đổi nằm trong
`indoor_detection.dataset`; lệnh chạy được ghi tại `data/README.md`.

Dataset của Bo Peng và Tae-Kook Kim dùng giấy phép CC BY-NC 4.0. Ảnh và
annotation không được đưa vào repo; việc sử dụng project hiện tại phải giữ mục
đích phi thương mại, ghi công nguồn và trích dẫn bài báo
`YOLO-HF: Early Detection of Home Fires Using YOLO` (IEEE Access 2025,
DOI `10.1109/ACCESS.2025.3566907`).

## Giới hạn trước training

Kiểm tra exact hash không chứng minh rằng split hoàn toàn độc lập theo video hoặc
nguồn camera. Cần kiểm tra near-duplicate/chuỗi frame và đánh giá các slice indoor,
kitchen, steam, blur, low-light trước khi dùng test set để chốt chất lượng model.

D-Fire chưa được nhập vào bản processed vì link dữ liệu chính thức hiện không tải
được tự động. Không dùng mirror không rõ nguồn để tránh sai lệch version/license.
