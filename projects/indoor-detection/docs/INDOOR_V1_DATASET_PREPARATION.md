# Indoor v1 dataset preparation

Ngày ghi nhận: 2026-09-30.

## Kết quả đã khóa

COCO 2017 person subset được tạo với seed 42 và mapping thống nhất
`smoke=0`, `fire=1`, `person=2`:

| Split | Images | Positive | Negative | Person boxes |
| --- | ---: | ---: | ---: | ---: |
| train | 7.000 | 6.000 | 1.000 | 23.611 |
| val | 2.501 | 1.347 | 1.154 | 5.335 |
| test | 2.499 | 1.346 | 1.153 | 5.442 |

Audit không tìm thấy exact duplicate hoặc cross-split duplicate. Manifest:
`E:\HomeAssistantPi4\processed\coco-person-v1\manifest.json`, SHA-256
`e03c62e8e34e44556495db097243eb596a3736a49bb23cde4a3e1b96fe6d89c6`.

Index tạm `E:\HomeAssistantPi4\datasets\indoor-v1` đã compose từ Home-fire,
Indoor-FS và COCO person:

| Split | Images |
| --- | ---: |
| train | 14.900 |
| val | 4.301 |
| test | 4.299 |

Manifest index có SHA-256
`9548c53c111033c53213cdc9b2a37e6ee41ac7f20fc46e9cae668918bd876d68`.

## Person annotation gate

YOLO26n COCO pretrained, SHA-256
`9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef`,
đã quét toàn bộ 11.500 ảnh smoke/fire tại confidence 0,20 và input 640:

- 2.360 ảnh có candidate, tổng cộng 3.887 person boxes.
- 898 ảnh chỉ có candidate confidence từ 0,65 trở lên.
- 1.462 ảnh có ít nhất một candidate cần manual review.
- Phân bố: train 1.628, val 433, test 299 ảnh có candidate.

Artifacts nằm trong `E:\HomeAssistantPi4\reports\person-audit-v1`:

- `report.json` SHA-256
  `15dcd39de13ecc0fb88a1ee37f99ba4ded42277e8f5e81c093b2b163b65491e6`.
- `candidates.jsonl` SHA-256
  `bd2832c1abeec96b051d1b09847e79b665d442ceb099bd041d1436d6765ded4a`.

Source labels chưa bị sửa. `indoor-v1` hiện là index kiểm kê, **chưa phải corpus
được phép train**. Gate tiếp theo là review candidate, tạo derivative smoke/fire
có person label, audit lại duplicate/annotation completeness, rồi compose một
index bất biến mới cho training.
