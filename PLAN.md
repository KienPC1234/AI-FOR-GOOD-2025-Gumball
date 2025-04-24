# AI FOR GOOD 2025 - Gumball

Kế hoạch triển khai

---

## 🎯 Nguyên tắc thiết kế tối giản

- **Tối giản hóa giao diện**: Chỉ giữ lại những thành phần cần thiết, loại bỏ các yếu tố không cần thiết để tránh làm người dùng phân tâm

- **Sử dụng không gian trắng hợp lý**: Tạo cảm giác thoáng đãng và giúp người dùng tập trung vào nội dung chính

- **Bảng màu đơn sắc**: Sử dụng các tông màu trung tính như trắng, xám, xanh nhạt để tạo cảm giác chuyên nghiệp và dễ chịu

- **Kiểu chữ rõ ràng**: Chọn font chữ dễ đọc, kích thước phù hợp để đảm bảo trải nghiệm người dùng tốt

- **Tập trung vào chức năng**: Mỗi thành phần trên giao diện phải phục vụ một mục đích cụ thể, tránh thêm các yếu tố trang trí không cần thiết

---

## 🧩 Thiết kế giao diện từng phần

### 1. Giao diện đăng nhập / đăng ký

- **Bố cục**: Sử dụng một form đơn giản với các trường: Email, Mật khẩu và nút Đăng nhập / Đăng ký.

- **Thiết kế**: Sử dụng không gian trắng rộng rãi, màu nền nhẹ nhàng để tạo cảm giác thân thiện.

- **Chức năng**: Hiển thị thông báo lỗi rõ ràng khi người dùng nhập sai thông tin.

### 2. Giao diện tải ảnh y khoa

- **Bố cục**: Khu vực kéo và thả ảnh hoặc nút chọn tệp, kèm theo hướng dẫn định dạng và kích thước ảnh.

- **Thiết kế**: Sử dụng biểu tượng đơn giản để hướng dẫn người dùng, tránh làm giao diện trở nên phức tạp.

- **Chức năng**: Hiển thị tiến trình tải lên và thông báo khi hoàn tất.

### 3. Giao diện hiển thị kết quả chẩn đoán

- **Bố cục**: Hiển thị ảnh đã tải lên cùng với kết quả chẩn đoán từ AI, bao gồm: tên bệnh, mức độ nghiêm trọng, đề xuất điều trị.

- **Thiết kế**: Sử dụng bảng hoặc thẻ thông tin để trình bày kết quả một cách rõ ràng và dễ hiểu.

- **Chức năng**: Cho phép người dùng tải xuống kết quả hoặc chia sẻ với bác sĩ.

### 4. Giao diện quản lý tài khoản và hồ sơ bệnh án

- **Bố cục**: Danh sách các lần chẩn đoán trước đây, thông tin cá nhân và tùy chọn chỉnh sửa.

- **Thiết kế**: Sử dụng bảng điều khiển đơn giản với các biểu tượng dễ hiểu để người dùng dễ dàng điều hướng.

- **Chức năng**: Cho phép người dùng cập nhật thông tin cá nhân và xem lại kết quả chẩn đoán trước đó.

---

## 🛠️ Công cụ và thư viện đề xuất

- **Framework*: Sử dụng React.js để xây dựng giao diện người dùng một cách linh hoạt và hiệu quả.

- **Thư viện UI*: Sử dụng Tailwind CSS để nhanh chóng tạo ra các giao diện đẹp mắt và responsive.

- **Thư viện HTTP*: Sử dụng Axios để thực hiện các yêu cầu HTTP đến backed.

- **Công cụ thiết kế*: Sử dụng Figma để thiết kế và chia sẻ giao diện với nhóm.

---

## 📅 Kế hoạch triển khai trong 9 ngày

| Ngày | Nhiệm vụ |
|------|----------|
| 1-2 | Thiết kế giao diện đăng nhập / đăng ký và tích hợp với backend. |
| 3-4 | Phát triển giao diện tải ảnh y khoa và xử lý tải lên. |
| 5-6 | Hiển thị kết quả chẩn đoán từ AI và thiết kế giao diện tương ứng. |
| 7   | Xây dựng giao diện quản lý tài khoản và hồ sơ bệnh án. |
| 8   | Kiểm tra, sửa lỗi và tối ưu hóa giao diện. |
| 9   | Triển khai ứng dụng và chuẩn bị tài liệu hướng dẫn sử dụng. |
