# Quyết định thiết kế (Pha 1)

- Ngôn ngữ và framework: Python 3.12, FastAPI
- ORM: SQLAlchemy 2.x
- Cơ sở dữ liệu của project Pha 1: SQLite, lưu trong file local để chạy offline; không triển khai PostgreSQL hay dịch vụ DB riêng.
- `DATABASE_URL` dùng để cấu hình vị trí file SQLite, không nhằm đổi sang một hệ quản trị khác.
- Xác thực: JWT (HS256), kiểm tra tại middleware chung
- Giá trị `type`: car, motorbike, bicycle
- Bảng giá (đ/giờ): ô tô 10.000, xe máy 3.000, xe đạp 1.000; làm tròn lên theo giờ, tối thiểu 1 giờ
- Trường lạ trong body: coi là 400
- Một biển số được phép có hai vé khác nhau trong bãi
