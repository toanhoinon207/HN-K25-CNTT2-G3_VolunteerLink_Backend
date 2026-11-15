USE volunteerlink_db;
SET NAMES utf8mb4;

-- Chạy trên database TEST mới/trống; IDs cố định để giữ khóa ngoại.
START TRANSACTION;
INSERT INTO attendances (id, registration_id, check_in_at, check_out_at, total_minutes, status, recorded_by, updated_by, updated_at, edit_reason) VALUES
('1', '10', '2026-11-08 08:00:00', '2026-11-08 12:00:00', '240', 'PRESENT', '9', NULL, NULL, NULL),
('2', '11', '2026-11-08 08:20:00', '2026-11-08 11:50:00', '210', 'PRESENT', '10', NULL, NULL, NULL),
('3', '12', '2026-11-08 08:10:00', NULL, '0', 'PRESENT', '13', NULL, NULL, NULL),
('4', '13', NULL, NULL, '0', 'ABSENT', NULL, '4', '2026-11-10 13:00:00', 'Vắng mặt theo xác nhận của tổ chức'),
('5', '14', '2026-11-10 08:00:00', '2026-11-10 11:00:00', '180', 'PRESENT', '15', '4', '2026-11-10 13:00:00', 'Điều chỉnh theo biên bản điểm danh');
COMMIT;
