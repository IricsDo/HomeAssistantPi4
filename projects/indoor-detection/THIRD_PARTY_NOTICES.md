# Third-party notices

Project dự kiến sử dụng các thành phần sau. Phiên bản chính xác sẽ được khóa sau
khi môi trường phát triển được cài và kiểm thử.

| Component | Purpose | License / terms |
|---|---|---|
| Ultralytics | Training, validation and model export | AGPL-3.0 |
| PyTorch | Training backend on Windows | BSD-style license |
| OpenCV | Image and video I/O | Apache-2.0 |
| NCNN | Raspberry Pi inference target | BSD-3-Clause |
| D-Fire dataset | Initial fire/smoke dataset | CC0-1.0 |
| [Home-fire dataset v1.0.0](https://github.com/PengBo0/Home-fire-dataset) | Indoor fire/smoke dataset by Bo Peng and Tae-Kook Kim | CC BY-NC 4.0 |
| [Indoor Fire and Smoke Dataset](https://huggingface.co/datasets/shahriar-5/IFireSmoke) | Indoor fire/smoke diversity | CC BY 4.0 |
| [COCO 2017](https://cocodataset.org/) | Bootstrap person boxes and negative scenes | Annotations CC BY 4.0; each image retains its recorded Flickr license |

Dataset và pretrained weight chỉ được đưa vào pipeline sau khi nguồn, version,
checksum và điều kiện giấy phép đã được ghi lại. Project này là phi thương mại và
phải duy trì source code theo nghĩa vụ AGPL của Ultralytics.

Khi sử dụng Home-fire dataset, trích dẫn: Bo Peng and Tae-Kook Kim,
“YOLO-HF: Early Detection of Home Fires Using YOLO,” IEEE Access, vol. 13,
pp. 79451–79466, 2025, DOI: `10.1109/ACCESS.2025.3566907`.

COCO derivatives retain the selected image IDs and source license metadata in
their generated manifest. Images must not be redistributed under a license
different from the license attached to the original COCO image record.
