---
name: corporate-navy-sheets
description: >-
  Kỹ năng nghiệp vụ thiết kế và tự động tạo bảng tính, phân tích tài chính/kinh doanh bằng Python openpyxl theo chuẩn nhận diện Corporate Navy (#1B365D), zebra striping, công thức Excel động, định dạng tiền tệ chuyên nghiệp.
---

# Kỹ năng Thiết kế Bảng tính Doanh nghiệp (Corporate Navy Excel)

## 1. Mục tiêu
Mọi bảng tính xuất ra cho Sếp và doanh nghiệp đều phải đạt chuẩn chuyên nghiệp như một sản phẩm phân tích từ các tập đoàn hàng đầu (McKinsey/Big4), trực quan, thẩm mỹ cao và chuẩn xác về mặt kỹ thuật.

## 2. Tiêu chuẩn Thiết kế (Corporate Navy Palette)
- **Bảng màu chủ đạo:**
  - Header: Nền Xanh Navy đậm `#1B365D`, chữ trắng (`#FFFFFF`), in đậm (`bold=True`), chiều cao dòng 28-32pt.
  - Sub-header / Section: Nền `#4A777A` hoặc `#2E5B88`, chữ trắng.
  - Dòng xen kẽ (Zebra Striping): Nền `#F0F4F8` và `#FFFFFF` giúp dễ theo dõi hàng ngang.
  - Dòng Tổng cộng (Total/Summary): Nền `#D9E1F2` hoặc `#E6EEF8`, chữ đậm, viền trên đơn (`thin`), viền dưới kép (`double`).
- **Font chữ:**
  - `Arial`, `Calibri`, hoặc `Segoe UI`. Kích thước: Title 14-16pt, Header 11pt, Data 10-11pt.
- **Quy chuẩn Căn lề (Alignment):**
  - Cột Văn bản / Tên gọi: Căn trái (`left`).
  - Cột Mã số / Ngày tháng / Trạng thái: Căn giữa (`center`).
  - Cột Số liệu / Tiền tệ / Tỷ lệ: Căn phải (`right`).
- **Quy chuẩn Định dạng Số (Number Formatting):**
  - Tiền Việt Nam: `#,##0 "VNĐ"` hoặc `#,##0` (có header ghi rõ đơn vị).
  - Tiền Đô la Mỹ: `$#,##0.00`.
  - Tỷ lệ phần trăm: `0.0%` hoặc `0.00%`.
  - Ngày tháng: `YYYY-MM-DD` hoặc `DD/MM/YYYY`.
- **Nguyên tắc Công thức (BẮT BUỘC):**
  - Tuyệt đối không hardcode kết quả tính toán.
  - Luôn sử dụng công thức Excel: `=SUM(C2:C15)`, `=AVERAGE(...)`, `=IF(...)`.
- **Tự động căn chỉnh độ rộng cột (Auto-fit Columns):**
  - Phải tính toán độ dài ký tự tối đa của từng cột và cộng thêm margin 3-5 ký tự để nội dung không bao giờ bị lỗi `###` hoặc che khuất.

## 3. Quy trình thực thi
1. Viết script Python sử dụng thư viện `openpyxl`.
2. Tạo dữ liệu, áp dụng styles đầy đủ.
3. Lưu file `.xlsx` trực tiếp vào `/app/workspace/`.
4. Hệ thống sẽ tự động phát hiện và gửi đính kèm qua Zalo.
