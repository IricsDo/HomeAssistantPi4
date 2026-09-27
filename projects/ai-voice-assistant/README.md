# Neko AI Voice Assistant

Prototype trợ lý gia đình bằng giọng nói dành cho Raspberry Pi 4. Trợ lý có tên
**Neko**, nhận đầu vào từ bàn phím hoặc microphone, gửi nội dung tới mô hình ngôn
ngữ và đọc câu trả lời bằng giọng nói.

Project được phát triển dựa trên hai nguồn tham khảo:

1. <https://github.com/ThomasVuNguyen/chatGPT-Voice-Assistant>
2. <https://github.com/arjun-krishnan/chatGPT-Voice-Assistant>

Mục tiêu ban đầu là điều chỉnh các project tham khảo cho trường hợp sử dụng cá
nhân, ưu tiên chi phí thấp và hướng tới một trợ lý gia đình chạy trên Raspberry
Pi.

## Trạng thái

Đây là prototype nghiên cứu, chưa phải ứng dụng hoàn chỉnh. Xem
[PROJECT_STATUS.md](PROJECT_STATUS.md) để biết chính xác phần đã triển khai,
những giới hạn hiện tại và hướng phát triển được suy ra từ code.

## Điểm chạy thử

- `main_user_typing.py`: nhập câu hỏi bằng bàn phím, nhận câu trả lời từ LLM và
  phát câu trả lời qua `pyttsx3`.
- `main_user_talking.py`: prototype nhận âm thanh từ microphone và chuyển giọng
  nói thành văn bản bằng AssemblyAI. Luồng này hiện còn dang dở.

Các script cần biến môi trường tương ứng với dịch vụ đang dùng, tối thiểu gồm
`NVIDIA_API_KEY` và `Assembly_AI_KEY`. Project chưa có file khai báo dependency
hoặc quy trình cài đặt tái lập.
