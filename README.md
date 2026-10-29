# Parking Management — Phase 1

Backend mô phỏng hệ thống quản lý bãi gửi xe. Tài liệu này giúp nhóm khác nắm nhanh bài toán, nghiệp vụ, cách tổ chức mã nguồn và yêu cầu kỹ thuật. Hướng dẫn cài đặt chi tiết nằm trong [Developer Guide](docs/developer-guide.md).

## Bài toán

Nhân viên tại cổng cần ghi nhận xe vào bãi, xác định một lượt gửi còn hiệu lực, tra cứu khi khách hỏi và xác nhận đúng xe trước khi cho ra. Hệ thống phải tránh dùng trùng mã vé, bảo vệ thao tác nghiệp vụ bằng đăng nhập và giữ trạng thái gửi xe sau khi Backend khởi động lại.

Phase 1 chỉ theo dõi **xe đang gửi**. Hệ thống không quản lý giá, tính phí, thanh toán hoặc lịch sử giao dịch sau khi xe đã được lấy ra.

## Nghiệp vụ chính

1. Nhân viên đăng nhập và nhận JWT.
2. Khi xe vào, Gate gửi mã vé, loại xe và biển số nếu cần.
3. Nhân viên có thể liệt kê xe đang gửi hoặc tra cứu một vé. Tra cứu chỉ đọc, không thay đổi dữ liệu.
4. Khi xe ra, Gate gửi vé cùng thông tin nhận dạng; Backend xác nhận khớp rồi xóa lượt gửi.

Quy tắc dữ liệu: loại xe là `car`, `motorbike` hoặc `bicycle`; xe đạp không có biển số, ô tô/xe máy bắt buộc có biển số. Mỗi vé chỉ có một lượt đang hoạt động. Biển số được chuẩn hóa thành chữ hoa; thời gian vào bãi lưu theo UTC.

## Thiết kế kỹ thuật

- **Backend:** Python 3.12, FastAPI và Pydantic; REST API trả JSON.
- **Lưu trữ:** SQLite qua SQLAlchemy, dùng file local để triển khai gọn và chạy trong LAN/offline.
- **Bảo vệ API:** JWT HS256; các route bãi xe yêu cầu `Authorization: Bearer <token>`. Mật khẩu quản trị được băm bcrypt.
- **Kiến trúc:** API → service nghiệp vụ → repository → SQLite. Service nghiệp vụ thuần Python phụ thuộc giao diện repository, không phụ thuộc FastAPI hay SQLAlchemy.
- **Triển khai:** Docker Compose lưu DB trong named volume; có Gate client mô phỏng và kịch bản Locust để thử tải.

| Thành phần | Trách nhiệm |
|---|---|
| `business_layer/api/` | Nhận request, áp dụng schema và trả response |
| `business_layer/services/` | Luật đăng nhập, gửi xe, tra cứu và lấy xe |
| `business_layer/security.py` | Kiểm tra Bearer JWT |
| `database_persistent/models/` | Bảng tài khoản và lượt xe |
| `database_persistent/repositories/` | Đọc/ghi SQLite qua SQLAlchemy |
| `gate_client/` | Mô phỏng thao tác tại cổng |
| `loadtest/` | Kịch bản và runner benchmark |

Sơ đồ luồng, ERD và giải thích từng module xem tại [docs/architecture.md](docs/architecture.md).

## API

Base path là `/api/v1`. Đặc tả OpenAPI JSON có thể xem trực tiếp trên GitHub tại [`docs/openapi.json`](docs/openapi.json); khi chạy hệ thống, Swagger nằm ở `/docs` và bản OpenAPI động ở `/openapi.json`. Sau khi sửa API, sinh lại tệp bằng `python scripts/export_openapi.py`.

| Method | Endpoint | Mục đích | Xác thực |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Đăng nhập, cấp JWT | Không |
| `POST` | `/api/v1/parking/entries` | Ghi nhận xe vào | Bearer |
| `GET` | `/api/v1/parking/entries?limit=50&offset=0` | Liệt kê lượt gửi có phân trang | Bearer |
| `GET` | `/api/v1/parking/entries/{ticket}` | Tra cứu, không xóa lượt gửi | Bearer |
| `DELETE` | `/api/v1/parking/entries/{ticket}` | Lấy xe ra và xóa lượt gửi | Bearer |
| `GET` | `/health` | Kiểm tra trạng thái dịch vụ | Không |

Lỗi API có dạng `{"error":"CODE"}`. Mã lỗi/HTTP, request và response đầy đủ nằm trong OpenAPI JSON. Hai tài liệu yêu cầu gốc được giữ tại [docs/specifications](docs/specifications/README.md).

## Chạy nhanh

Cần Git và Python 3.12. Từ PowerShell tại thư mục repo:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Thay `JWT_SECRET` và mật khẩu quản trị mẫu trong `.env`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe -m uvicorn business_layer.main:app --reload
```

Mở `http://127.0.0.1:8000/docs`. Để chạy đủ test: `.\.venv\Scripts\python.exe -m pytest -q`. Cách chạy Docker, Gate client và benchmark Kaggle xem [Developer Guide](docs/developer-guide.md). Baseline benchmark được lưu tại [docs/benchmarks](docs/benchmarks/README.md).

## Gợi ý giới thiệu trong 5–7 phút

Trình bày lần lượt: vấn đề tại cổng → luồng gửi/tra cứu/lấy xe → quy tắc vé/biển số và phần không bao gồm giá → các tầng API/service/repository → demo Swagger hoặc Gate client. Vấn đề kỹ thuật đáng chú ý là chống trùng vé khi có request đồng thời, kiểm tra token trước nghiệp vụ, chuẩn hóa UTC và giữ dữ liệu SQLite qua lần khởi động lại.
