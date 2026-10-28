# Quyết định thiết kế (Pha 1)

- Ngôn ngữ và framework: Python 3.12, FastAPI
- ORM: SQLAlchemy 2.x
- Cơ sở dữ liệu của project Pha 1: SQLite, lưu trong file local để chạy offline; không triển khai PostgreSQL hay dịch vụ DB riêng.
- `DATABASE_URL` dùng để cấu hình vị trí file SQLite, không nhằm đổi sang một hệ quản trị khác.
- Xác thực: JWT (HS256), kiểm tra qua FastAPI dependencies ở cấp router; login và health không yêu cầu token.
- Giá trị `type`: car, motorbike, bicycle
- Phạm vi nghiệp vụ hiện tại: gửi xe và lấy xe; GET chỉ tra cứu thông tin lượt gửi.
- Không có bảng giá, cấu hình đơn giá, tính phí hoặc trường `charge` trong request/response.
- Trường lạ trong body: coi là 400
- Một biển số được phép có hai vé khác nhau trong bãi
- Persistence: SQLAlchemy 2.x với SQLite dạng file; tạo schema và seed tài khoản quản trị khi ứng dụng khởi động.
- Mật khẩu tài khoản được lưu dưới dạng bcrypt hash; secret JWT và thông tin quản trị lấy từ cấu hình môi trường, không commit `.env`.
- Thời gian `time_in` chuẩn hóa UTC; SQLite lưu giá trị UTC không timezone và adapter khôi phục timezone UTC khi đọc.
- Ticket là khóa chính của `parked_vehicles`; ràng buộc DB kiểm tra loại xe, độ dài ticket/plate và plate theo loại xe.
