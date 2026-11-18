USE volunteerlink_db;
SET NAMES utf8mb4;

-- Chạy trên database TEST mới/trống; IDs cố định để giữ khóa ngoại.
START TRANSACTION;
INSERT INTO users (id, email, password_hash, full_name, phone, role, status, created_at, updated_at) VALUES
('1', 'user@gmail.com', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Nguyễn Minh Anh', '0901000001', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('2', 'admin@gmail.com', '$2b$12$EH8d7a.ZSxNA3c8oNMUrNeU0zbIkANJCPMq6MsAJ3wJ8rt.3JV4Zq', 'Quản trị viên', '0901000002', 'ADMIN', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('3', 'organizer@gmail.com', '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry', 'Chủ tổ chức 1', '0901000003', 'ORGANIZER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('4', 'organizer2@gmail.com', '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry', 'Chủ tổ chức 2', '0901000004', 'ORGANIZER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('5', 'organizer3@gmail.com', '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry', 'Chủ tổ chức 3', '0901000005', 'ORGANIZER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('6', 'pending.org@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Người gửi hồ sơ chờ duyệt', '0901000006', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('7', 'rejected.org@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Người có hồ sơ bị từ chối', '0901000007', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('8', 'locked@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tài khoản bị khóa', '0901000008', 'USER', 'LOCKED', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('9', 'volunteer09@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 09', '0912000009', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('10', 'volunteer10@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 10', '0912000010', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('11', 'volunteer11@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 11', '0912000011', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('12', 'volunteer12@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 12', '0912000012', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('13', 'volunteer13@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 13', '0912000013', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('14', 'volunteer14@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 14', '0912000014', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('15', 'volunteer15@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 15', '0912000015', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('16', 'volunteer16@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 16', '0912000016', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('17', 'volunteer17@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 17', '0912000017', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('18', 'volunteer18@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 18', '0912000018', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('19', 'volunteer19@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 19', '0912000019', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('20', 'volunteer20@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 20', '0912000020', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('21', 'volunteer21@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 21', '0912000021', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('22', 'volunteer22@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 22', '0912000022', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('23', 'volunteer23@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 23', '0912000023', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('24', 'volunteer24@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 24', '0912000024', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('25', 'volunteer25@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 25', '0912000025', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('26', 'volunteer26@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 26', '0912000026', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('27', 'volunteer27@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 27', '0912000027', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('28', 'volunteer28@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 28', '0912000028', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('29', 'volunteer29@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 29', '0912000029', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00'),
('30', 'volunteer30@test.local', '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm', 'Tình nguyện viên 30', '0912000030', 'USER', 'ACTIVE', '2026-11-01 08:00:00', '2026-11-01 08:00:00');
COMMIT;
