# Hệ thống quản lý bãi đỗ xe

Dự án Python mô phỏng hệ thống quản lý bãi đỗ xe, hỗ trợ ghi nhận xe vào bãi, tra cứu phí, xác nhận thanh toán và thống kê doanh thu. Các thành phần giao tiếp qua giao thức TCP tự định nghĩa, sử dụng thông điệp văn bản theo từng dòng; giao thức tuân theo REST nhưng không phải HTTP.

## 1. Kiến trúc dự án

Dự án được chia thành các module với trách nhiệm riêng:

- `network.py`: gửi và nhận thông điệp qua kết nối TCP.
- `main.py`: phân tích request, kiểm tra mật khẩu xác thực trên từng request và chuyển yêu cầu đến tầng xử lý phù hợp.
- `business.py`: kiểm tra dữ liệu đầu vào, áp dụng quy tắc nghiệp vụ, tính phí và xác định khoảng thời gian thống kê doanh thu.
- `database.py`: thao tác với cơ sở dữ liệu SQLite.
- `client.py`: giao diện dòng lệnh để nhân viên thao tác với hệ thống.
- `config.json`: cấu hình địa chỉ và cổng server, mật khẩu, giá gửi xe theo giờ và tên file cơ sở dữ liệu.
- `api_spec.json`: đặc tả giao thức, định dạng request/response và các mã trạng thái.
- `tests/`: các bài kiểm thử tự động.
- `Dockerfile`: cấu hình đóng gói ứng dụng bằng Docker.

Tầng nghiệp vụ không trực tiếp xử lý socket hoặc câu lệnh SQL. Các thao tác lưu trữ được chuyển cho `database.py`.

## 2. Cài đặt và chạy

Yêu cầu Python 3. Ứng dụng cơ bản không cần cài thêm thư viện bên ngoài.

Mở terminal thứ nhất và chạy server:

```bash
python main.py
```

Mở terminal thứ hai và chạy client:

```bash
python client.py
```

Cấu hình mặc định sử dụng mật khẩu `123` và cổng TCP `8765`. Các giá trị có thể thay đổi trong `config.json`. Khi client chạy trên máy khác trong cùng mạng LAN, hãy nhập địa chỉ IP LAN của máy chạy server và bảo đảm cổng TCP được phép kết nối.

## 3. Giao thức và chức năng API

Mỗi request là một dòng văn bản UTF-8 kết thúc bằng ký tự xuống dòng (`\n`). Server trả về một dòng phản hồi theo định dạng `STATUS/JSON`. Mã `204` biểu thị thao tác thành công không có dữ liệu trả về (`204/{}`). Các request nghiệp vụ cần kèm mật khẩu xác thực.

Ví dụ các request:

```text
POST/auth/123
POST/vehicle/{"ticket":1001,"plate":"30A-12345","type":"CAR"}/auth/123
GET/vehicle/{"ticket":1001,"plate":"30A-12345","type":"CAR"}/auth/123
DELETE/vehicle/{"ticket":1001}/auth/123
GET/revenue/today/auth/123
```

Các chức năng chính:

- **Kiểm tra mật khẩu:** xác nhận mật khẩu truy cập.
- **Ghi nhận xe vào bãi:** lưu mã vé, biển số (nếu có), loại xe và thời điểm vào.
- **Tra cứu xe và phí:** kiểm tra thông tin vé, trả về thời gian tính phí và số tiền cần thanh toán.
- **Xác nhận thanh toán:** ghi nhận doanh thu và xóa vé đang hoạt động.
- **Thống kê doanh thu:** truy vấn doanh thu theo ngày, tuần hoặc tháng.

Các loại xe hợp lệ là `CAR`, `MOTORCYCLE` và `BICYCLE`. Xe đạp không có biển số; ô tô và xe máy phải có biển số. Các kỳ thống kê gồm `today`, `yesterday`, `this-week`, `last-week`, `this-month` và `last-month`. Xem `api_spec.json` để biết đầy đủ cú pháp raw text, dữ liệu và mã phản hồi của từng API.

## 4. Quy tắc tính phí và thanh toán

Phí gửi xe được tính theo công thức:

```text
charge = ceil(elapsed_seconds / 3600) * hourly_rate
```

Thời gian tính phí tối thiểu là một giờ. Mức giá theo giờ được cấu hình trong `config.json`.

Quy trình thanh toán gồm hai bước:

1. Client gửi `GET/vehicle` để tra cứu và hiển thị số tiền cần thu. Request này chỉ đọc dữ liệu, không xóa vé và không ghi nhận doanh thu.
2. Sau khi nhân viên xác nhận đã nhận tiền, client gửi `DELETE/vehicle`. Server tự tính lại phí, ghi nhận thanh toán và xóa vé trong cùng một giao dịch cơ sở dữ liệu.

## 5. Chạy kiểm thử

Tại thư mục gốc của dự án, chạy:

```bash
python -m unittest discover -s tests -v
```

Dự án cũng có `Dockerfile` để đóng gói ứng dụng và chạy trong container.
