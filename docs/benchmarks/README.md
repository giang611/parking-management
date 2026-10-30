# Kết quả benchmark CPU trên Kaggle

Sau khi cài `requirements-loadtest.txt` và khởi động API, chạy `bash loadtest/kaggle_runner.sh` từ thư mục gốc của dự án. Script sẽ tạo một thư mục có tên theo thời gian chạy, bao gồm:

- `environment.txt`: thông tin phần cứng Kaggle, phiên bản phần mềm, địa chỉ API và cấu hình tải.
- `locust_stats.csv`, `locust_stats_history.csv` và `locust_failures.csv`: số lượng request, số lỗi, thông lượng và các phân vị thời gian phản hồi.
- `report.html`: báo cáo tổng hợp của Locust.
- `summary.md`: các chỉ số tóm tắt của dòng tổng hợp.

Cấu hình mặc định chạy trong 60 giây với 10 người dùng đồng thời và tốc độ khởi tạo 2 người dùng mỗi giây. Để chạy với cấu hình khác, đặt các biến `USERS`, `SPAWN_RATE`, `RUN_TIME` và `BASE_URL`; hãy giữ lại các giá trị này khi so sánh những lần chạy. Nếu API và Locust cùng chạy trên một notebook, cả hai sẽ dùng chung CPU Kaggle; cần ghi rõ cách chạy này trong kết quả.

## Kết quả cơ sở đã ghi nhận

Kết quả benchmark CPU Kaggle đầu tiên được lưu trong [`20261028T182659Z-m8jDvhHE/`](20261028T182659Z-m8jDvhHE/). Lần chạy này dùng 10 người dùng, tốc độ khởi tạo 2 người dùng mỗi giây và kéo dài 60 giây trên môi trường Kaggle có 4 CPU Intel Xeon. Locust kết thúc với mã 0 và không ghi nhận request lỗi. Bảng cuối trong console ghi nhận 4.918 request; ảnh chụp CSV định kỳ cuối cùng và `summary.md` ghi nhận 4.868. Locust cập nhật thống kê CSV theo chu kỳ, vì vậy tổng cuối trong console có thể mới hơn số liệu trong ảnh chụp đó. Log gốc và các tệp CSV đều được giữ lại trong thư mục của lần chạy.
