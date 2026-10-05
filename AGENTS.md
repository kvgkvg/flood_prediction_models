# Quy tắc cho Codex (executor)
- Bạn được Claude (orchestrator) giao task. Chỉ làm đúng phạm vi task.
- Làm trên branch hiện tại, không đổi branch, không push.
- Cuối cùng in: danh sách file đã sửa, lệnh test đã chạy và kết quả, vấn đề còn tồn đọng.
- Không refactor ngoài yêu cầu.

# Quy ước dự án (lớp nguy cơ ngập đường)
- Bản thiết kế: `2026-10-04-du-bao-nguy-co-ngap-duong-design.md`. Mục tiêu cuối: xác suất ngập theo tuyến theo giờ phục vụ tìm đường tránh ngập, cảnh báo sớm 1–2 giờ, bản đồ ngập hiện tại.
- Máy: 14 GB RAM, GPU RTX 4050 6 GB VRAM, 12 luồng. KHÔNG được OOM: đọc raster theo cửa sổ/bbox, không nạp cả file PBF Việt Nam vào RAM, `n_jobs`/luồng ≤ 6, giải phóng bộ nhớ giữa các bước, mỗi tiến trình giữ dưới ~8 GB RAM.
- Python: dùng venv `.venv/` ở gốc repo (`.venv/bin/python`). Ghi phụ thuộc vào `requirements.txt`.
- Bố cục: `src/floodrisk/` (thư viện), `scripts/` (lệnh chạy), `tests/` (pytest), `data/raw|interim|processed/` (không commit), `reports/` (số liệu, hình nhỏ, có commit), `models/` (artifact nhỏ, có commit nếu < 5 MB).
- Bộ kiểm tra cuối (ngày ngập 2025–2026) bị KHÓA: không dùng để chọn mô hình, chọn đặc trưng, chỉnh ngưỡng hay xem số liệu, trừ khi task ghi rõ "mở khóa".
- Đầu vào Mô hình 1 không được chứa tọa độ, tên đường/phường/quận, hay việc tuyến từng ngập.
- Không vượt rào chặn truy cập (captcha, chặn bot); lấy dữ liệu tần suất thấp, có cache trên đĩa, chạy lại không tải lại.
- Mọi con số báo cáo phải kèm khoảng dao động (bootstrap) và lệnh tái lập.
