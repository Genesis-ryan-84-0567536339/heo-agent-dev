# 🐷 CẨM NANG HƯỚNG DẪN SỬ DỤNG HEO-AGENT (BÉ HEO) — PHIÊN BẢN v2.1
### Executive AI Assistant Suite — Zalo Edition | Core Agent: Google Antigravity (AGY) CLI

---

Chào mừng Sếp và các anh/chị đến với cuốn **Cẩm Nang Sử Dụng Toàn Diện Bé Heo (Heo-Agent v2.1)**!  
Tài liệu này được biên soạn bởi chính **Kỹ Năng Hướng Dẫn Viên Hệ Thống (`heo-agent-guide`)**, cung cấp đầy đủ các bí kíp, cú pháp lệnh và quy trình thao tác chuẩn xác nhất theo đúng phiên bản phát hành hiện tại.

---

## 📑 MỤC LỤC NHANH
1. [Khởi Động Nhanh & 5 Bước Bắt Đầu Cho Người Mới](#1-khởi-động-nhanh--5-bước-bắt-đầu-cho-người-mới)
2. [Bảng Điều Khiển Heo Console (HCS — Port 5066)](#2-bảng-điều-khiển-heo-console-hcs--port-5066)
3. [Bảng Tra Cứu Lệnh Chat Zalo (Zalo Chat Commands)](#3-bảng-tra-cứu-lệnh-chat-zalo-zalo-chat-commands)
4. [Bảng Tra Cứu Lệnh Quản Trị Hệ Thống (`heo-agent` CLI)](#4-bảng-tra-cứu-lệnh-quản-trị-hệ-thống-heo-agent-cli)
5. [Khai Thác Bộ Công Cụ Đa Phương Tiện & Nghiệp Vụ](#5-khai-thác-bộ-công-cụ-đa-phương-tiện--nghiệp-vụ)
6. [Tương Tác Nhóm & Điều Hành Chéo 2 Chiều](#6-tương-tác-nhóm--điều-hành-chéo-2-chiều)
7. [Bác Sĩ Hệ Thống (`heo-agent doctor`) & Tự Sửa Lỗi 1-Click](#7-bác-sĩ-hệ-thống-heo-agent-doctor--tự-sửa-lỗi-1-click)
8. [Tuyên Bố Miễn Trừ & Thông Tin Tác Giả](#8-tuyên-bố-miễn-trừ--thông-tin-tác-giả)

---

## 1. Khởi Động Nhanh & 5 Bước Bắt Đầu Cho Người Mới

### 🔹 Bước 1: Mở Web Console
Truy cập trình duyệt tại địa chỉ:  
👉 **`http://localhost:5066`** *(hoặc `http://<IP_MÁY_CHỦ>:5066` nếu cài trên VPS/Server)*

### 🔹 Bước 2: Chấp thuận Điều khoản (Disclaimer Lock)
* Màn hình sẽ tự động khóa và hiển thị **Tuyên Bố Miễn Trừ Trách Nhiệm**.
* Đọc kỹ các điều khoản nghiên cứu mở của tác giả Ryan.
* Tích chọn xác nhận và nhấn nút **"✅ Chấp Thuận & Bắt Đầu Sử Dụng"** để mở khóa màn hình điều khiển.

### 🔹 Bước 3: Tạo Mã PIN Quản Trị Viên (Admin PIN)
* Tại mục **"Thiết Lập Danh Xưng & Admin PIN"** ở góc dưới bên trái.
* Nhấn **"Tạo Mã PIN"**, nhập từ 4 đến 8 chữ số (ví dụ: `123456`) và nhấn **"Lưu Mã PIN"**.

### 🔹 Bước 4: Đăng nhập Zalo cho Bé Heo
* Tại thẻ **"Tài Khoản Zalo"**, nhấn nút **"Quét QR"**.
* Mở ứng dụng Zalo trên điện thoại (tài khoản dùng làm bot) $\rightarrow$ Quét mã QR trên màn hình $\rightarrow$ Chọn **"Đăng nhập trên máy tính"**.
* Web Console tự động thông báo đăng nhập thành công và kết nối tức thì.

### 🔹 Bước 5: Ghép Nối Quyền Chủ Nhân (Pairing Boss)
* Lấy Zalo cá nhân của bạn kết bạn với tài khoản Bé Heo.
* Nhắn một tin bất kỳ cho Bé Heo (ví dụ: *"Chào em"*).
* Bé Heo sẽ yêu cầu nhập mã PIN bảo mật.
* Nhắn đúng mã PIN (ví dụ: `123456`) $\rightarrow$ Bé Heo lập tức nhận diện bạn là **Sếp (Boss/Owner)** với toàn quyền điều hành!

---

## 2. Bảng Điều Khiển Heo Console (HCS — Port 5066)

* 🎛️ **Chuyển Đổi Model 1-Click:** Đổi linh hoạt giữa Gemini 3.8 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B.
* ⚡ **Tinh Chỉnh Effort:** Chọn mức suy luận Low (siêu tốc), Medium (cân bằng), hoặc High (tư duy logic chuyên sâu).
* 📊 **Kiểm Tra Quota Thời Gian Thực:** Nhận diện gói Google AI Pro/Studio, số lượt truy vấn, độ trễ và % dung lượng còn lại.
* 📲 **Quản Trị Phiên Đăng Nhập:** Quét QR đăng nhập lại hoặc Đăng xuất Zalo an toàn bất kỳ lúc nào.
* 🔄 **Icon Refresh Đa Năng:** Nằm ở góc trên bên phải, vừa làm mới dữ liệu vừa kiểm tra bản cập nhật mới nhất từ GitHub.
* 🩺 **Nút Bác Sĩ Hệ Thống:** Chạy chẩn đoán toàn diện sức khỏe hệ thống ngay trên giao diện web.
* 💬 **Widget Góp Ý (Gen-hub Ingest):** Nút tròn nổi ở góc dưới bên phải giúp gửi tin nhắn phản hồi, góp ý tính năng hoặc báo lỗi trực tiếp.

---

## 3. Bảng Tra Cứu Lệnh Chat Zalo (Zalo Chat Commands)

Khi chat 1-1 với Bé Heo, Sếp có thể sử dụng các lệnh tắt hoặc câu nói tự nhiên sau:

| Lệnh / Câu Nói | Tác Dụng & Kết Quả |
| :--- | :--- |
| `/status` hoặc `/model` | Xem model hiện tại, mức suy luận và trạng thái hạn ngạch Quota |
| `/model flash` *(hoặc `/model 3.8`)* | Chuyển sang mô hình Gemini 3.8 Flash (tốc độ cao) |
| `/model pro` *(hoặc `/model 3.1`)* | Chuyển sang Gemini 3.1 Pro (phân tích sâu, xử lý tài liệu lớn) |
| `/model sonnet` | Chuyển sang Claude Sonnet 4.6 (tư duy đa chiều phản biện) |
| `/model opus` | Chuyển sang Claude Opus 4.6 (mô hình cao cấp nhất) |
| `/effort low` | Chỉnh mức suy luận nhanh, phản hồi ngắn gọn tức thì |
| `/effort medium` | Chỉnh mức suy luận tiêu chuẩn cân bằng |
| `/effort high` | Chỉnh mức suy luận đào sâu logic, đối chiếu đa chiều |
| `/style` *(hoặc `/phongcach`)* | Xem danh sách 7 phong cách và chuyển đổi thái độ của Heo |
| `/style <tên_phong_cách>` | Đổi ngay phong cách: `macdinh`, `nghiemtuc`, `deomieng`, `chuyennghiep`, `coccan`, `troll`, `tuychinh` |
| `[Gửi file ghi âm giọng nói]` | Heo tự động dịch ra chữ và **hỏi lại xác nhận** trước khi làm việc |
| *"Heo hát một bài về..."* | Sáng tác bài hát có vần điệu, beat Ukulele/Acoustic gửi file `.mp3` |
| *"Heo vẽ ảnh..."* | Tạo ảnh nghệ thuật AI gửi trực tiếp vào khung chat Zalo |
| *"Heo lập bảng tính Excel..."* | Xuất file `.xlsx` chuẩn Corporate Navy với công thức tự động |
| *"Heo soạn thảo tờ trình/văn bản..."* | Xuất file Word `.docx` chuẩn thể thức hành chính doanh nghiệp |

---

## 4. Bảng Tra Cứu Lệnh Quản Trị Hệ Thống (`heo-agent` CLI)

Trên terminal của máy chủ hoặc máy tính đã cài đặt Heo-Agent:

```bash
# 🚀 KHỞI ĐỘNG VÀ VẬN HÀNH
heo-agent                  # Khởi động hệ thống & mở Web Console (http://localhost:5066)
heo-agent --bg             # Chạy chế độ nền Daemon 24/7 không tắt khi đóng terminal
heo-agent tui              # Mở giao diện tương tác Terminal UI
heo-agent web              # Mở riêng Bảng điều khiển Web Console

# ⚙️ GIÁM SÁT & QUẢN TRỊ
heo-agent status           # Kiểm tra trạng thái hoạt động (Zalo, Core Agent, Container)
heo-agent logs             # Xem luồng nhật ký hoạt động thời gian thực (Live logs)
heo-agent model            # Xem model hiện tại và danh sách các model khả dụng
heo-agent model pro        # Đổi ngay sang Gemini 3.1 Pro
heo-agent model flash      # Đổi ngay sang Gemini 3.8 Flash
heo-agent effort high      # Chỉnh mức độ suy luận thành High
heo-agent login-zalo       # Bật màn hình quét QR đăng nhập Zalo mới
heo-agent logout-zalo      # Đăng xuất tài khoản Zalo an toàn
heo-agent login-google     # Đồng bộ tài khoản Google cho Core Agent AGY
heo-agent restart          # Khởi động lại toàn bộ dịch vụ
heo-agent stop             # Tạm dừng an toàn toàn bộ hệ thống

# 🩺 BÁC SĨ TỰ ĐỘNG PHỤC HỒI
heo-agent doctor           # Chẩn đoán sức khỏe hệ thống 10 tiêu chuẩn
heo-agent doctor --fix     # Tự động sửa chữa và phục hồi dịch vụ 1-Click

# 🗑️ GỠ BỎ HOÀN TOÀN
heo-agent uninstall        # Khôi phục cài đặt gốc 100% (Factory Reset)
```

---

## 5. Khai Thác Bộ Công Cụ Đa Phương Tiện & Nghiệp Vụ

### 🎙️ 1. Tin nhắn thoại & Quy trình Xác nhận 2 Bước
* Khi Sếp gửi file ghi âm qua Zalo:
  * **Bước 1 (Xác nhận):** Heo dịch âm thanh thành văn bản và nhắn tin hỏi lại: *"Tai em bắt được câu nói là '...' (Tạm dịch: ...). Cho em hỏi tai em đã nghe đúng chuẩn 100% chưa ạ? Sếp thả 👍 hoặc nhắn 'đúng rồi' là em bắt tay vào làm ngay ạ!"*.
  * **Bước 2 (Thực thi):** Chỉ khi Sếp thả reaction 👍 hoặc nhắn xác nhận, Heo mới chính thức tiến hành công việc. Điều này giúp loại bỏ hoàn toàn việc làm sai do nghe nhầm âm thanh.

### 🎵 2. Phòng thu Ca khúc AI (`create_song.py`)
* Bé Heo có thể viết lời bài hát theo chủ đề Sếp yêu cầu (chúc mừng sinh nhật, cổ vũ tinh thần, tổng kết quý...).
* Tự động lồng ghép beat Ukulele/Acoustic rộn ràng, thêm hiệu ứng phòng thu vang vọng (Studio Reverb), nhạc dạo đầu và fade-out cuối bài, biến thành một file nhạc `.mp3` chất lượng cao gửi vào Zalo!

### 🎨 3. Sáng tạo Ảnh Minh Họa AI (`generate_image.py`)
* Chỉ cần mô tả: *"Heo vẽ ảnh chú heo công nghệ đeo tai nghe làm việc bên laptop"*, Heo sẽ tạo ngay ảnh minh họa sắc nét và gửi trực tiếp vào Zalo.

### 📊 4. Soạn thảo Bảng tính Corporate Navy (`.xlsx`)
* Bảng tính được căn chỉnh theo chuẩn nhận diện doanh nghiệp:
  * Header xanh đậm Corporate Navy (`#1B365D`) với chữ trắng in đậm.
  * Kẻ sọc Zebra (`#F0F4F8` và `#FFFFFF`) giúp mắt dễ theo dõi số liệu.
  * Tự động cài công thức Excel (`=SUM(...)`, `=AVERAGE(...)`), không hardcode kết quả tính toán.

### 📄 5. Soạn thảo Văn bản Doanh nghiệp Chuẩn Mực (`.docx`)
* Đầy đủ thể thức văn bản: Tờ trình, Quyết định, Biên bản họp (MoM), Công văn, Kế hoạch hành động, lưu trữ sẵn sàng trong thư mục `workspace/` và tự động gửi file đính kèm sang Zalo.

---

## 6. Tương Tác Nhóm & Điều Hành Chéo 2 Chiều

### 👥 Quy chuẩn trong Nhóm Chat:
* Bé Heo chỉ lên tiếng khi được gọi tên (`@heo`, `Heo ơi...`) hoặc được quote tin nhắn.
* Phản hồi ngắn gọn tối đa 2-3 câu lịch thiệp, khiêm tốn. Nội dung chuyên môn dài sẽ được xuất ra file `.md` hoặc `.docx` đính kèm.

### 🔄 Điều hành Chéo 2 Chiều (Cross-Channel Control):
1. **Từ chat 1-1 chỉ đạo Nhóm:**
   * Gửi tin nhắn vào nhóm: `[POST_TO_GROUP: <Tên nhóm hoặc ID> | <Nội dung>]`
   * Gỡ bỏ tin nhắn trong nhóm: `[UNDO_GROUP_MESSAGE: <Tên nhóm hoặc ID>]`
2. **Từ Nhóm báo cáo mật 1-1 cho Sếp:**
   * Khi phát hiện có thành viên trong nhóm hỏi số liệu nhạy cảm (tài chính, lương, hợp đồng mật, quyết sách quan trọng), Heo khéo léo hoãn binh trước nhóm và lập tức dùng cú pháp `[PRIVATE_ALERT_BOSS: ...]` để gửi tin nhắn riêng cho Sếp xin chỉ đạo!

---

## 7. Bác Sĩ Hệ Thống (`heo-agent doctor`) & Tự Sửa Lỗi 1-Click

Nếu hệ thống gặp sự cố (mất kết nối, container treo, xung đột cổng mạng, file cấu hình bị hỏng):
* **Cách 1 (Qua dòng lệnh):**
  ```bash
  heo-agent doctor --fix
  ```
* **Cách 2 (Qua Web Console):** Nhấn nút **🩺 Bác Sĩ** trên thanh tiêu đề của Web Console (cổng 5066).

Hệ thống sẽ tự động rà soát qua 10 tiêu chuẩn và tự động vá lỗi mà không cần phải cài đặt lại từ đầu!

---

## 8. Tuyên Bố Miễn Trừ & Thông Tin Tác Giả

* **Tác giả sáng lập & phát triển:** **Anh Cơ La (Ryan)**  
* **Email liên hệ:** [genesis.corp.os@gmail.com](mailto:genesis.corp.os@gmail.com) | **Hotline/Zalo:** [(+84)090.919.8823](tel:+84909198823)  
* **Repositories:**
  - 🔒 Private Master: [`Genesis-ryan-84-0567536339/Heo-Agent`](https://github.com/Genesis-ryan-84-0567536339/Heo-Agent)
  - 🌐 Public Community: [`Genesis-ryan-84-0567536339/heo-agent-free`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-free)
  - 🌐 Public Dev Sandbox: [`Genesis-ryan-84-0567536339/heo-agent-dev`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-dev)
* **Pháp lý:** Xem toàn văn tại tài liệu [`DISCLAIMER.md`](file:///app/DISCLAIMER.md).

---
*Chúc Sếp và các anh/chị có những trải nghiệm tuyệt vời và hiệu quả cùng Trợ lý Điều hành Bé Heo!* 🐷✨
