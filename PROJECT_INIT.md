# 🐷 HEO-AGENT (BÉ HEO) — HỒ SƠ KHỞI TẠO DỰ ÁN (PROJECT INIT)

* **Kiến trúc sư trưởng & Tác giả sáng lập:** **Anh Cơ La (Ryan)**
* **Email chính thức:** `genesis.corp.os@gmail.com` | **Hotline/Zalo:** `(+84)090.919.8823`
* **Hệ sinh thái:** **Genesis Corp OS**
* **Phiên bản:** `v2.1` (Cột mốc Checkpoint: `v2.1-stable-checkpoint`)
* **Ngày khởi tạo & Định hình:** 14/09/2026 - 18/09/2026

---

## 🎯 1. Tầm Nhìn & Sứ Mệnh
Heo-Agent (Bé Heo) là Trợ lý Điều hành Cấp cao (Executive AI Assistant Suite) thế hệ mới, hoạt động tự trị 24/7 trên nền tảng Zalo và giao diện Bảng điều khiển Web Console (HCS - Heo Control System).

Hệ thống được thiết kế hướng tới khả năng phục vụ toàn diện cho Chủ nhân (Sếp Ryan / Anh Cơ La), đồng thời đóng vai trò trợ lý chuyên nghiệp, thông minh, lịch thiệp trong các nhóm làm việc chung.

---

## 🏗️ 2. Kiến Trúc & Công Nghệ Cốt Lõi
1. **Container Engine & Ảo hóa:**
   - Hỗ trợ toàn diện cả **Docker Engine** và **Podman** (Fedora / RHEL / CentOS / Ubuntu / Debian / macOS / Windows WSL2).
   - Đóng gói chuẩn OCI Container, bind-mount phân tách dữ liệu an toàn (`assets`, `data`, `auth`, `config`, `logs`, `workspace`).
2. **AI Engine & Đa Mô Hình (Multi-Model Hub):**
   - Hỗ trợ luân chuyển mượt mà giữa các dòng mô hình hàng đầu: Gemini 3.8 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6 Thinking, Claude Opus 4.6, GPT-OSS 120B.
   - Cơ chế Multi-Key Quota Failover tự động chuyển đổi khi hết hạn mức.
3. **Zalo Bridge 2 Chiều:**
   - Kết nối trực tiếp qua Zalo Client API, hỗ trợ đăng nhập QR Code 1 chạm, tự động phục hồi phiên kết nối.
   - Cơ chế nhận diện nhóm thông minh: **Chỉ phản hồi khi được @tag tên**.
4. **Hệ Thống 7 Phong Cách Thái Độ (Persona Styles):**
   - Mặc định, Nghiêm túc, Dẻo miệng, Chuyên nghiệp (Executive Advisor), Cọc cằn (Tsundere), Hài nhảm & Chọc ngoáy (Troll), Tùy chỉnh.

---

## 🌐 3. Hệ Thống Kho Mã Nguồn (Repository Ecosystem)
Kể từ ngày 18/09/2026, dự án được quản trị qua 3 kho mã nguồn độc lập:
1. **Master Repo (Main):** [`Genesis-ryan-84-0567536339/Heo-Agent`](https://github.com/Genesis-ryan-84-0567536339/Heo-Agent) — Bản chuẩn dự phòng tối cao.
2. **Community Repo (Free):** [`Genesis-ryan-84-0567536339/heo-agent-free`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-free) — Bản dùng thử đóng băng tại Checkpoint v2.1.
3. **Dev Repo (Laboratory):** [`Genesis-ryan-84-0567536339/heo-agent-dev`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-dev) — Không gian phát triển và nâng cấp tính năng mới.
