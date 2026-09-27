# Project snapshot: Neko AI Voice Assistant

Ngày ghi nhận: 2026-09-27

Tài liệu này lưu lại trạng thái của project tại thời điểm được tách khỏi thư mục
gốc của repository. Nội dung phản ánh code hiện có; không khẳng định các luồng
phụ thuộc API, microphone hoặc thiết bị Raspberry Pi đã được kiểm thử lại.

## Mục tiêu được thể hiện trong code

Xây dựng trợ lý gia đình AI tên **Neko** cho Raspberry Pi 4 với chu trình dự kiến:

```text
Người dùng -> bàn phím/microphone -> văn bản -> LLM có lịch sử hội thoại
             -> câu trả lời -> text-to-speech -> loa
```

Project ưu tiên hội thoại ngắn gọn phù hợp với kênh âm thanh và có định hướng
giảm hoặc tránh chi phí dịch vụ. Các tài liệu tham khảo ban đầu trong lịch sử Git
còn cho thấy định hướng dài hạn về giám sát/an ninh gia đình bằng Raspberry Pi,
nhưng phần tích hợp phần cứng đó chưa xuất hiện trong code hiện tại.

## Những phần đã có

- Persona và system prompt cho trợ lý Neko.
- Tích hợp `ChatNVIDIA` với model `meta/llama3-8b-instruct` thông qua LangChain.
- Lịch sử hội thoại trong bộ nhớ, phân biệt bằng session ID.
- Chế độ nhập văn bản, nhận phản hồi LLM và đọc bằng `pyttsx3`.
- Prototype thu âm từ microphone bằng `speech_recognition`.
- Prototype chuyển giọng nói thành văn bản bằng AssemblyAI.
- Các thử nghiệm riêng lẻ cho OpenAI, NVIDIA, AssemblyAI, Whisper, microphone và
  text-to-speech.
- Module thử nghiệm sửa lỗi chính tả/ngữ pháp bằng NLTK, GingerIt và
  PySpellChecker.
- Bản code và tài nguyên âm thanh từ project tham khảo được giữ trong
  `chatGPT-Voice-Assistant/`.

## Kết quả hiện tại

### Luồng nhập bằng bàn phím

Luồng chính đã được ghép nối ở mức prototype:

1. Khởi tạo Neko và engine `pyttsx3`.
2. Nhận nội dung từ terminal.
3. Gửi nội dung qua conversation chain có memory.
4. In và đọc câu trả lời.
5. Thoát khi người dùng nhập `q`.

Luồng này vẫn phụ thuộc cấu hình API NVIDIA và voice index của hệ điều hành.

### Luồng hội thoại bằng giọng nói

Code đã có bước hiệu chỉnh microphone, nghe âm thanh và gọi AssemblyAI. Tuy
nhiên, khi transcription thành công, chương trình mới chỉ gán `transcript.text`.
Đoạn gọi LLM và TTS hiện nằm trong nhánh xử lý exception, nên chu trình hội thoại
giọng nói chưa chạy trọn vẹn.

### Kiểm thử

Thư mục `test/` chủ yếu là các script thử nghiệm thủ công và ví dụ tích hợp;
chưa phải test suite tự động có assertion. Tại thời điểm snapshot không có báo
cáo cho thấy toàn bộ project đã chạy thành công trên Raspberry Pi 4.

## Kiến trúc file

```text
ai-voice-assistant/
|-- main_user_typing.py       # Prototype nhập văn bản
|-- main_user_talking.py      # Prototype hội thoại qua microphone
|-- llm/nvidia.py             # LLM chain và conversation memory
|-- packagelib/__init__.py    # Import dùng chung và nạp biến môi trường
|-- utilities/
|   |-- prompt_template/      # Persona/system prompt của Neko
|   |-- nlp/                  # Thử nghiệm sửa chính tả/ngữ pháp
|   `-- voice/                # Khung module STT/TTS chưa triển khai
|-- test/                     # Script nghiên cứu và thử nghiệm thủ công
`-- chatGPT-Voice-Assistant/  # Code tham khảo ban đầu
```

## Dịch vụ và thư viện được sử dụng

- NVIDIA AI Endpoints / LangChain cho LLM.
- AssemblyAI và SpeechRecognition cho speech-to-text.
- `pyttsx3` và thử nghiệm `gTTS` cho text-to-speech.
- NLTK, GingerIt và PySpellChecker cho thử nghiệm NLP.
- `.env` được nạp bằng `python-dotenv`.

Các biến môi trường được code tham chiếu:

- `NVIDIA_API_KEY`
- `Assembly_AI_KEY`
- Một số script tham khảo/thử nghiệm cũ có thể dùng `OPENAI_API_KEY`.

## Giới hạn và việc còn thiếu

- Chưa hoàn thiện success path của luồng microphone -> LLM -> loa.
- Chưa có wake word trong implementation chính.
- Chưa có `requirements.txt`, `pyproject.toml` hoặc lockfile.
- Chưa có cấu hình chọn microphone/loa/voice một cách portable; code nhập văn
  bản đang chọn cố định `voices[29]`.
- Conversation memory chỉ tồn tại trong RAM và mất khi tiến trình dừng.
- Vẫn phụ thuộc các API bên ngoài, nên chưa đạt mục tiêu hoàn toàn local/offline
  hoặc đảm bảo miễn phí.
- Chưa có tích hợp Home Assistant, MQTT, GPIO, cảm biến, camera hay thiết bị nhà
  thông minh.
- Chưa có daemon/service, Docker image hoặc quy trình tự khởi động trên Pi.
- Chưa có test tự động và CI.

## Lịch sử chính

- `59b9ee9` (2024-09-16): thêm tài liệu tham khảo về hệ thống an ninh Raspberry
  Pi và các liên kết Raspberry Pi security alarm.
- `4048bf7` (2024-09-25): tạo raw prototype cho home/voice assistant và chuyển
  trọng tâm sang hội thoại AI.
- `7e62060` (2024-09-26): thêm thử nghiệm NLP, các script STT/TTS/LLM và sắp xếp
  lại package.
- `952d25e` (2026-01-30): cập nhật `.gitignore`; không thay đổi chức năng.
