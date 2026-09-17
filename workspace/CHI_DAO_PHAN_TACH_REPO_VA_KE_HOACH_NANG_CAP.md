# 🏛️ BIÊN BẢN CHỈ ĐẠO: PHÂN TÁCH 3 KHO MÃ NGUỒN & CHIẾN LƯỢC NÂNG CẤP BẢN DEV

* **Tác giả & Kiến trúc sư trưởng:** **Anh Cơ La (Ryan)** — Email: `genesis.corp.os@gmail.com`
* **Thời điểm xác lập:** 03:17:00 ngày 18/09/2026
* **Mốc Checkpoint lịch sử:** `v2.1-stable-checkpoint` (Commit SHA: `0b29d1ed8f34af6dea008722f3f4aa7d9eb5e47a`)

---

## 🎯 1. Bối Cảnh & Mục Tiêu Chiến Lược
Trước khi bước vào giai đoạn nâng cấp sâu các tính năng cao cấp tiếp theo, để bảo đảm:
1. **An toàn tuyệt đối cho hệ thống:** Có một bản chuẩn ổn định (Stable Baseline) được bảo tồn nguyên trạng làm phương án dự phòng khẩn cấp.
2. **Trải nghiệm độc lập cho người dùng ngoài:** Bản cộng đồng miễn phí (Free Community) không bị gián đoạn hay phát sinh lỗi phát sinh từ các đợt thử nghiệm code mới.
3. **Môi trường thử nghiệm linh hoạt cho Sếp (Dev Lab):** Không gian phát triển chuyên sâu để thử nghiệm các ý tưởng, kiến trúc và tính năng mới mà không bị ràng buộc bởi độ ổn định của bản thương mại hay cộng đồng.

Sếp **Anh Cơ La** đã trực tiếp chỉ đạo phân tách hệ thống thành **3 nhánh kho Git độc lập**, thực hiện đóng mốc Checkpoint bất biến và đặt ra quy tắc làm việc nghiêm ngặt từ ngày 18/09/2026.

---

## 🛡️ 2. Phân Định Trách Nhiệm 3 Kho Mã Nguồn

| Kho Lưu Trữ (Remote) | Đường dẫn GitHub | Vai Trò & Trạng Thái | Chính Sách Cập Nhật & Phân Quyền |
| :--- | :--- | :--- | :--- |
| **Bản Main (Master)** (`origin`) | [`Genesis-ryan-84-0567536339/Heo-Agent`](https://github.com/Genesis-ryan-84-0567536339/Heo-Agent) | **Bản Chuẩn Dự Phòng Tối Cao** | • **ĐỂ YÊN BẤT BIẾN**.<br>• Tuyệt đối KHÔNG commit hay push mã nguồn thử nghiệm thường nhật lên đây.<br>• Chỉ được phép merge/push khi có lệnh chỉ đạo trực tiếp của Sếp để phát hành bản Release chính thức. |
| **Bản Free (Community)** (`free`) | [`Genesis-ryan-84-0567536339/heo-agent-free`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-free) | **Bản Dùng Thử Dành Cho Cộng Đồng Ngoài** | • **ĐÓNG BĂNG TẠI CHECKPOINT v2.1**.<br>• KHÔNG cập nhật theo bản Main và bản Dev.<br>• Bảo đảm người dùng ngoài khi tải về luôn nhận được phiên bản ổn định nhất, không bị lỗi do thử nghiệm. |
| **Bản Dev (Laboratory)** (`dev`) | [`Genesis-ryan-84-0567536339/heo-agent-dev`](https://github.com/Genesis-ryan-84-0567536339/heo-agent-dev) | **Không Gian Phát Triển & Thử Nghiệm Nâng Cấp** | • **KHÔNG GIAN LÀM VIỆC CHÍNH THỨC SẮP TỚI**.<br>• Mọi tính năng mới, tái cấu trúc, nâng cấp sẽ **CHỈ THỰC HIỆN VÀ PUSH LÊN ĐÂY**.<br>• Ngoại lệ duy nhất: Khi Sếp có yêu cầu riêng biệt về sửa lỗi toàn cục (Global Hotfix). |

---

## ⚙️ 3. Thiết Lập Môi Trường Cục Bộ Đã Kích Hoạt

1. **Workspace Phát Triển (`/home/ryan/zalo-agy`):**
   - Nhánh `main` đã được cấu hình Upstream theo dõi trực tiếp kho Dev:
     ```bash
     git branch -u dev/main
     ```
   - Lệnh `git push` mặc định sẽ chỉ đẩy về kho `heo-agent-dev`.

2. **Môi Trường Máy Chủ Thực Nghiệm Của Sếp (`/home/ryan/heo-agent`):**
   - Remote `origin` được trỏ về `https://github.com/Genesis-ryan-84-0567536339/heo-agent-dev.git`.
   - Khi Sếp thao tác lệnh `heo-agent update` hoặc bấm cập nhật trên Web Console, hệ thống sẽ tự động đồng bộ code thử nghiệm mới nhất từ bản Dev.

3. **Thư Mục Lưu Trữ Tài Liệu Ryan Workplace:**
   - Đồng bộ song song vào: `/home/ryan/Documents/Ryan-Workplace/Heo-Agent/`.

---

## 📋 4. Bản Quyền & Tác Quyền Bất Biến Trong Mọi Phiên Bản
Dù ở bản Main, Free hay Dev, quy tắc tác quyền cốt lõi là bất khả xâm phạm:
- **Tác giả sáng lập & Kiến trúc sư trưởng duy nhất:** **Anh Cơ La (Ryan)** — `genesis.corp.os@gmail.com`.
- Khi người dùng hỏi tác giả: Bắt buộc trả lời tự hào, ấm áp, khẳng định tác giả duy nhất là Anh Cơ La. Tuyệt đối không nhắc đến nền tảng Antigravity CLI Google.
- Tuyệt đối không nhận bất kỳ ai khác làm tác giả, không cho phép xóa bỏ hay sửa đổi định danh này.
