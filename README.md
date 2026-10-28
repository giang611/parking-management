# Parking Management — Pha 1

Backend quản lý bãi đỗ xe theo yêu cầu Pha 1: ghi nhận xe vào, tra cứu lượt xe đang gửi, lấy xe ra, xác thực JWT và lưu trạng thái qua tầng Repository. Phạm vi hiện tại không bao gồm bảng giá hoặc tính phí. Project chọn SQLite làm hệ quản trị cơ sở dữ liệu, chạy bằng file local để hỗ trợ vận hành offline.

## Trạng thái hiện tại

Backend Pha 1 hiện có cấu hình SQLite, model/repository, nghiệp vụ gửi xe/lấy xe, đăng nhập JWT, dependency injection, REST API, cấu hình Docker Compose, Gate client và kịch bản Locust. Các endpoint nghiệp vụ cùng `/health` được khai báo trong ASGI app `business_layer.main:app`; Swagger ở `/docs` và OpenAPI ở `/openapi.json`. Baseline Kaggle CPU đầu tiên đã được lưu trong `docs/benchmarks/`; chạy lại benchmark trên Kaggle để tạo kết quả mới cho runtime/phần cứng hiện tại.

## Cấu trúc hiện tại

```text
parking-management/
├── business_layer/           # Package API, middleware, service và điểm khởi động
│   ├── api/
│   ├── middleware/
│   ├── schemas/
│   ├── services/
│   ├── Dockerfile
│   └── main.py
├── database_persistent/      # Package cấu hình DB, ORM models, repositories, seed
├── gate_client/              # Mô phỏng Gate PC
│   └── gate_simulation.py
├── loadtest/                 # Locust và runner cho Kaggle CPU
│   ├── locustfile.py
│   └── kaggle_runner.sh
├── tests/                    # Kiểm thử
├── docs/
│   ├── architecture.md       # Kiến trúc, luồng xử lý, ERD và vận hành offline
│   ├── specifications/        # Tài liệu yêu cầu gốc của Pha 1
│   └── benchmarks/           # Baseline Kaggle và hướng dẫn đọc kết quả
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── requirements-loadtest.txt
├── .env.example
└── README.md
```

Kiến trúc mục tiêu: `business_layer/api` → `business_layer/services` → `database_persistent/repositories`. Hai tầng dữ liệu và nghiệp vụ là package Python hợp lệ, có `__init__.py`; service nghiệp vụ không phụ thuộc framework web hoặc thư viện cơ sở dữ liệu. `gate_client/` là client mô phỏng riêng, không phải package backend.

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

Sau khi cài dependencies và tạo `.env`, khởi chạy backend:

```powershell
python -m uvicorn business_layer.main:app --reload
```

Mở `http://127.0.0.1:8000/docs` để xem Swagger hoặc `http://127.0.0.1:8000/health` để kiểm tra service.

## Chạy bằng Docker Compose

Đảm bảo `.env` tồn tại và đã thay `JWT_SECRET` cùng mật khẩu quản trị mẫu. Compose truyền cấu hình từ `.env`; file này bị loại khỏi build context và không được đóng gói vào image. SQLite được lưu trong named volume `parking_data`, nên dữ liệu vẫn còn sau khi dừng và tạo lại container.

### Windows PowerShell

```powershell
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
```

### Linux / WSL

```bash
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
curl http://127.0.0.1:8000/health
```

Mở `http://127.0.0.1:8000/docs` để thử API. Xem log bằng `docker compose logs -f api` và dừng service bằng `docker compose down`. Volume dữ liệu không bị xóa khi chạy lệnh dừng này.

Để vận hành offline, build image một lần khi đã có mạng và Docker đã tải image nền cùng Python dependencies. Sau đó có thể chạy bằng `docker compose up -d --pull never`; API, JWT và SQLite đều chạy tại máy/LAN, không gọi dịch vụ bên ngoài.

Lần build đầu cần truy cập registry Docker và PyPI để tải image nền và dependencies. Sau khi build thành công, việc chạy ứng dụng không cần Internet.

## Gate client và kiểm thử tải

Chạy Gate client tương tác từ thư mục gốc project. Client hỏi thông tin đăng nhập bằng prompt ẩn cho mật khẩu, sau đó cho phép gửi xe, tra cứu hoặc lấy xe. Có thể đổi Backend URL bằng `--base-url`:

```powershell
python gate_client/gate_simulation.py --base-url http://127.0.0.1:8000
```

Cài thêm Locust trong môi trường dùng để chạy tải; dependency này không được cài vào image backend:

```bash
python -m pip install -r requirements-loadtest.txt
```

`loadtest/locustfile.py` chạy vòng đời gửi xe → tra cứu → lấy xe với ticket ngẫu nhiên cho mỗi vòng, và dọn xe ở bước cuối. Kịch bản chọn ngẫu nhiên ô tô, xe máy hoặc xe đạp; không ghi phí. Backend phải được chạy riêng và tài khoản thử phải có trong cấu hình môi trường. Đặt `ADMIN_USERNAME`, `ADMIN_PASSWORD` làm environment variables từ Kaggle Secrets, không ghi credentials vào notebook hoặc repo.

Trên Kaggle, chạy Backend tại `127.0.0.1:8000` trong một cell/process khác. Sau đó chạy từ thư mục repo:

```bash
BASE_URL=http://127.0.0.1:8000 USERS=10 SPAWN_RATE=2 RUN_TIME=60s \
  bash loadtest/kaggle_runner.sh
```

Runner kiểm tra `/health`, ghi CPU/RAM, Python, Locust, revision và cấu hình tải, rồi lưu CSV, HTML, log cùng bảng throughput/latency/failures vào `docs/benchmarks/<run-id>/`. Có thể đổi `USERS`, `SPAWN_RATE`, `RUN_TIME`, `BASE_URL` và `RESULTS_DIR` qua environment. Giá trị mặc định 10 users, spawn 2 users/giây và 60 giây phù hợp cho baseline ngắn; ghi lại cấu hình khi so sánh các lần chạy. Locust chạy trên cùng Kaggle CPU với API sẽ chia sẻ CPU với Backend, vì vậy ghi chú phần cứng và cách đặt server cùng máy trong báo cáo.

Dependencies lần đầu cần tải khi có mạng. Baseline Kaggle CPU thật đầu tiên đã được lưu tại [`docs/benchmarks/20261028T182659Z-m8jDvhHE/`](docs/benchmarks/20261028T182659Z-m8jDvhHE/). Chạy lại runner để tạo thư mục baseline mới; mỗi lượt được cấp thư mục riêng. Locust ghi CSV theo chu kỳ, nên khi kiểm tra số request cuối hãy đối chiếu cả `locust.log` và `locust_stats.csv`.

## Đặc tả Phase 1

Hai tài liệu yêu cầu gốc được lưu trong [`docs/specifications/`](docs/specifications/README.md). Kiến trúc, ERD và quyết định triển khai được mô tả tại [`docs/architecture.md`](docs/architecture.md) và [`docs/decisions.md`](docs/decisions.md). Các tài liệu này là căn cứ đối chiếu; README tóm tắt hành vi API đang được triển khai.

- REST API JSON, base path `/api/v1`.
- `POST /api/v1/auth/login` cấp JWT.
- `POST /api/v1/parking/entries` ghi nhận xe (yêu cầu xác thực).
- `GET /api/v1/parking/entries/{ticket}` tra cứu thông tin xe đang gửi (yêu cầu xác thực, không trả phí).
- `GET /api/v1/parking/entries?limit=50&offset=0` xem danh sách xe đang gửi theo trang (yêu cầu xác thực; `limit` từ 1 đến 100, mặc định 50; thứ tự theo mã vé tăng dần).
- `DELETE /api/v1/parking/entries/{ticket}` lấy xe ra và xóa lượt gửi (yêu cầu xác thực; trả `200` cùng mã vé).
- `GET /health` kiểm tra trạng thái dịch vụ.
- Loại xe: `car`, `motorbike`, `bicycle`; xe đạp không có biển số, ô tô/xe máy bắt buộc có biển số.
- Thời gian gửi xe do server ghi theo UTC.
- Swagger `/docs` và OpenAPI `/openapi.json` được tạo từ các route hiện có.

Đăng nhập thành công trả `access_token`, `token_type: "Bearer"` và `expires_in` (giây, theo `JWT_EXPIRE_SECONDS`). Các thao tác gửi xe, tra cứu, xem danh sách và lấy xe yêu cầu `Authorization: Bearer <token>` lấy từ endpoint đăng nhập. Lỗi trả JSON dạng `{"error":"CODE"}`; format/loại xe trả `400`, lỗi luật biển số trả `422`, và trường lạ trong request bị từ chối. Không có đơn giá hoặc phí.

| Mã lỗi | HTTP | Ý nghĩa |
|---|---:|---|
| `INVALID_FORMAT` | 400 | JSON sai định dạng, thiếu trường hoặc trường không hợp lệ |
| `INVALID_TYPE` | 400 | Loại xe không nằm trong `car`, `motorbike`, `bicycle` |
| `INVALID_CREDENTIALS` | 401 | Sai tên đăng nhập hoặc mật khẩu |
| `UNAUTHORIZED` | 401 | Thiếu hoặc sai Bearer token |
| `VEHICLE_NOT_FOUND` | 404 | Không tìm thấy xe hoặc bộ ba thông tin không khớp |
| `NOT_FOUND` | 404 | Đường dẫn API không tồn tại |
| `TICKET_IN_USE` | 409 | Mã vé đang gắn với xe trong bãi |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method không được hỗ trợ cho đường dẫn |
| `PLATE_REQUIRED` | 422 | Ô tô hoặc xe máy thiếu biển số |
| `PLATE_NOT_ALLOWED` | 422 | Xe đạp có trường biển số |

## Kiểm thử

Chạy toàn bộ suite từ thư mục gốc:

```powershell
python -m pytest -q
```

Test API dùng SQLite tạm và bao phủ đăng nhập, xác thực, gửi xe/tra cứu/lấy xe, danh sách phân trang, lỗi validation, OpenAPI và hai request POST đồng thời cùng ticket. Unit test kiểm tra riêng JWT, nghiệp vụ và repository.

Để nghiệm thu từ một clone mới, thực hiện lần lượt: cài Python dependencies, tạo `.env` từ `.env.example`, chạy `python -m pytest -q`, chạy ứng dụng local hoặc Docker Compose, kiểm tra `/health` và `/docs`. Muốn chạy benchmark, cài `requirements-loadtest.txt`, khởi động API và chạy lệnh Kaggle trong phần trên. Bảng mapping yêu cầu T01–T14 được duy trì trong tài liệu đặc tả của nhóm; không dùng số hiệu này làm kết luận nếu chưa đối chiếu bản yêu cầu tương ứng.
