# Kế hoạch hoàn thiện hệ thống — Pha 1

Tài liệu này chuyển yêu cầu trong mô tả bài toán, đặc tả API và đề bài Pha 1 thành các bước triển khai và tiêu chí nghiệm thu. Nội dung tài liệu đính kèm được xem là yêu cầu của dự án; chỉ thị triển khai trong phiên này đến từ người dùng.

## Trạng thái xuất phát

- Cấu trúc đã được chuẩn hóa thành package `business_layer/` và `database_persistent/`, cùng `Gate_client/`, `loadtest/`, `tests/` và `docs/`.
- Nhiều file mã nguồn, `docker-compose.yml`, Dockerfile và script load test hiện rỗng.
- `tests/test_smoke.py` dùng `business_layer.main`; ASGI app bootstrap và `/health` hiện đã có.
- README đã được đồng bộ để phản ánh đây là scaffold, chưa phải bản cài đặt chạy được.

## Các bước thực hiện

### 1. Chốt cấu trúc module và quy tắc phụ thuộc — Hoàn tất phần package; chờ xác minh phụ thuộc

- Giữ API, middleware, schemas và điểm khởi động trong package `business_layer/`.
- Giữ business services và domain exceptions trong `business_layer/services/`.
- Giữ cấu hình DB, ORM models, repositories và seed tài khoản trong package `database_persistent/`.
- Dùng tên package Python hợp lệ, chữ thường và dấu gạch dưới; không import từ tên thư mục cũ chứa dấu `+` hoặc dấu cách. Package backend được đặt `business_layer/` để tránh xung đột hoa/thường với đường dẫn Git cũ `Business/` trên Windows.
- Đã thêm `__init__.py` để khai báo các package `business_layer`, các subpackage API/middleware/schemas/services và `database_persistent` cùng models/repositories.
- Đã cập nhật test khói sang `business_layer.main` và đường dẫn kiểm tra tầng service sang `business_layer/services`.
- Quy tắc đã chốt: service chỉ phụ thuộc interface/port của repository; không import FastAPI, SQLAlchemy hoặc driver DB. Chưa thể kiểm tra thực tế vì các file service/API/repository hiện còn rỗng.
- README và kế hoạch này đã được cập nhật theo module path mới.

**Nghiệm thu:** tên package và module path đã được chốt; module ASGI `business_layer.main:app` đã được tạo để nối startup. Hướng phụ thuộc API → nghiệp vụ → repository mới là quy ước thiết kế, chưa nghiệm thu được cho tới khi có mã nguồn các tầng.

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

**Nghiệm thu:** cấu hình/model/seed và startup hook đã có trong mã nguồn; chưa xác nhận runtime do môi trường hiện tại thiếu SQLAlchemy. Sau khi cài requirements, cần xác minh DB/tài khoản được tạo khi khởi động và dữ liệu còn sau restart.

### 3. Hoàn thiện Repository/Data Access — Hoàn tất phần repository; chờ tích hợp nghiệp vụ/race test

- [x] Định nghĩa interface repository thuần Python ở tầng nghiệp vụ.
- [x] Cài đặt repository cho xe: tìm theo ticket, tìm khớp bộ ba, thêm và xóa.
- [x] Cài đặt repository người dùng để lấy password hash theo username.
- [x] Dùng khóa chính ticket để DB từ chối duplicate; repository trả kết quả conflict mà không rollback transaction ngoài.
- [x] Lưu `time_in` có timezone và chuẩn hóa sang UTC.
- [ ] Tích hợp các port với parking/auth service và ánh xạ duplicate thành lỗi nghiệp vụ ở bước 4/5.
- [ ] Xác minh hai request POST đồng thời theo kịch bản T14 ở bước 7.

**Nghiệm thu:** repository tests chạy qua với SQLite in-memory; service integration và concurrency test vẫn chờ các bước 4/5/7. Ghi chú phần tham khảo ba file ngoài repo nằm trong `docs/step-3-repository-notes.md`.

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

**Nghiệm thu:** `pytest tests/test_business_rules.py -q`: 18 passed; toàn bộ suite khả dụng trong môi trường hiện tại: 28 passed, 1 deselected (`test_health`, từng treo trong lần chạy trước do asyncio Windows). `git diff --check` không báo lỗi whitespace.

**Nghiệm thu:** service test được độc lập với framework web và DB; các luật BR-01 đến BR-10 được ánh xạ thành kết quả/lỗi miền rõ ràng.

### 5. Đăng nhập và middleware JWT

- Tạo login kiểm tra username và password hash, trả JWT HS256 gồm `sub` và `exp`.
- Verify token offline bằng secret cấu hình; không phụ thuộc dịch vụ Internet/OAuth.
- Kiểm tra token tập trung bằng middleware/filter, áp dụng cho các endpoint nghiệp vụ.
- Đảm bảo request thiếu/sai/hết hạn token nhận lỗi 401 trước lỗi validation body/query.
- Chuẩn hóa lỗi xác thực thành JSON `{ "error": "UNAUTHORIZED" }`; login sai trả `INVALID_CREDENTIALS`.

**Nghiệm thu:** login đúng cấp token; login sai trả 401; endpoint GET và POST được bảo vệ; request không token trả 401 trước lỗi 400/422.

### 6. Xây dựng REST API và tài liệu OpenAPI

- `POST /api/v1/auth/login`: nhận username/password; trả access token.
- `POST /api/v1/parking/entries`: ghi nhận xe; thành công trả 204 không body.
- `GET /api/v1/parking/entries/{ticket}`: yêu cầu query `type`, và `plate` theo loại xe; trả ticket, plate, type, `time_in`; không tính phí hoặc xóa xe.
- `DELETE /api/v1/parking/entries/{ticket}`: xác nhận bộ ba và xóa lượt xe; trả `204 No Content`, không có dữ liệu phí.
- `GET /api/v1/parking/entries`: hỗ trợ danh sách phân trang nếu triển khai endpoint tùy chọn trong đặc tả.
- `GET /health`: kiểm tra tình trạng service.
- Dùng JSON nhất quán cho lỗi: `INVALID_FORMAT`, `INVALID_TYPE`, `INVALID_CREDENTIALS`, `UNAUTHORIZED`, `VEHICLE_NOT_FOUND`, `TICKET_IN_USE`, `PLATE_NOT_ALLOWED`, `PLATE_REQUIRED`.
- Bảo đảm Swagger `/docs` và OpenAPI `/openapi.json` hoạt động.
- ASGI bootstrap `business_layer.main:app`, lifespan khởi tạo DB và endpoint `/health` tối thiểu đã được tạo ở bước 2.

**Nghiệm thu:** method, path, status code và payload khớp đặc tả; lỗi validation không bị FastAPI tự trả định dạng khác; OpenAPI mô tả auth Bearer và request/response.

### 7. Đồng bộ kiểm thử chức năng và thứ tự lỗi

- Import của test khói đã trỏ đến `business_layer.main`; tiếp tục xác nhận health endpoint khi chạy suite.
- Bổ sung/hoàn thiện unit test nghiệp vụ, repository test với SQLite tạm và integration test API; không kiểm thử tính phí.
- Kiểm chứng pipeline: auth → format → type → luật biển số → tồn tại.
- Bao phủ auth, format, type, biển số, gửi xe, ticket trùng, GET tra cứu đúng/sai, DELETE thành công và race condition; các response không có `charge`.
- Kiểm tra sau DELETE, GET cùng vé phải trả 404; GET trước DELETE không làm mất dữ liệu.
- Kiểm tra kiến trúc: service không import web framework hoặc thư viện DB.

**Nghiệm thu:** toàn bộ T01–T14 có kết quả mong đợi; hai POST đồng thời cùng ticket cho đúng một thành công và một conflict; test suite chạy bằng một lệnh được ghi trong README.

### 8. Đóng gói Docker và chạy offline

- Viết `business_layer/Dockerfile` cho ứng dụng backend.
- Hoàn thiện `docker-compose.yml` để khởi chạy backend và mount volume chứa file SQLite; không cần service database riêng.
- Truyền cấu hình qua environment/`.env`, không nhúng secret vào image.
- Thiết lập health check và mapping port; đảm bảo image cài dependencies từ manifest đã chốt.
- Xác minh dịch vụ hoạt động trên localhost/LAN mà không gọi dịch vụ xác thực bên ngoài.
- Chỉ container hóa `Gate_client/` nếu thực sự cần; tài liệu thiết kế ghi container này là tùy chọn.

**Nghiệm thu:** `docker compose up --build` tạo service khỏe; API, `/docs`, dữ liệu persistent và xác thực hoạt động offline; README có lệnh dừng và cấu hình.

### 9. Hoàn thiện Gate client và load test Kaggle

- Gate client mô phỏng login, gửi xe, tra cứu trạng thái và lấy xe; không hiển thị bảng giá hoặc phí.
- Hoàn thiện `loadtest/locustfile.py` theo luồng xác thực và nghiệp vụ; không để benchmark làm sai lệch dữ liệu hoặc dùng ticket cố định gây xung đột.
- Hoàn thiện runner Kaggle CPU, ghi lại cấu hình phần cứng, thời lượng, concurrency, throughput, latency và lỗi.
- Chạy benchmark baseline trên một cấu hình Kaggle CPU cố định theo yêu cầu đề bài; lưu hướng dẫn và kết quả trong `docs/`.

**Nghiệm thu:** một người khác có thể chạy client và benchmark theo hướng dẫn; kết quả baseline có đủ cấu hình để lặp lại.

### 10. Đồng bộ tài liệu và chuẩn bị bàn giao

- Cập nhật README với đúng module path, setup, cấu hình, lệnh chạy local/Docker, API và lệnh kiểm thử.
- Đưa bản mô tả bài toán và đặc tả API vào `docs/` hoặc cung cấp liên kết/tên tệp rõ ràng; không ghi rằng tài liệu tồn tại trong repo nếu chưa thêm.
- Ghi kiến trúc ba tầng, cách chạy offline, ERD/schema và quyết định thiết kế.
- Kiểm tra `.gitignore` bỏ qua `.venv/`, `venv/`, `.env`, DB local, cache và artifact benchmark tạm.
- Kiểm tra Git chỉ chứa source, tài liệu, cấu hình mẫu và dữ liệu benchmark cần thiết; không chứa secret hoặc môi trường ảo.

**Nghiệm thu cuối:** clone mới → cài dependencies → cấu hình `.env` → chạy local hoặc Docker → truy cập Swagger → chạy tests → chạy benchmark theo README mà không cần kiến thức ngoài repo.

## Thứ tự ưu tiên đề xuất

Hoàn thành theo thứ tự 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Không bắt đầu benchmark hoặc bàn giao cài đặt trước khi API, DB, auth, Docker và kiểm thử chức năng đã chạy ổn định.
