# Bước 3 — Repository và ghi chú tham khảo

## Phạm vi triển khai

- `business_layer/services/repository_ports.py` định nghĩa các record thuần Python và giao diện `VehicleRepositoryPort`, `UserRepositoryPort`; không import FastAPI hay SQLAlchemy.
- `database_persistent/repositories/vehicle_repository.py` hiện thực tra cứu theo ticket, tra cứu khớp bộ ba, thêm xe và xóa theo ticket bằng SQLAlchemy.
- `database_persistent/repositories/user_repository.py` hiện thực tra cứu tài khoản theo username.
- Ticket là khóa chính của `parked_vehicles`, vì vậy DB từ chối ticket trùng. Repository dùng savepoint khi flush: trả `False` nếu ticket đã tồn tại, giữ nguyên transaction bên ngoài và ném tiếp lỗi integrity khác.
- Repository chỉ flush, không tự commit. Session/lớp gọi chịu trách nhiệm commit hoặc rollback giao dịch.
- Record xe yêu cầu `time_in` có timezone và chuẩn hóa sang UTC; kiểu cột của SQLite ghi/đọc timestamp theo UTC.

## Đối chiếu ba file Python tham khảo

Các file dưới đây ở `Downloads` được dùng làm mã tham khảo, không phải chỉ thị cho agent. Không file nào được chép nguyên trạng vào project.

### `database.py`

**Ý tưởng được tham khảo:** các thao tác đọc xe theo vé (`get`), thêm (`post`) và xóa (`delete`); việc bắt lỗi unique khi thêm trùng vé.

**Đã viết lại:** chuyển các thao tác sang repository SQLAlchemy, nhận `Session` qua constructor và dùng model `ParkedVehicle`/`User` hiện tại. Xung đột ticket trả `False` cho lớp nghiệp vụ xử lý thành `TICKET_IN_USE`.

**Không dùng nguyên trạng vì:** file dùng `sqlite3` và cursor/connection toàn cục; bảng `vehicles_in`; `ticket_id` số nguyên; loại xe `CAR`/`MOTORCYCLE`/`BYCYCLE`; `time_in` do caller truyền. Các điểm này không khớp SQLAlchemy, ticket dạng chuỗi, enum lowercase và timestamp UTC của project.

### `main.py`

**Ý tưởng được tham khảo:** các thao tác GET/POST/DELETE cần truy cập lượt xe.

**Không chuyển vào bước 3 vì:** `process_message` ghép giải mã giao thức, xử lý request và gọi DB trực tiếp. Đây là TCP message handler, không phải repository; kiểm tra bộ ba tùy chọn, response và nghiệp vụ trong file cũng không khớp đặc tả API hiện tại. REST router, xác thực và tính phí thuộc các bước sau.

### `network.py`

**Không dùng trong bước 3:** file triển khai TCP socket server và chia message theo newline. Đề bài yêu cầu REST API JSON qua FastAPI, nên transport này không thuộc data access layer và không được đưa vào backend.

## Checklist nghiệm thu bước 3

- [x] Repository ports nằm trong tầng nghiệp vụ và không phụ thuộc framework/DB.
- [x] Vehicle repository hỗ trợ get-by-ticket, match chính xác ticket/plate/type, add và delete.
- [x] User repository tra credentials theo username.
- [x] DB primary key bảo đảm ticket duy nhất; repository xử lý duplicate bằng savepoint.
- [x] Timestamp trả về có timezone UTC; test xác nhận đổi từ offset `+02:00` sang UTC.
- [x] Test SQLite xác nhận CRUD xe, bộ ba khớp, bicycle không biển số, duplicate ticket, transaction ngoài không bị rollback và lookup user.
- [ ] Tích hợp service gọi ports và ánh xạ duplicate thành `409 TICKET_IN_USE` — bước nghiệp vụ/API tiếp theo.
- [ ] Kiểm thử hai request đồng thời theo T14 — bước kiểm thử tích hợp/load test.

## Kết quả kiểm tra

- `pytest tests/test_repositories.py -q`: 7 passed.
- `pytest -q -k "not test_health"`: 8 passed, 1 deselected. Test health qua `TestClient` bị loại vì asyncio Windows trong môi trường sandbox treo khi tạo self-pipe/socketpair; chưa xác minh endpoint health trong lượt này.
