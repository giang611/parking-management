# Parking Management

Hệ thống backend quản lý bãi đỗ xe (đồ án Pha 1): ghi nhận xe vào bãi, kiểm tra xe khi ra, tính phí theo thời gian gửi và loại xe, xóa xe khỏi bãi. Dịch vụ cung cấp REST API (JSON) cho ba loại xe: ô tô, xe máy, xe đạp.

## 1. Yêu cầu môi trường

- Git
- Python 3.12.x
- Docker và Docker Compose (khi chạy bằng container)
- Visual Studio Code (khuyến nghị)

## 2. Clone repository

```bash
git clone https://github.com/hoang-van-duong-ux/parking-management.git
cd parking-management
```

## 3. Cài đặt

### Windows PowerShell

Tại thư mục gốc của dự án:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu PowerShell chặn việc kích hoạt môi trường ảo, chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Windows CMD

```cmd
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux / WSL

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 4. Cấu hình

Sao chép file mẫu thành `.env` rồi chỉnh giá trị nếu cần.

Windows:

```powershell
copy .env.example .env
```

Linux / WSL:

```bash
cp .env.example .env
```

| Biến | Ý nghĩa | Giá trị mẫu |
|---|---|---|
| `DATABASE_URL` | Chuỗi kết nối cơ sở dữ liệu | `sqlite:///./parking.db` |
| `JWT_SECRET` | Khóa bí mật ký token (bắt buộc đổi khi triển khai) | `doi-gia-tri-nay` |
| `JWT_EXPIRE_SECONDS` | Thời hạn token, tính bằng giây | `3600` |
| `ADMIN_USERNAME` | Tên đăng nhập tạo sẵn khi khởi động | `gatekeeper` |
| `ADMIN_PASSWORD` | Mật khẩu của tài khoản tạo sẵn | `secret123` |
| `RATE_CAR` | Đơn giá ô tô (đồng/giờ) | `10000` |
| `RATE_MOTORBIKE` | Đơn giá xe máy (đồng/giờ) | `3000` |
| `RATE_BICYCLE` | Đơn giá xe đạp (đồng/giờ) | `1000` |

## 5. Chạy dịch vụ

Tại thư mục gốc của dự án.

Windows (PowerShell hoặc CMD):

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Linux / WSL:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

### Kiểm tra API

Sau khi dịch vụ chạy, truy cập:

- Health check: http://127.0.0.1:8000/health
- API documentation (Swagger UI): http://127.0.0.1:8000/docs
- Đặc tả OpenAPI: http://127.0.0.1:8000/openapi.json

Dừng server bằng `Ctrl + C`.

## 6. Chạy bằng Docker

Mục này áp dụng sau khi repository có `Dockerfile` và `docker-compose.yml`.

```bash
docker compose up --build
```

Dịch vụ lắng nghe tại http://127.0.0.1:8000. Dừng bằng `Ctrl + C`, hoặc chạy `docker compose down`.

## 7. Kiểm thử

```bash
pytest -q
```

Bộ kiểm thử gồm:

- Kiểm thử nghiệp vụ và API theo các kịch bản T01 đến T14 trong tài liệu đặc tả API.
- Kiểm tra luật phân tầng: tầng nghiệp vụ (`app/service`) không được import web framework hay thư viện cơ sở dữ liệu.

## 8. Kiến trúc

Dự án chia thành ba tầng, phụ thuộc theo một chiều từ trên xuống:

```
API  ->  Nghiệp vụ  ->  Truy cập dữ liệu
```

| Tầng | Thư mục | Trách nhiệm |
|---|---|---|
| API | `app/api` | Nhận HTTP, kiểm tra token ở middleware chung, ánh xạ lỗi nghiệp vụ sang mã HTTP |
| Nghiệp vụ | `app/service` | Kiểm tra luật, tính phí, đăng nhập; chỉ phụ thuộc interface Repository, không import web framework hay thư viện DB |
| Truy cập dữ liệu | `app/repository` | Cài đặt Repository bằng ORM (SQLAlchemy) |

Cấu trúc thư mục:

```
parking-management/
├─ app/
│  ├─ api/          # router, schema, middleware xác thực
│  ├─ service/      # nghiệp vụ, tính phí, exception, interface Repository
│  ├─ repository/   # model ORM và cài đặt Repository
│  └─ main.py       # lắp ghép các tầng
├─ tests/           # kiểm thử
├─ loadtest/        # kịch bản mô phỏng Gate PC (kiểm thử tải)
├─ docs/            # tài liệu mô tả bài toán, đặc tả API, quyết định thiết kế
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 9. Tổng quan API

Base path: `/api/v1`. Dữ liệu dạng JSON. Các endpoint cần xác thực dùng header `Authorization: Bearer <access_token>`.

| Method | Đường dẫn | Chức năng | Xác thực |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Đăng nhập, nhận token | Không |
| POST | `/api/v1/parking/entries` | Gửi xe | Có |
| GET | `/api/v1/parking/entries/{ticket}` | Kiểm tra xe và xem phí tạm tính | Có |
| DELETE | `/api/v1/parking/entries/{ticket}` | Lấy xe: trả phí và xóa khỏi bãi | Có |
| GET | `/api/v1/parking/entries` | Danh sách xe trong bãi (tùy chọn) | Có |
| GET | `/health` | Kiểm tra dịch vụ sống | Không |

Các mã trả về chính:

| Mã | Ý nghĩa |
|---|---|
| 200 | Thành công, có body (ví dụ phí cần thu) |
| 204 | Gửi xe thành công, không có body |
| 400 | Sai format hoặc `type` không hợp lệ |
| 401 | Thiếu hoặc sai token, hoặc sai tài khoản đăng nhập |
| 404 | Vé hoặc biển số không có trong bãi, hoặc không khớp |
| 409 | Vé đang gắn với một xe trong bãi |
| 422 | Xe đạp có biển số, hoặc ô tô/xe máy thiếu biển số |

Chi tiết từng endpoint (request, response, ví dụ) xem file đặc tả API trong thư mục `docs/`.

### Ví dụ nhanh

```bash
# 1. Đăng nhập
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gatekeeper","password":"secret123"}'

# 2. Gửi xe (thay <TOKEN> bằng access_token nhận được)
curl -X POST http://127.0.0.1:8000/api/v1/parking/entries \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"ticket":"T0001","plate":"29A-12345","type":"car"}'

# 3. Lấy xe
curl -X DELETE -H "Authorization: Bearer <TOKEN>" \
  "http://127.0.0.1:8000/api/v1/parking/entries/T0001?type=car&plate=29A-12345"
```

## 10. Nghiệp vụ chính

- Loại xe: `car` (ô tô), `motorbike` (xe máy), `bicycle` (xe đạp).
- Xe đạp không có biển số; ô tô và xe máy bắt buộc có biển số.
- Một vé chỉ gắn với tối đa một xe đang ở trong bãi.
- Thời điểm vào do server gắn khi gửi xe thành công.
- Phí = số giờ làm tròn lên (tối thiểu 1 giờ) nhân đơn giá theo loại xe.


## 12. Công nghệ sử dụng

- Backend: Python, FastAPI, Uvicorn
- ORM và cơ sở dữ liệu: SQLAlchemy, SQLite (baseline)
- Xác thực: JWT
- Kiểm thử: pytest
- Đóng gói: Docker
- Version control: Git và GitHub
- API testing: Swagger UI của FastAPI
- IDE: Visual Studio Code

## 13. Lưu ý khi phát triển

- Không commit thư mục `.venv/` hoặc file `*.db`.
- Không commit file `.env` chứa thông tin bí mật; dùng `.env.example` làm mẫu cấu hình.
- Khi thêm dependency, cập nhật `requirements.txt`.
- Giữ tầng `app/service` không import web framework hay thư viện cơ sở dữ liệu.
- Đặt tên commit theo quy ước: `feat:`, `fix:`, `test:`, `docs:`, `chore:`.

## 14. Tài liệu

Thư mục `docs/` chứa:

- Mô tả bài toán và nghiệp vụ cơ bản.
- Đặc tả API.
- `decisions.md`: các quyết định thiết kế của Pha 1.

## 15. Thành viên

    Nguyễn Hà Giang
    Hoàng Văn Dương
    Nguyễn Văn Tấn