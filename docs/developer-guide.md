# Hướng dẫn cài đặt và vận hành

README ở thư mục gốc là bản giới thiệu nhanh cho người đọc dự án. Tài liệu này chứa các bước cài đặt, chạy local/Docker, dùng Gate client và tạo benchmark.

## Làm mới đặc tả API

`docs/openapi.json` được sinh từ các router và schema hiện tại. Sau khi thay đổi API, chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe scripts/export_openapi.py
```

Sau đó review và commit lại `docs/openapi.json` để bản preview trên GitHub khớp với code.

## Môi trường và cấu hình

Cần Git và Python 3.12. Docker Desktop cùng Docker Compose chỉ cần nếu chạy bằng container.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

### Linux / WSL

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Chỉnh `.env` theo môi trường trước khi chạy. Thay `JWT_SECRET` bằng khóa ngẫu nhiên và đổi mật khẩu quản trị mẫu. Không commit `.env` hoặc virtualenv.

| Biến | Ý nghĩa | Giá trị mẫu |
|---|---|---|
| `DATABASE_URL` | Vị trí file SQLite | `sqlite:///./parking.db` |
| `JWT_SECRET` | Khóa ký JWT | Thay giá trị placeholder trong `.env.example` |
| `JWT_EXPIRE_SECONDS` | Thời hạn token tính bằng giây | `3600` |
| `ADMIN_USERNAME` | Tên tài khoản quản trị được tạo lúc khởi động | `gatekeeper` |
| `ADMIN_PASSWORD` | Mật khẩu khởi tạo | `secret123` (chỉ dùng mẫu local) |

## Chạy local

Từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m uvicorn business_layer.main:app --reload
```

Kiểm tra `http://127.0.0.1:8000/health`; xem/thử API tại `http://127.0.0.1:8000/docs`.

## Chạy Docker Compose

Đảm bảo `.env` đã có và secret/mật khẩu mẫu được thay trước khi chạy:

```powershell
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
```

SQLite nằm trong named volume `parking_data` nên tồn tại khi container được tạo lại. Xem log bằng `docker compose logs -f api`; dừng bằng `docker compose down`. Để chạy offline, cần build image và tải dependencies trước khi mất kết nối, sau đó chạy `docker compose up -d --pull never`.

## Gate client

Khi Backend đang chạy, mở terminal thứ hai và chạy:

```powershell
.\.venv\Scripts\python.exe gate_client/gate_simulation.py --base-url http://127.0.0.1:8000
```

Client hỏi tài khoản, sau đó cho phép ghi nhận, tra cứu và lấy xe. Mật khẩu được nhập ẩn. Có thể đặt `ADMIN_USERNAME`/`ADMIN_PASSWORD` trong environment thay vì nhập lại.

## Benchmark Locust trên Kaggle

Locust tách khỏi dependency của Backend. Cài trong môi trường chạy tải:

```bash
python -m pip install -r requirements-loadtest.txt
```

Đặt `ADMIN_USERNAME` và `ADMIN_PASSWORD` qua Kaggle Secrets, chạy Backend ở một cell/process khác trên cổng `8000`, rồi chạy:

```bash
BASE_URL=http://127.0.0.1:8000 USERS=10 SPAWN_RATE=2 RUN_TIME=60s \
  bash loadtest/kaggle_runner.sh
```

Runner ghi cấu hình, thông tin máy, CSV, HTML và log vào `docs/benchmarks/<run-id>/`. Có thể đổi `USERS`, `SPAWN_RATE`, `RUN_TIME`, `BASE_URL` và `RESULTS_DIR`. Khi so sánh kết quả, ghi nhận API và Locust có dùng chung máy Kaggle hay không. Baseline đã lưu tại [`benchmarks/20261028T182659Z-m8jDvhHE/`](benchmarks/20261028T182659Z-m8jDvhHE/); console cuối và CSV có thể lệch nhẹ vì Locust cập nhật CSV theo chu kỳ.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Trên Linux/WSL, dùng `.venv/bin/python -m pytest -q`.

Test tạo SQLite tạm, bao phủ API, xác thực, quy tắc nghiệp vụ, repository, xử lý đồng thời và OpenAPI. Các dependency cài qua `requirements.txt` là đủ để chạy toàn bộ suite; `requirements-loadtest.txt` chỉ cần để tự chạy Locust.
