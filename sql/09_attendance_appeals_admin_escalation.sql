-- Bổ sung cột khiếu nại lên Admin cho bảng attendance_appeals.
-- Chạy trên MySQL hiện có. Sao lưu trước khi migration.
ALTER TABLE attendance_appeals
    ADD COLUMN escalation_reason TEXT NULL AFTER reviewed_at,
    ADD COLUMN escalated_at DATETIME NULL AFTER escalation_reason,
    ADD COLUMN admin_id INT NULL AFTER escalated_at,
    ADD COLUMN admin_note TEXT NULL AFTER admin_id,
    ADD COLUMN admin_resolved_at DATETIME NULL AFTER admin_note,
    ADD CONSTRAINT fk_attendance_appeals_admin FOREIGN KEY (admin_id) REFERENCES users(id);
