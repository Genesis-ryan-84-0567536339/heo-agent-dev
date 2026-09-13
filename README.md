# 🚀 Zalo-AGY Copilot (Bé Heo)

> **Antigravity Executive AI Co-Pilot — Zalo Edition**  
> Trợ lý Điều hành Cấp cao (Executive Assistant / Chief of Staff) độc lập, tự trị, kết nối trực tiếp tài khoản cá nhân & nhóm chat Zalo với **Google Antigravity (AGY) CLI**.  
> Được đóng gói hoàn chỉnh bằng **Docker**, cài đặt nhanh chỉ với **1 lệnh duy nhất** cùng giao diện dòng lệnh tương tác **Terminal UI (TUI)**.

---

## ✨ Điểm nổi bật & Tính năng cốt lõi (100% Feature Parity)

* 🗣️ **Năng lực Đa Ngôn Ngữ Chuẩn Bản Địa (Multilingual Mirroring):**
  * Tự động nhận diện và phản hồi tức thì bằng **Tiếng Việt**, **Tiếng Anh (English)**, **Tiếng Trung Phổ thông (普通话 - Mandarin)** và **Tiếng Quảng Đông (粵語 - Cantonese)** với đúng phong thái, từ vựng và ngữ điệu người bản xứ.
* 🎙️ **Quy Trình Xác Nhận File Ghi Âm (Voice Note Confirmation Protocol):**
  * Xử lý âm thanh song song bằng thuật toán đa luồng (**Concurrent Multi-Candidate STT**).
  * Tuân thủ quy trình 2 bước nghiêm ngặt: Khi nhận voice note, hệ thống **bắt buộc hỏi lại xác nhận nội dung và ngôn ngữ** trước khi chính thức giải quyết công việc, loại trừ 100% rủi ro nghe nhầm ý.
* 🎵 **Phòng Thu Sản Xuất Ca Khúc AI (Studio Song Producer):**
  * Tự động sáng tác và phối nhạc với beat Ukulele / Acoustic Guitar rộn ràng (`create_song.py`), hòa âm reverb phòng thu chuyên nghiệp, nhạc dạo đầu (intro) và fade-out cuối bài.
* 🔊 **Giọng Đọc AI Neural Tự Nhiên (Edge-TTS):**
  * Giọng đọc truyền cảm chuẩn nữ theo từng ngôn ngữ: Hoài My (Việt), Jenny (Anh), Xiaoxiao (Trung), HiuMaan (Quảng Đông).
* 🎨 **Sáng Tạo Hình Ảnh AI (AI Image Generator):**
  * Tạo ảnh minh họa chất lượng cao theo prompt trực tiếp gửi vào Zalo qua Flux / SDXL (`generate_image.py`).
* 📊 **Soạn Thảo Bảng Tính & Văn Bản Doanh Nghiệp Tự Động:**
  * Xuất bảng tính Excel `.xlsx` chuẩn nhận diện **Corporate Navy** (`#1B365D`), zebra striping, công thức động (`=SUM`, `=AVERAGE`).
  * Soạn thảo tài liệu Word `.docx` chuẩn thể thức hành chính: Tờ trình, Quyết định, Biên bản họp (MoM), Công văn, Kế hoạch hành động.
* 💖 **Đọc Vị Tâm Lý Qua Reaction (Sentiment Analysis):**
  * Phân tích và thấu cảm tức thời phản ứng của người dùng qua biểu tượng cảm xúc Zalo (`❤️`, `👍`, `😂`, `😮`, `😢`, `😡`, `👎`). Chế độ **Red Alert** hạ nhiệt tức thì khi gặp phẫn nộ (`😡`).
* 🧠 **Nắm Bắt Toàn Diện Bối Cảnh Trong Ngày (Same-Day Full Context):**
  * Âm thầm ghi nhận toàn bộ hội thoại và tương tác trong ngày của nhóm. Khi được gọi tên, Bé Heo nắm bắt trọn vẹn mạch sự việc mà không bao giờ hỏi lại ngơ ngác.
* 🔄 **Điều Hành Chéo 2 Chiều (Cross-Channel Control):**
  * **1-1 chỉ đạo Group:** Từ phiên riêng với Sếp, có thể ra lệnh nhắn tin hoặc gửi tài liệu vào bất kỳ nhóm nào (`[POST_TO_GROUP]`), hoặc thu hồi tin nhắn khẩn cấp (`[UNDO_GROUP_MESSAGE]`).
  * **Group báo cáo 1-1:** Tự động phát hiện yêu cầu nhạy cảm trong nhóm, khéo léo hoãn binh và bắn tin nhắn riêng cho Sếp xin ý kiến chỉ đạo (`[PRIVATE_ALERT_BOSS]`).

---

## ⚡ Cài Đặt Nhanh 1 Lệnh Duy Nhất (One-Line Install)

Chạy lệnh sau trên máy chủ Linux (Ubuntu, Debian, Fedora, CentOS... đã có Docker):

```bash
curl -fsSL https://raw.githubusercontent.com/Genesis-ryan-84-0567536339/zalo-agy/main/install.sh | bash
```

Trình cài đặt tự động:
1. Kiểm tra môi trường Docker & Docker Compose.
2. Tải mã nguồn và chuẩn bị binary `agy`.
3. Tự động đóng gói Docker Container.
4. Mở ngay **Terminal UI (TUI)** tương tác để bạn đăng nhập Google AGY và quét mã QR Zalo trên điện thoại.

---

## 🖥️ Trình Cấu Hình Trực Quan (Interactive Terminal UI)

Khi khởi động lần đầu, màn hình TUI hướng dẫn bạn 4 bước đơn giản:

```text
  _____       _             _    ______   __ 
 |__  / __ _| | ___       / \  / ___\ \ / / 
   / / / _` | |/ _ \ ___ / _ \| |  _ \ V /  
  / /_| (_| | | (_) |___/ ___ \ |_| | | |   
 |____|\__,_|_|\___/   /_/   \_\____| |_|   
    Executive AI Assistant — Powered by Google Antigravity & Zalo
```

1. **Bước 1 — Xác thực Google AGY:** Đăng nhập tài khoản Google để kích hoạt Antigravity CLI (chạy trực tiếp trong terminal).
2. **Bước 2 — Quét mã QR Zalo:** Mã QR Code hiển thị dạng ASCII ngay trên màn hình terminal; mở app Zalo trên điện thoại -> Quét mã -> Xác nhận đăng nhập.
3. **Bước 3 — Thiết lập Chủ sở hữu (Boss):** Chọn chế độ *Auto-Claim* (chỉ cần nhắn tin đầu tiên cho bot trên Zalo để bot tự nhận diện bạn là Sếp).
4. **Bước 4 — Bảng điều khiển Giám sát (Live Dashboard):** Theo dõi trạng thái hoạt động của Engine, Bridge, model phục vụ, và dòng sự kiện tin nhắn thời gian thực.

---

## 🐳 Vận Hành Bằng Docker Compose

### 1. Khởi động chạy nền 24/7 (Daemon Mode)
```bash
docker compose up -d
```

### 2. Xem nhật ký hoạt động trực tiếp (Live Logs)
```bash
docker compose logs -f
```

### 3. Mở lại giao diện tương tác TUI Dashboard
```bash
docker compose run --rm -it app tui
```

### 4. Dừng hệ thống
```bash
docker compose down
```

---

## ⚙️ Cấu Hình Dự Án (`config/config.json`)

Tệp `config/config.json` lưu trữ các thiết lập linh hoạt:

```json
{
  "boss_uid": "",
  "boss_name": "Sếp",
  "boss_caller_name": "Sếp",
  "bot_name": "Bé Heo",
  "model": "Gemini 3.8 Flash (High)",
  "bridge_port": 5051,
  "engine_port": 5066,
  "auto_claim_boss": true
}
```

* `boss_uid`: Zalo UID của tài khoản Chủ sở hữu. Để trống nếu muốn dùng tính năng tự động nhận diện (Auto-Claim).
* `boss_name`: Tên xưng hô khi trợ lý chào hỏi Sếp (ví dụ: "Sếp", "anh Nam", "chị Linh").
* `boss_caller_name`: Cách trợ lý nhắc về Sếp trước mặt người khác trong nhóm chat.
* `model`: Model AI mặc định được cấp phát qua Antigravity CLI.
* `auto_claim_boss`: Tự động nhận diện tài khoản gửi tin nhắn 1-1 đầu tiên làm Sếp.

---

## 📁 Cấu Trúc Mã Nguồn

```text
zalo-agy/
├── Dockerfile                  # Định nghĩa môi trường container chuẩn hóa
├── docker-compose.yml          # Cấu hình dịch vụ, volume mount dữ liệu và cổng
├── install.sh                  # Script cài đặt tự động 1 lệnh
├── start.sh / stop.sh          # Quản trị khởi động và dừng nhanh
├── entrypoint.sh               # Điểm vào container (hỗ trợ TUI và Daemon)
├── bridge/                     # Zalo Bridge (Node.js + zca-js)
│   ├── bot.js                  # Quản lý WebSocket Zalo, QR login, API webhook
│   └── package.json            # Thư viện phụ thuộc Node.js
├── engine/                     # AI Engine (Python)
│   ├── server.py               # HTTP Server điều phối, ngữ cảnh bối cảnh, prompt template
│   ├── agy_exec.sh             # Wrapper thực thi AGY CLI cô lập
│   └── requirements.txt        # Thư viện phụ thuộc Python
├── scripts/                    # Bộ công cụ xử lý đa phương tiện & nghiệp vụ
│   ├── generate_image.py       # Tạo ảnh minh họa AI (Flux / SDXL / Pillow)
│   ├── generate_voice.py       # Tạo tin nhắn thoại AI 4 ngôn ngữ (Edge-TTS)
│   ├── transcribe_voice.py     # Nhận diện giọng nói song song đa luồng (STT)
│   ├── create_song.py          # Sản xuất bài hát có beat Ukulele/Acoustic
│   └── send_zalo.py            # CLI tiện ích gửi tin nhắn/file
├── cli/                        # Giao diện Terminal UI
│   ├── tui.py                  # Wizard cài đặt & Dashboard thời gian thực
│   └── requirements.txt
├── workspace/                  # Thư mục sinh tài liệu, ảnh, bài hát và prompt
│   ├── AGENTS.md               # Quy chuẩn cốt lõi hành vi & tác phong Trợ lý
│   ├── GEMINI.md / CLAUDE.md   # Bản sao đồng bộ prompt cho các model
├── skills/                     # 7 Kỹ năng nghiệp vụ điều hành cấp cao
│   ├── corporate-documentation/
│   ├── corporate-navy-sheets/
│   ├── executive-reporting/
│   ├── executive-stakeholder-dossier/
│   ├── human-executive-persona/
│   ├── market-intelligence/
│   └── vietnamese-cskh-persona/
├── data/                       # Dữ liệu hoạt động (sessions, group context)
│   └── beats/                  # Nhạc beat ukulele/acoustic chuẩn bị sẵn
└── logs/                       # Nhật ký hoạt động chi tiết
```

---

## 🔒 Bảo Mật & Quyền Riêng Tư (Privacy by Design)

* 🛡️ **Zero Personal Data**: Kho mã nguồn hoàn toàn không chứa bất kỳ số điện thoại, Zalo UID, token hay lịch sử chat cá nhân nào.
* 💾 **Dữ liệu được cô lập tại chỗ**: Mọi phiên đăng nhập (`zalo_session.json`), token Google AGY và lịch sử trò chuyện đều được lưu trữ trực tiếp trong các thư mục volume tại máy chủ của bạn (`data/`, `auth/`), không gửi ra bất kỳ máy chủ bên thứ ba nào.

---

## 📜 Giấy Phép & Bản Quyền

Phát triển bởi **Genesis** — Phục vụ cộng đồng tự động hóa điều hành và ứng dụng AI thực chiến.
Giấy phép: MIT License.
