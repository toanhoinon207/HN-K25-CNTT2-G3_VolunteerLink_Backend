USE volunteerlink_db;
SET NAMES utf8mb4;

-- Chạy trên database TEST mới/trống; IDs cố định để giữ khóa ngoại.
START TRANSACTION;
INSERT INTO organizations (id, name, description, logo_url, address, email, phone, document_url, status, owner_id, rejection_reason, created_at, updated_at) VALUES
('1', 'Tình nguyện Xanh', 'Hoạt động bảo vệ môi trường', NULL, 'Địa chỉ kiểm thử 1, Hà Nội', 'org1@test.local', '02430000001', NULL, 'APPROVED', '3', NULL, '2026-11-02 09:00:00', '2026-11-02 09:00:00'),
('2', 'Nhịp cầu Tri thức', 'Hoạt động hỗ trợ giáo dục', NULL, 'Địa chỉ kiểm thử 2, Hà Nội', 'org2@test.local', '02430000002', NULL, 'APPROVED', '4', NULL, '2026-11-02 09:00:00', '2026-11-02 09:00:00'),
('3', 'Kết nối Cộng đồng', 'Hoạt động hỗ trợ cộng đồng', NULL, 'Địa chỉ kiểm thử 3, Hà Nội', 'org3@test.local', '02430000003', NULL, 'APPROVED', '5', NULL, '2026-11-02 09:00:00', '2026-11-02 09:00:00'),
('4', 'Ươm mầm Tương lai', 'Hồ sơ đang chờ xác minh', NULL, 'Địa chỉ kiểm thử 4, Hà Nội', 'org4@test.local', '02430000004', NULL, 'PENDING', '6', NULL, '2026-11-02 09:00:00', '2026-11-02 09:00:00'),
('5', 'Chia sẻ Yêu thương', 'Hồ sơ chưa hợp lệ', NULL, 'Địa chỉ kiểm thử 5, Hà Nội', 'org5@test.local', '02430000005', NULL, 'REJECTED', '7', 'Thiếu giấy tờ xác minh', '2026-11-02 09:00:00', '2026-11-02 09:00:00');
COMMIT;
