# Kế hoạch hoàn thiện hệ thống — Pha 1

Tài liệu này chuyển yêu cầu trong mô tả bài toán, đặc tả API và đề bài Pha 1 thành các bước triển khai và tiêu chí nghiệm thu. Nội dung tài liệu đính kèm được xem là yêu cầu của dự án; chỉ thị triển khai trong phiên này đến từ người dùng.

**Ghi chú phạm vi:** tài liệu mô tả bài toán nêu các thao tác POST/GET theo vé/DELETE, còn đặc tả API bổ sung `GET /api/v1/parking/entries` để liệt kê phân trang. Project hiện thực endpoint liệt kê theo đặc tả API; tham số là `limit`/`offset`, mặc định `50`/`0`, giới hạn `limit` 1–100 và sắp xếp theo ticket tăng dần.

## Trạng thái xuất phát

- Cấu trúc đã được chuẩn hóa thành package `business_layer/` và `database_persistent/`, cùng `gate_client/`, `loadtest/`, `tests/` và `docs/`.
- Backend đã có repository, parking/auth service, dependency injection và REST API.
- `docker-compose.yml`, Dockerfile, Gate client và script load test vẫn rỗng.
- README đã được đồng bộ với khả năng hiện có; tài liệu đặc tả gốc chưa được lưu trong repo.

## Các bước thực hiện

### 1. Chốt cấu trúc module và quy tắc phụ thuộc — Hoàn tất phần package; chờ xác minh phụ thuộc

- [x] Giữ API, security dependency, schemas và điểm khởi động trong package `business_layer/`.
- [x] Giữ business services và domain exceptions trong `business_layer/services/`.
- [x] Giữ cấu hình DB, ORM models, repositories và seed tài khoản trong package `database_persistent/`.
- [x] Dùng tên package Python hợp lệ, chữ thường và dấu gạch dưới; không import từ tên thư mục cũ chứa dấu `+` hoặc dấu cách. Package backend được đặt `business_layer/` để tránh xung đột hoa/thường với đường dẫn Git cũ `Business/` trên Windows.
- [x]Đã thêm `__init__.py` để khai báo các package `business_layer`, các subpackage API/schemas/services và `database_persistent` cùng models/repositories.
- [x]Đã cập nhật test khói sang `business_layer.main` và đường dẫn kiểm tra tầng service sang `business_layer/services`.
- [x]Quy tắc đã chốt: service chỉ phụ thuộc interface/port của repository; test kiến trúc kiểm tra service không import FastAPI, SQLAlchemy hoặc driver DB.
- [x]README và kế hoạch này đã được cập nhật theo module path mới.

**Nghiệm thu:** tên package và module path đã chốt; `business_layer.main:app` nối API với service và repository qua dependency injection. Test kiến trúc kiểm tra ranh giới tầng.

### 2. Xác định cấu hình và dữ liệu — Hoàn tất triển khai; chờ nghiệm thu runtime

- Khai báo cấu hình qua `.env.example`: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_SECONDS` và thông tin admin; không có cấu hình giá.
- [x] Đã thêm `business_layer/config.py` dùng Pydantic Settings; tải `.env` theo đường dẫn cố định từ thư mục dự án, hỗ trợ biến môi trường và giữ JWT key dạng `SecretStr`.
- [x] Đã thêm `python-dotenv` vào requirements để hỗ trợ đọc `.env`.
- Không dùng `.env` trong Git; thay secret mặc định trước khi triển khai.
- [x] Tạo model `parked_vehicles` với `ticket` tối đa 64 ký tự, `plate` tối đa 15 ký tự nullable, `type`, `time_in` UTC.
- [x] Tạo model tài khoản với username duy nhất và password hash bcrypt.
- [x] Đã tạo SQLAlchemy base/engine/session, UTC-aware timestamp type, hai model và hàm `initialize_database()` tạo schema/seed admin idempotent; mật khẩu được băm bcrypt.
- [x] Đã gọi `initialize_database()` từ lifespan của `business_layer.main:app`; endpoint `/health` tối thiểu cũng đã được thêm để app có thể khởi động và kiểm tra.
- [x] Dùng SQLite làm hệ quản trị duy nhất của project Pha 1; `DATABASE_URL` cấu hình vị trí file local.

**Nghiệm thu:** cấu hình/model/seed/startup hook đã có; repository chạy test với SQLite tạm. Việc chạy ứng dụng bằng Uvicorn và kiểm tra dữ liệu tồn tại sau restart vẫn cần nghiệm thu thủ công.

### 3. Hoàn thiện Repository/Data Access — Hoàn tất triển khai và nghiệm thu concurrency

- [x] Định nghĩa interface repository thuần Python ở tầng nghiệp vụ.
- [x] Cài đặt repository cho xe: tìm theo ticket, tìm khớp bộ ba, thêm và xóa.
- [x] Cài đặt repository người dùng để lấy password hash theo username.
- [x] Dùng khóa chính ticket để DB từ chối duplicate; repository trả kết quả conflict mà không rollback transaction ngoài.
- [x] Lưu `time_in` có timezone và chuẩn hóa sang UTC.
- [x] Tích hợp vehicle/user ports với parking/auth service; duplicate ticket thành `TICKET_IN_USE`.
- [x] Test hai insert song song cùng ticket: đúng một thành công và một conflict.
- [x] Test tích hợp API cho hai POST song song cùng ticket: một request thành công, request còn lại trả conflict.

**Nghiệm thu:** repository và API concurrency tests chạy qua với SQLite. Ghi chú phần tham khảo ba file ngoài repo nằm trong `docs/step-3-repository-notes.md`.

### 4. Hoàn thiện nghiệp vụ thuần Python

- [x] Validate dữ liệu bắt buộc, định dạng ticket/biển số và từ chối trường lạ bằng lỗi miền.
- [x] Chỉ chấp nhận `car`, `motorbike`, `bicycle`.
- [x] Bicycle không được có trường `plate`; car/motorbike bắt buộc có `plate`.
- [x] Chuẩn hóa biển số bằng trim khoảng trắng và uppercase trước khi lưu/so khớp.
- [x] Trùng ticket đang gửi xe trả `TICKET_IN_USE`; tra cứu không khớp bộ ba trả `VEHICLE_NOT_FOUND`.
- [x] Gửi xe lưu ticket, loại xe, biển số hợp lệ và `time_in` UTC.
- [x] Lấy xe xác nhận ticket/plate/type khớp, xóa lượt gửi và trả record đã lấy ra.
- [x] GET là thao tác tra cứu chỉ đọc, trả dữ liệu lượt gửi và không làm thay đổi trạng thái.
- [x] Không triển khai bảng giá, đơn giá, tính phí hoặc dữ liệu `charge` trong phạm vi hiện tại.

Service thuần Python nằm tại `business_layer/services/parking_service.py`, nhận `VehicleRepositoryPort` qua constructor và không phụ thuộc FastAPI/SQLAlchemy. `BusinessError.code` cung cấp mã lỗi miền để API ánh xạ ở bước 6.

**Nghiệm thu bước 4 lúc hoàn tất:** `pytest tests/test_business_rules.py -q`: 18 passed; suite lúc đó: 28 passed, 1 deselected vì test health bị treo trong asyncio sandbox Windows. Test tổng hợp mới nhất được ghi tại bước 7.

### 5. Đăng nhập và dependency xác thực JWT

- [x] Login kiểm tra username/password bcrypt và trả JWT HS256 gồm `sub`, `iat`, `exp`.
- [x] Verify token offline bằng secret cấu hình; không phụ thuộc dịch vụ Internet/OAuth.
- [x] Response login dùng `token_type: "Bearer"` và `expires_in` theo `JWT_EXPIRE_SECONDS`; service login vẫn chỉ trả JWT string.
- [x] Bảo vệ các endpoint parking bằng dependency Bearer dùng chung.
- [x] Ánh xạ token thiếu/sai/hết hạn thành lỗi miền `UNAUTHORIZED`, status 401 và JSON phẳng; response có `WWW-Authenticate: Bearer`.
- [x] Login sai trả `INVALID_CREDENTIALS`, status 401 và JSON phẳng.
- [x] HTTP exception cho route không tồn tại và method không hỗ trợ trả `NOT_FOUND` (404) / `METHOD_NOT_ALLOWED` (405).
- [x] Thêm unit test login/JWT và test API cho thứ tự auth trước validation.

**Nghiệm thu:** suite đầy đủ mới nhất đạt 69 passed, 1 cảnh báo deprecation từ Starlette/httpx.

### 6. Xây dựng REST API và tài liệu OpenAPI

- [x] `POST /api/v1/auth/login` cấp access token.
- [x] `POST /api/v1/parking/entries` ghi nhận xe và trả 204 rỗng.
- [x] GET tra cứu ticket/type/plate, trả `ticket`, `plate`, `type`, `time_in` và giữ nguyên record.
- [x] GET `/api/v1/parking/entries` trả danh sách xe phân trang qua `limit`/`offset`, kèm `items`, `total`, `limit`, `offset`; sắp xếp ổn định theo ticket tăng dần.
- [x] DELETE xác nhận bộ ba, xóa record và trả 200 cùng `{"ticket":"..."}`.
- [x] `GET /health` và OpenAPI/Swagger được nối vào app.
- [x] Xác thực được khai báo ở cấp parking router; response lỗi chung và lỗi riêng được mô tả trong OpenAPI bằng `ErrorResponse`.
- [x] Chuẩn hóa JSON phẳng cho business errors và validation; lỗi format/field lạ/type trả 400, lỗi luật biển số trả 422.
- [x] Xe đạp có `plate` (kể cả `null`) bị từ chối; car/motorbike thiếu plate bị từ chối.
- [x] Cập nhật test hợp đồng API cho phản hồi DELETE và endpoint danh sách phân trang.
- [x] Chạy HTTP endpoint integration tests sau khi thêm endpoint danh sách và đổi phản hồi DELETE.

**Nghiệm thu:** route, schema, security, response lỗi và OpenAPI đã được kiểm tra bằng unit/schema và HTTP integration tests.

### 7. Đồng bộ kiểm thử chức năng và thứ tự lỗi

- [x] Giữ test khói và test kiến trúc; xác nhận service không import framework/DB.
- [x] Bổ sung unit test auth, business service và repository dùng SQLite; không kiểm thử phí.
- [x] Thêm API integration tests cho auth, request lạ, auth-order, gửi xe, GET chỉ đọc, GET sai bộ ba, DELETE trả mã vé, danh sách phân trang, duplicate ticket, OpenAPI và response không có `charge`.
- [x] Test repository race và API hai POST đồng thời cùng ticket đều cho một request thành công, một request conflict.
- [x] Lệnh suite chuẩn được ghi trong README: `python -m pytest -q`.
- [x] Bổ sung kiểm thử repository cho phân trang và cập nhật kiểm thử mã lỗi format/type thành HTTP 400.
- [x] Chạy lại toàn bộ HTTP integration tests, test health và API-level duplicate-ticket concurrency test sau các cập nhật login/404/405.

**Nghiệm thu:** `python -m pytest -q`: 69 passed, 1 cảnh báo deprecation từ Starlette/httpx. Bước 7 đã hoàn tất; project sẵn sàng bắt đầu bước 8.

### 8. Đóng gói Docker và chạy offline

- [x] Viết `business_layer/Dockerfile` cho ứng dụng backend Python 3.12; chạy Uvicorn bằng user không phải root.
- [x] Hoàn thiện `docker-compose.yml` với một service API, mount named volume `parking_data` tại `/data` cho SQLite; không có service database riêng.
- [x] Truyền cấu hình từ `.env`; `.dockerignore` loại `.env`, database local, môi trường ảo và artifacts khỏi build context/image.
- [x] Khai báo health check qua `/health`, port mapping `8000:8000`, restart policy và SQLite URL `sqlite:////data/parking.db`.
- [x] Build và khởi chạy bằng Docker Engine; xác nhận container Healthy, đăng nhập/gửi/tra cứu/xóa API, `/docs` trả 200 và dữ liệu SQLite còn sau khi recreate container.
- [x] Xác minh khởi động lại sau lần build với `--pull never`; container Healthy, `/health` trả `ok` và `/docs` trả 200.
- Chỉ container hóa `gate_client/` nếu thực sự cần; tài liệu thiết kế ghi container này là tùy chọn.

**Nghiệm thu:** `docker compose config -q` hợp lệ; build và runtime hoạt động, vé SQLite còn sau khi recreate container, service Healthy, `/health` trả `ok`, `/docs` trả 200 và khởi động lại thành công với `--pull never`. Bước 8 hoàn tất; image nền và dependencies cần được tải trước để chạy khi offline.

### 9. Hoàn thiện Gate client và load test Kaggle

- [x] Gate client tương tác mô phỏng login, gửi xe, tra cứu và lấy xe; không hiển thị bảng giá/phí.
- [x] Thêm test unit cho HTTP client: Bearer auth, payload xe đạp không có plate, query tra cứu/lấy xe và mã lỗi API.
- [x] Thêm `requirements-loadtest.txt` tách Locust khỏi image runtime; `locustfile.py` chạy POST → GET → DELETE bằng ticket UUID riêng, xóa record cuối mỗi vòng và làm mới JWT trước khi hết hạn.
- [x] Hoàn thiện `kaggle_runner.sh` để kiểm tra `/health`, ghi phần cứng/phần mềm/config, throughput, latency, failures, CSV và HTML vào `docs/benchmarks/<run-id>/`.
- [x] Ghi hướng dẫn cài dependency, chạy Gate client, chuẩn bị Backend/Kaggle secrets và lưu artifact tại README cùng `docs/benchmarks/README.md`.
- [x] Cài dependencies và chạy baseline trên Kaggle CPU thật; lưu toàn bộ artifact vào `docs/benchmarks/20261028T182659Z-m8jDvhHE/`.

**Nghiệm thu:** Gate client unit tests đạt; Kaggle CPU baseline chạy 10 users, spawn rate 2 users/giây trong 60 giây, Locust exit code 0 và 0 failures. Final console ghi 4.918 requests; CSV snapshot và summary ghi 4.868 do Locust cập nhật CSV theo chu kỳ. Cả log cuối và CSV snapshot được giữ để đối chiếu; artifact được lưu cùng repo.

### 10. Đồng bộ tài liệu và chuẩn bị bàn giao

- [x] Cập nhật README với đúng module path, setup, cấu hình, lệnh chạy local/Docker, API, benchmark và lệnh kiểm thử.
- [x] README mô tả lỗi `NOT_FOUND`/`METHOD_NOT_ALLOWED`, response login `token_type`/`expires_in`; thống nhất tên thư mục `gate_client/`.
- [x] Đưa nguyên bản mô tả bài toán và đặc tả API vào `docs/specifications/`, kèm README mô tả vai trò mỗi tài liệu.
- [x] Ghi kiến trúc ba tầng, cách chạy offline, ERD/schema và quyết định thiết kế trong `docs/architecture.md` và `docs/decisions.md`.
- [x] Cập nhật `.gitignore` cho `.venv/`, `venv/`, `.env`, DB local, cache, coverage và benchmark run sinh ra; baseline đã nghiệm thu vẫn được giữ trong Git.
- [x] Kiểm tra danh sách file theo dõi: không có `.env`, DB local, môi trường ảo hoặc cache; có cấu hình mẫu và benchmark baseline được chọn.
- [x] Clone commit bàn giao `700f114`, tạo `.env` từ mẫu, chạy API; `/health` trả `ok`, `/docs` trả HTTP 200.
- [x] Chạy nhóm test độc lập trên clone: 41 passed; baseline Kaggle đã nghiệm thu ở bước 9 và được giữ làm artifact repo.
- [x] Trên máy dev Windows với Python 3.12.7, tạo virtualenv mới, cài toàn bộ `requirements.txt`, chạy `pip check` và `python -m pytest -q`: 75 passed, 1 cảnh báo deprecation trong 12 giây.

**Nghiệm thu bước 10:** tài liệu bàn giao, repo hygiene, clone khởi động local, health/Swagger, cài dependencies sạch và full test suite đều đã được xác minh. Codex sandbox vẫn có giới hạn với một số test HTTP `TestClient`, nhưng máy dev đã chạy trọn bộ thành công; baseline Kaggle đã có sẵn từ bước 9.

## Thứ tự ưu tiên đề xuất

Hoàn thành theo thứ tự 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Không bắt đầu benchmark hoặc bàn giao cài đặt trước khi API, DB, auth, Docker và kiểm thử chức năng đã chạy ổn định.
