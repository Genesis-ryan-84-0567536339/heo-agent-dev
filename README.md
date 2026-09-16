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

Chạy lệnh sau trên bất kỳ máy chủ Linux nào (Ubuntu, Debian, Fedora, CentOS, Arch...) hoặc macOS / Windows WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/Genesis-ryan-84-0567536339/zalo-agy/main/install.sh | bash
```

> [!NOTE]
> **Tiêu chuẩn hóa 100% trên Docker Engine:** Hệ thống sử dụng Docker Engine và Docker Compose v2 chính thức để đảm bảo tính tương thích và hoạt động ổn định trên mọi hệ điều hành. Nếu máy chủ chưa có Docker (hoặc đang dùng Podman giả lập), bộ cài đặt sẽ tự động thiết lập Docker CE chính thức cho bạn chỉ với 1 cú nhấn phím `Enter`.

Trình cài đặt tự động:
1. Kiểm tra và thiết lập môi trường Docker Engine & Docker Compose v2 tiêu chuẩn.
2. Tải mã nguồn và chuẩn bị binary `agy`.
3. Tự động đóng gói Docker Container (`zalo-agy:latest`).
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

## 🌐 Giao Diện Quản Trị Web UI (Web Dashboard)

Bên cạnh giao diện Terminal UI (TUI), hệ thống tích hợp sẵn **Web Dashboard** hiện đại, trực quan tại cổng `5066`:

👉 **`http://localhost:5066`** *(hoặc `http://<IP_MÁY_CHỦ>:5066`)*

* 🎛️ **1-Click đổi Model**: Chuyển đổi tức thì giữa *Gemini 3.8 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6, Claude Opus 4.6*.
* ⚡ **1-Click đổi Effort**: Chỉnh mức suy luận logic (*Low, Medium, High*).
* 🔐 **Quản lý Tài khoản**: Đăng xuất / Đăng nhập lại Google AGY & Zalo ngay trên giao diện; quét mã QR Zalo trực tiếp trong popup.
* 📜 **Live Logs Console**: Theo dõi nhật ký luồng xử lý AI Engine và Zalo Bridge thời gian thực.
* ⚙️ **Thiết lập Sếp**: Cập nhật Boss UID, Tên gọi, Danh xưng chỉ với một cú nhấp chuột.

---

## 🎮 Điều Hành Nhanh Bằng Lệnh `heo-zalo`

Sau khi cài đặt, hệ thống tự động đăng ký lệnh `heo-zalo` vào `PATH` toàn hệ thống:

```bash
# === Quản Trị & Vận Hành ===
heo-zalo web              # Mở đường link giao diện Web Dashboard (http://localhost:5066)
heo-zalo                  # Mở giao diện tương tác Terminal TUI Dashboard
heo-zalo --bg             # Khởi chạy chế độ nền (Daemon 24/7) trong Docker
heo-zalo status           # Kiểm tra trạng thái hoạt động của hệ thống
heo-zalo logs             # Xem luồng nhật ký thời gian thực (live stream logs)
heo-zalo restart          # Khởi động lại toàn bộ dịch vụ
heo-zalo stop             # Dừng an toàn toàn bộ hệ thống
heo-zalo uninstall        # Dọn dẹp và gỡ bỏ toàn bộ container, images, symlinks

# === Thay Đổi Model & Mức Suy Luận (Effort) ===
heo-zalo model            # Xem model hiện tại và danh sách các mô hình hỗ trợ
heo-zalo model pro        # Đổi ngay sang Gemini 3.1 Pro (High)
heo-zalo model sonnet     # Đổi ngay sang Claude Sonnet 4.6 (Thinking)
heo-zalo model flash      # Đổi ngay sang Gemini 3.8 Flash (High/Medium)
heo-zalo effort high      # Chỉnh mức độ suy luận: low (nhanh), medium (vừa), high (sâu)

# === Quản Lý Đăng Nhập / Đăng Xuất Tài Khoản ===
heo-zalo logout-zalo      # Đăng xuất tài khoản Zalo hiện tại
heo-zalo login-zalo       # Mở màn hình quét mã QR để đăng nhập tài khoản Zalo mới
heo-zalo logout-google    # Đăng xuất tài khoản Google của AGY CLI
heo-zalo login-google     # Đăng nhập tài khoản Google mới cho AGY CLI
```

---

## 💬 Điều Khiển Model & Effort Trực Tiếp Trong Zalo Chat

Chủ sở hữu (Boss) có thể ra lệnh thay đổi mô hình và mức suy luận ngay trong khung chat Zalo với Bé Heo:

* **Xem cấu hình hiện tại**: Nhắn `/model` hoặc `/status`.
* **Đổi mô hình nhanh**:
  * Nhắn: `/model flash` (hoặc `/model 3.8`) &rarr; Chuyển về Gemini 3.8 Flash siêu tốc.
  * Nhắn: `/model pro` (hoặc `/model 3.1`) &rarr; Chuyển sang Gemini 3.1 Pro xử lý tài liệu lớn, lập trình phức tạp.
  * Nhắn: `/model sonnet` &rarr; Chuyển sang Claude Sonnet 4.6 tư duy phản biện.
  * Nhắn: `/model opus` &rarr; Chuyển sang Claude Opus 4.6 cao cấp nhất.
  * *(Hỗ trợ cả câu nói tự nhiên: "Heo đổi sang model pro", "chuyển model sonnet").*
* **Đổi mức suy luận (Effort)**:
  * Nhắn: `/effort low` &rarr; Suy luận ngắn gọn, tốc độ tối đa.
  * Nhắn: `/effort medium` &rarr; Mức cân bằng chuẩn.
  * Nhắn: `/effort high` &rarr; Đào sâu bản chất, tư duy logic chuyên sâu.

---

## 🐳 Vận Hành Trực Tiếp Bằng Docker Compose

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
docker compose run --rm app tui
```

### 4. Dừng hệ thống
```bash
docker compose down
```

### 5. Dọn dẹp / Gỡ bỏ hoàn toàn
```bash
./uninstall.sh
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
