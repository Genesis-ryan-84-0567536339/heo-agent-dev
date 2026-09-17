# 🐷 Heo-Agent (Bé Heo) — Executive AI Co-Pilot v2.1

<p align="center">
  <img src="assets/heo_avatar.png" alt="Heo-Agent Mascot" width="130" style="border-radius: 24px; box-shadow: 0 8px 30px rgba(236,72,153,0.3);">
</p>

[![Version](https://img.shields.io/badge/version-v2.1-blue.svg)](https://github.com/Genesis-ryan-84-0567536339/Heo-Agent)
[![Release Date](https://img.shields.io/badge/release-17%2F09%2F2026-green.svg)](https://github.com/Genesis-ryan-84-0567536339/Heo-Agent/releases)
[![Community](https://img.shields.io/badge/community-heo--agent--free-pink.svg)](https://github.com/Genesis-ryan-84-0567536339/heo-agent-free)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](docker-compose.yml)
[![Tác giả](https://img.shields.io/badge/tác_giả-Ryan-purple.svg)](mailto:genesis.corp.os@gmail.com)

> **Heo-Agent Executive AI Assistant Suite — Zalo Edition (Phiên bản v2.1)**  
> Trợ lý Điều hành Cấp cao (Executive Assistant / Chief of Staff) độc lập, tự trị, kết nối trực tiếp tài khoản cá nhân & nhóm chat Zalo với **Google Antigravity (AGY) CLI**.  
> Được đóng gói hoàn chỉnh bằng **Docker**, cài đặt nhanh chỉ với **1 lệnh duy nhất**, giao diện Web Dashboard **Heo-Agent Console (HCS)** chuẩn Glassmorphism và **Terminal UI (TUI)** chuyên nghiệp.

---

## 📌 Điểm Mới Nổi Bật Trên Bản Phát Hành v2.1 (Release v2.1)
* 🔐 **Mã PIN Bảo Mật Quản Trị Viên (Admin Security PIN):**
  * Thiết lập và thay đổi mã PIN 4-8 chữ số trực tiếp trên Heo Console (HCS) với thuật toán mã hóa mật mã an toàn (`SHA-256` + salt).
  * **Xác thực Chủ nhân an toàn (Owner Pairing via PIN):** Khi tài khoản kết bạn Zalo nhắn tin đầu tiên, hệ thống gửi tin nhắn yêu cầu nhập mã PIN để xác minh danh tính và cấp quyền Chủ nhân (Boss/Owner).
  * Bảo vệ các thao tác nhạy cảm trên web (Hủy ghép nối Boss, thao tác quản trị).
* ⚖️ **Quy Trình Chấp Thuận Điều Khoản & Miễn Trừ Trách Nhiệm (Disclaimer Lock):**
  * Tuyên bố miễn trừ trách nhiệm toàn diện từ tác giả **Ryan** trong tài liệu [`DISCLAIMER.md`](DISCLAIMER.md).
  * Khi khởi chạy lần đầu, giao diện HCS tự động khóa và yêu cầu người dùng đọc kỹ, đồng ý điều khoản trước khi bắt đầu sử dụng.
* 📊 **Giám Sát Quota & Nhận Diện Gói Google AI Tự Động:**
  * Tự động phát hiện và hiển thị chính xác gói dịch vụ (**Google AI Pro / Studio / Free**) từ tài khoản Google đang đăng nhập.
  * Thẻ hiển thị trực quan hạn ngạch (Quota) còn lại, số lượt phản hồi, tốc độ phản hồi trung bình cho từng mô hình AI.
* 📲 **Tối Ưu Hóa Quét Mã QR Zalo & Đăng Xuất An Toàn:**
  * Cơ chế tạo mã QR độc lập với thanh tiến trình và tự động kiểm tra trạng thái đăng nhập theo thời gian thực.
  * Nút Đăng xuất Zalo an toàn, xóa sạch session và giải phóng kết nối tức thì.

---

## 🧠 Kiến Trúc Core Agent: Google Antigravity CLI (The Central Intelligence)

Hệ thống **Heo-Agent (Bé Heo)** được xây dựng trên kiến trúc **Module Phân Lớp Độc Lập**, trong đó:

> 🎯 **Google Antigravity (AGY) CLI chính thức được định danh là CORE AGENT (Bộ Não Trí Tuệ & Điều Phối Trung Tâm)** của toàn bộ hệ thống.

```text
       ┌─────────────────────────────────────────────────────────────┐
       │                 NGƯỜI DÙNG & CHỦ SỞ HỮU                     │
       │    (Ứng dụng Zalo Mobile/PC  •  Web Console HCS 5066)       │
       └──────────────────────────────┬──────────────────────────────┘
                                      │ (Tin nhắn, Voice, Lệnh)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                  TẦNG KẾT NỐI & ĐIỀU PHỐI                   │
       │   • Zalo Bridge (zca-js WebSocket - Port 5051)              │
       │   • AI Engine Orchestrator (Python HTTP Server - Port 5066) │
       └──────────────────────────────┬──────────────────────────────┘
                                      │ (Ngữ cảnh hội thoại, Nhiệm vụ)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │            🧠 CORE AGENT: GOOGLE ANTIGRAVITY CLI            │
       │                                                             │
       │   • Suy luận logic đa tầng (Gemini 3.8 / Pro, Claude...)    │
       │   • Tự trị thực thi công cụ (Autonomous Tool Execution)     │
       │   • Nạp động bộ kỹ năng điều hành (Progressive Skills)      │
       │   • Điều phối công cụ đa phương tiện (STT, TTS, Image, Song)│
       │   • Tự sinh bảng tính Excel, văn bản Word vào workspace/    │
       └─────────────────────────────────────────────────────────────┘
```

### 5 Trụ Cột Của Core Agent (Google Antigravity CLI):
1. **Trí tuệ suy luận đa mô hình (Multi-Model Intelligence):** Khai thác tối đa sức mạnh tính toán từ các mô hình AI tiên tiến (*Gemini 3.8 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B*).
2. **Quyền năng tự trị (Autonomous Tool Execution):** Core Agent tự phân tích yêu cầu, tự lựa chọn script cần thực thi (`create_song.py`, `generate_image.py`, `corporate_sheet_builder.py`), tự viết mã và tự kiểm tra kết quả mà không cần can thiệp thủ công.
3. **Cơ chế nạp kỹ năng tiến trình (Progressive Skills Discovery):** Tự động phát hiện và nạp động 7 kỹ năng điều hành tại thư mục `skills/` theo nhu cầu thực tế.
4. **Hệ thống quy chuẩn phân tầng (Hierarchical Rules):** Tuân thủ tuyệt đối quy tắc ứng xử con người (`workspace/AGENTS.md`) và bảo mật thông tin nội bộ của Sếp.
5. **Tính mở & Độc lập kiến trúc (Modular Extensibility):** Tầng kết nối Zalo và Web HCS hoàn toàn tách biệt với Core Agent. Thiết kế này giúp hệ thống dễ dàng nâng cấp Core Agent hoặc mở rộng kết nối sang các kênh tương tác khác trong tương lai.

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
curl -fsSL https://raw.githubusercontent.com/Genesis-ryan-84-0567536339/heo-agent-free/main/install.sh | bash
```

> [!NOTE]
> **Tiêu chuẩn hóa 100% trên Docker Engine:** Hệ thống sử dụng Docker Engine và Docker Compose v2 chính thức để đảm bảo tính tương thích và hoạt động ổn định trên mọi hệ điều hành. Nếu máy chủ chưa có Docker (hoặc đang dùng Podman giả lập), bộ cài đặt sẽ tự động thiết lập Docker CE chính thức cho bạn chỉ với 1 cú nhấn phím `Enter`.

Trình cài đặt tự động:
1. Kiểm tra và thiết lập môi trường Docker Engine & Docker Compose v2 tiêu chuẩn.
2. Tải mã nguồn và chuẩn bị binary `agy`.
3. Tự động đóng gói Docker Container (`heo-agent:latest`).
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

## 🌐 Bảng Điều Khiển Heo Console (HCS — Web Dashboard)

Giao diện Web Dashboard hiện đại chuẩn **Glassmorphism**, vận hành độc lập tại cổng `5066`:

👉 **`http://localhost:5066`** *(hoặc `http://<IP_MÁY_CHỦ>:5066`)*

### Các tính năng cốt lõi trên Heo Console:
* ⚖️ **Cổng Chấp Thuận Điều Khoản:** Tự động hiển thị và yêu cầu người dùng xác nhận Tuyên bố miễn trừ trách nhiệm khi khởi động lần đầu.
* 🔐 **Bảo Mật Quản Trị & Mã PIN:** Thiết lập mã PIN bảo mật 4-8 số để bảo vệ việc ghép nối Chủ sở hữu (Owner Pairing) và hủy ghép nối an toàn.
* 🎛️ **1-Click Đổi Mô Hình AI:** Chuyển đổi linh hoạt giữa *Gemini 3.8 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B*.
* ⚡ **1-Click Tinh Chỉnh Mức Suy Luận (Effort):** Tùy chỉnh mức độ tư duy *Low (Siêu tốc), Medium (Cân bằng), High (Đào sâu bản chất)*.
* 📊 **Giám Sát Quota & Hiệu Năng Thời Gian Thực:** Nút *"Kiểm Tra Quota Ngay"*, hiển thị % Quota còn lại, số lượt phản hồi và độ trễ trung bình của từng model.
* 📲 **Quản Trị Phiên Đăng Nhập:** Quét mã QR Zalo trực tiếp trong popup với cơ chế tự động kết nối, đổi tài khoản Google AGY và đăng xuất an toàn.
* 📜 **Live Stream Terminal Logs:** Cửa sổ nhật ký thời gian thực hỗ trợ lọc theo *AI Engine* hoặc *Zalo Bridge*.

---

## 📖 Hướng Dẫn Sử Dụng Chi Tiết Từ A Đến Z (User Manual)

### 1. Khởi Chạy Lần Đầu & Đọc Chấp Thuận Điều Khoản (Disclaimer)
1. Sau khi cài đặt hoàn tất, truy cập vào đường link **`http://localhost:5066`** trên trình duyệt web.
2. Hộp thoại **"Tuyên Bố Miễn Trừ Trách Nhiệm & Điều Khoản Sử Dụng"** sẽ tự động hiển thị ở chế độ khóa màn hình.
3. Người dùng đọc kỹ các điều khoản về:
   - Mục đích nghiên cứu & học tập mở của phần mềm.
   - Cam kết miễn trừ trách nhiệm toàn diện của tác giả **Ryan** đối với mọi rủi ro tài khoản hoặc nội dung AI.
   - Trách nhiệm của người dùng trong việc tuân thủ pháp luật và điều khoản bên thứ ba.
4. Tích chọn vào ô: *"Tôi xác nhận đã đọc kỹ, hiểu rõ và chấp thuận vô điều kiện toàn bộ Điều khoản sử dụng & Tuyên bố miễn trừ mọi trách nhiệm..."*.
5. Bấm nút **"✅ Chấp Thuận & Bắt Đầu Sử Dụng"** để mở khóa toàn bộ giao diện điều khiển.

---

### 2. Thiết Lập Mã PIN Bảo Mật (Admin Security PIN)
1. Tại thẻ **"Thiết Lập Danh Xưng & Admin PIN"** ở góc dưới bên trái màn hình HCS:
2. Bấm nút **"Tạo Mã PIN"** (hoặc **"Đổi Mã PIN"**).
3. Nhập mã PIN bảo mật (từ 4 đến 8 chữ số, ví dụ: `123456`) và bấm **"Lưu Mã PIN"**.
4. Hệ thống sẽ mã hóa và lưu trữ an toàn mã PIN này.

---

### 3. Đăng Nhập Tài Khoản Zalo Cho Bé Heo
1. Trên thẻ **"TÀI KHOẢN ZALO"**, bấm nút **"Quét QR"**.
2. Một hộp thoại popup sẽ hiển thị mã QR Code kèm vòng tròn tiến trình tải:
   - Mở ứng dụng Zalo trên điện thoại của tài khoản dùng làm Bé Heo.
   - Nhấn biểu tượng Quét mã QR $\rightarrow$ Quét mã trên màn hình máy tính $\rightarrow$ Chọn **"Đăng nhập trên máy tính"**.
3. Hệ thống sẽ tự động nhận diện kết nối thành công, hiển thị thông báo chúc mừng và tự động đóng hộp thoại sau 2 giây.

---

### 4. Ghép Nối Quyền Chủ Nhân (Pairing Owner / Boss)
Sau khi Bé Heo đã online Zalo:
1. Tài khoản Zalo cá nhân của bạn (người muốn làm Chủ nhân/Sếp) cần **kết bạn Zalo** với tài khoản của Bé Heo.
2. Từ Zalo cá nhân, bạn gửi một tin nhắn bất kỳ cho Bé Heo (ví dụ: *"Chào em"*).
3. Bé Heo sẽ tự động phản hồi lại:
   > 🔐 *Xin chào! Để xác thực quyền Sếp (Chủ sở hữu), vui lòng nhập mã PIN bảo mật của hệ thống:*
4. Bạn chỉ cần gửi tin nhắn chứa đúng mã PIN (ví dụ: `123456`).
5. Bé Heo sẽ lập tức xác thực thành công, ghi nhận tài khoản của bạn là **Chủ nhân (Boss)** với toàn quyền điều hành!

---

### 5. Điều Khiển Bằng Tin Nhắn Chat Zalo
Sau khi đã được ghép nối làm Sếp, bạn có thể ra lệnh cho Bé Heo mọi lúc mọi nơi ngay trên khung chat Zalo:

| Lệnh Chat Zalo | Ý Nghĩa / Tác Dụng |
| :--- | :--- |
| `/status` hoặc `/model` | Xem mô hình đang dùng, mức suy luận và trạng thái quota |
| `/model flash` (hoặc `/model 3.8`) | Chuyển sang mô hình Gemini 3.8 Flash (tốc độ cao) |
| `/model pro` (hoặc `/model 3.1`) | Chuyển sang mô hình Gemini 3.1 Pro (phân tích sâu, dữ liệu lớn) |
| `/model sonnet` | Chuyển sang mô hình Claude Sonnet 4.6 (tư duy logic đa chiều) |
| `/model opus` | Chuyển sang mô hình Claude Opus 4.6 (chuyên sâu nhất) |
| `/effort low` | Chỉnh mức suy luận nhanh, câu trả lời tức thì |
| `/effort medium` | Chỉnh mức suy luận tiêu chuẩn cân bằng |
| `/effort high` | Chỉnh mức suy luận đào sâu, tư duy toàn diện |
| `[Gửi file ghi âm thoại]` | Tự động chuyển voice thành văn bản, hỏi lại xác nhận trước khi làm |
| `Heo làm một bài hát...` | Tự động sáng tác lời, ghép nhạc beat Ukulele/Acoustic và gửi file audio |
| `Heo tạo cho anh một ảnh...` | Tự động sinh ảnh AI theo mô tả và gửi trực tiếp |
| `Heo lập bảng tính Excel...` | Xuất bảng tính `.xlsx` chuẩn Corporate Navy với công thức tự động |
| `Heo soạn thảo tờ trình/biên bản...` | Xuất file Word `.docx` chuẩn thể thức văn bản hành chính |

---

## 🎮 Điều Hành Nhanh Bằng Lệnh `heo-agent` (hoặc `heo-zalo`)

Sau khi cài đặt, hệ thống tự động đăng ký lệnh `heo-agent` (và bí danh `heo-zalo`) vào `PATH` toàn hệ thống:

```bash
# === Quản Trị & Vận Hành ===
heo-agent web              # Mở đường link giao diện Web Dashboard (http://localhost:5066)
heo-agent                  # Mở giao diện tương tác Terminal TUI Dashboard
heo-agent --bg             # Khởi chạy chế độ nền (Daemon 24/7) trong Docker
heo-agent status           # Kiểm tra trạng thái hoạt động của hệ thống
heo-agent logs             # Xem luồng nhật ký thời gian thực (live stream logs)
heo-agent restart          # Khởi động lại toàn bộ dịch vụ
heo-agent stop             # Dừng an toàn toàn bộ hệ thống
heo-agent uninstall        # Dọn dẹp và gỡ bỏ toàn bộ container, images, symlinks

# === Thay Đổi Model & Mức Suy Luận (Effort) ===
heo-agent model            # Xem model hiện tại và danh sách các mô hình hỗ trợ
heo-agent model pro        # Đổi ngay sang Gemini 3.1 Pro (High)
heo-agent model sonnet     # Đổi ngay sang Claude Sonnet 4.6 (Thinking)
heo-agent model flash      # Đổi ngay sang Gemini 3.8 Flash (High/Medium)
heo-agent effort high      # Chỉnh mức độ suy luận: low (nhanh), medium (vừa), high (sâu)

# === Quản Lý Đăng Nhập / Đăng Xuất Tài Khoản ===
heo-agent logout-zalo      # Đăng xuất tài khoản Zalo hiện tại
heo-agent login-zalo       # Mở màn hình quét mã QR để đăng nhập tài khoản Zalo mới
heo-agent logout-google    # Đăng xuất tài khoản Google của AGY CLI
heo-agent login-google     # Đăng nhập tài khoản Google mới cho AGY CLI
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
heo-agent/
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

## ⚖️ Tuyên Bố Miễn Trừ Trách Nhiệm (Disclaimer of Liability)

> [!IMPORTANT]
> **THÔNG TIN TÁC GIẢ & TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM:**  
> Phần mềm này được phát triển độc lập bởi tác giả **Ryan** ([genesis.corp.os@gmail.com](mailto:genesis.corp.os@gmail.com) • [(+84)090.919.8823](tel:+84909198823)) cho mục đích nghiên cứu, học tập và trải nghiệm công nghệ AI mã nguồn mở.
> 
> * **Cung cấp nguyên trạng ("AS IS")**: Tác giả **Ryan hoàn toàn không chịu bất kỳ trách nhiệm pháp lý, trách nhiệm dân sự hay tài chính nào** đối với bất kỳ rủi ro, thiệt hại hoặc tổn thất nào phát sinh từ việc cài đặt, vận hành hoặc sử dụng phần mềm này (bao gồm các vấn đề liên quan đến tài khoản Zalo, tài khoản Google, dữ liệu cá nhân hoặc nội dung do AI tạo ra).
> * **Trách nhiệm của người dùng**: Người dùng tự chịu trách nhiệm 100% trong việc tuân thủ pháp luật và Điều khoản dịch vụ của bên thứ ba (Google ToS, Zalo ToS).
> 
> 👉 Xem toàn văn chi tiết tại tài liệu chính thức: **[`DISCLAIMER.md`](DISCLAIMER.md)** (có sẵn trong mã nguồn tải về và trên giao diện Heo Console). Khi khởi động lần đầu, người dùng bắt buộc phải đọc và bấm chấp thuận điều khoản thì mới có thể bắt đầu sử dụng.

---

## 🏷️ Thông Tin Checkpoint & Phiên Bản

* **Phiên bản chính thức:** `Heo-Agent v2.1`
* **Thời gian chốt phiên bản (Checkpoint Timestamp):** `2026-09-17 17:40:33 +07:00` (17/09/2026)
* **Git Tag:** `v2.1`
* **Kiểm duyệt an toàn thông tin (Security & Privacy Audit):** Đã rà soát và kiểm duyệt toàn diện (Zero Leak: không chứa bất kỳ Zalo UID cá nhân, cookie phiên đăng nhập, số điện thoại hay token bảo mật riêng tư nào trên Git repository).

---

## 📜 Giấy Phép & Bản Quyền

Tác giả sáng lập & phát triển: **Ryan** — `genesis.corp.os@gmail.com` • `(+84)090.919.8823`.  
Dự án: **Genesis** — Phục vụ cộng đồng tự động hóa điều hành và ứng dụng AI thực chiến.  
Giấy phép: MIT License.

