# Parking Management — Pha 1

Backend quản lý bãi đỗ xe theo yêu cầu Pha 1: ghi nhận xe vào, tra cứu lượt xe đang gửi, lấy xe ra, xác thực JWT và lưu trạng thái qua tầng Repository. Phạm vi hiện tại không bao gồm bảng giá hoặc tính phí. Project chọn SQLite làm hệ quản trị cơ sở dữ liệu, chạy bằng file local để hỗ trợ vận hành offline.

## Trạng thái hiện tại

Repository hiện có khung thư mục theo tài liệu thiết kế, nhưng chưa hoàn chỉnh API để sử dụng: nhiều router/service/repository, `docker-compose.yml` và script load test vẫn còn rỗng. ASGI app ở `business_layer.main:app` đã có lifespan khởi tạo schema/tài khoản và health endpoint; cần cài dependencies và hoàn thiện các bước tiếp theo để vận hành toàn bộ nghiệp vụ.

## Cấu trúc hiện tại

```text
parking-management/
├── business_layer/           # Package API, middleware, service và điểm khởi động
│   ├── api/
│   ├── middleware/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── database_persistent/      # Package cấu hình DB, ORM models, repositories, seed
├── Gate_client/              # Mô phỏng Gate PC
├── loadtest/                 # Locust và runner cho Kaggle CPU
├── tests/                    # Kiểm thử
├── docs/                     # Quyết định thiết kế
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

Kiến trúc mục tiêu: `business_layer/api` → `business_layer/services` → `database_persistent/repositories`. Hai tầng dữ liệu và nghiệp vụ là package Python hợp lệ, có `__init__.py`; service nghiệp vụ không phụ thuộc framework web hoặc thư viện cơ sở dữ liệu. `Gate_client/` là client mô phỏng riêng, không phải package backend.

## Yêu cầu môi trường

- Git
- Python 3.12
- Docker Desktop và Docker Compose nếu chạy bằng container

## Cài dependencies

Từ thư mục gốc dự án:

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux / WSL

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Chỉnh `.env` theo môi trường triển khai. Thay `JWT_SECRET` bằng khóa ngẫu nhiên riêng và thay mật khẩu admin mặc định. Không commit `.env` hoặc thư mục môi trường ảo. Cấu hình được đọc tập trung từ `business_layer/config.py`; schema DB và tài khoản admin được khởi tạo trong lifespan của ứng dụng.

| Biến | Ý nghĩa | Mặc định mẫu |
|---|---|---|
| `DATABASE_URL` | Đường dẫn file SQLite local | `sqlite:///./parking.db` |
| `JWT_SECRET` | Khóa ký JWT; cần thay bằng giá trị riêng | `replace-with-a-random-secret-before-deployment` |
| `JWT_EXPIRE_SECONDS` | Thời hạn token (giây) | `3600` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Tài khoản khởi tạo | `gatekeeper` / `secret123` |

## Chạy hệ thống

Sau khi cài dependencies và tạo `.env`, có thể khởi chạy phần bootstrap hiện có bằng `python -m uvicorn business_layer.main:app --reload`. Endpoint `/health` kiểm tra app; các endpoint nghiệp vụ và Docker chưa hoàn thiện.

## Đặc tả Phase 1

- REST API JSON, base path `/api/v1`.
- `POST /api/v1/auth/login` cấp JWT.
- `POST /api/v1/parking/entries` ghi nhận xe (yêu cầu xác thực).
- `GET /api/v1/parking/entries/{ticket}` tra cứu thông tin xe đang gửi (yêu cầu xác thực, không trả phí).
- `DELETE /api/v1/parking/entries/{ticket}` lấy xe ra và xóa lượt gửi (yêu cầu xác thực, không tính phí).
- `GET /health` kiểm tra trạng thái dịch vụ.
- Loại xe: `car`, `motorbike`, `bicycle`; xe đạp không có biển số, ô tô/xe máy bắt buộc có biển số.
- Thời gian gửi xe do server ghi theo UTC.
- Tài liệu API dự kiến được cung cấp qua Swagger `/docs` và OpenAPI `/openapi.json` khi API được triển khai.

Chi tiết nghiệp vụ, response lỗi và kịch bản T01–T14 nằm trong tài liệu đề bài được cung cấp cho nhóm. Trong repo hiện chưa có bản tài liệu API hoặc mô tả bài toán trong `docs/`; chỉ có `docs/decisions.md`.
