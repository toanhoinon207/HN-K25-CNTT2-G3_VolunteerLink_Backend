-- Chạy một lần trên database hiện tại sau khi sao lưu.
-- MySQL 8.0: kiểm tra cột trước nếu đã từng chạy migration này.
ALTER TABLE campaigns
  ADD COLUMN attendance_code_type VARCHAR(10) NULL;
-- Mã cũ không xác định loại: giữ NULL và không tự động hoàn thành.
-- Không cập nhật tất cả mã cũ thành CHECK_OUT.
