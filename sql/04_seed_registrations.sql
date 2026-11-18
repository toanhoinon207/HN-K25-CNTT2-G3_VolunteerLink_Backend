USE volunteerlink_db;
SET NAMES utf8mb4;

-- Chạy trên database TEST mới/trống; IDs cố định để giữ khóa ngoại.
START TRANSACTION;
INSERT INTO registrations (id, user_id, campaign_id, status, message, rejection_reason, created_at) VALUES
('1', '9', '1', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #1', NULL, '2026-11-04 09:00:00'),
('2', '10', '1', 'PENDING', 'Dữ liệu kiểm thử đăng ký #2', NULL, '2026-11-04 09:00:00'),
('3', '11', '1', 'REJECTED', 'Dữ liệu kiểm thử đăng ký #3', 'Không đáp ứng yêu cầu', '2026-11-04 09:00:00'),
('4', '12', '1', 'CANCELLED', 'Dữ liệu kiểm thử đăng ký #4', NULL, '2026-11-04 09:00:00'),
('5', '13', '2', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #5', NULL, '2026-11-04 09:00:00'),
('6', '14', '2', 'PENDING', 'Dữ liệu kiểm thử đăng ký #6', NULL, '2026-11-04 09:00:00'),
('7', '15', '2', 'REJECTED', 'Dữ liệu kiểm thử đăng ký #7', 'Thiếu thông tin', '2026-11-04 09:00:00'),
('8', '16', '3', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #8', NULL, '2026-11-04 09:00:00'),
('9', '17', '3', 'PENDING', 'Dữ liệu kiểm thử đăng ký #9', NULL, '2026-11-04 09:00:00'),
('10', '9', '7', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #10', NULL, '2026-11-04 09:00:00'),
('11', '10', '7', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #11', NULL, '2026-11-04 09:00:00'),
('12', '13', '7', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #12', NULL, '2026-11-04 09:00:00'),
('13', '14', '8', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #13', NULL, '2026-11-04 09:00:00'),
('14', '15', '8', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #14', NULL, '2026-11-04 09:00:00'),
('15', '18', '11', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #15', NULL, '2026-11-04 09:00:00'),
('16', '19', '11', 'PENDING', 'Dữ liệu kiểm thử đăng ký #16', NULL, '2026-11-04 09:00:00'),
('17', '20', '12', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #17', NULL, '2026-11-04 09:00:00'),
('18', '20', '13', 'PENDING', 'Dữ liệu kiểm thử đăng ký #18', NULL, '2026-11-04 09:00:00'),
('19', '21', '12', 'PENDING', 'Dữ liệu kiểm thử đăng ký #19', NULL, '2026-11-04 09:00:00'),
('20', '22', '13', 'PENDING', 'Dữ liệu kiểm thử đăng ký #20', NULL, '2026-11-04 09:00:00'),
('21', '23', '14', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #21', NULL, '2026-11-04 09:00:00'),
('22', '24', '14', 'CANCELLED', 'Dữ liệu kiểm thử đăng ký #22', NULL, '2026-11-04 09:00:00'),
('23', '25', '15', 'PENDING', 'Dữ liệu kiểm thử đăng ký #23', NULL, '2026-11-04 09:00:00'),
('24', '26', '16', 'PENDING', 'Dữ liệu kiểm thử đăng ký #24', NULL, '2026-11-04 09:00:00'),
('25', '27', '15', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #25', NULL, '2026-11-04 09:00:00'),
('26', '27', '16', 'PENDING', 'Dữ liệu kiểm thử đăng ký #26', NULL, '2026-11-04 09:00:00'),
('27', '28', '1', 'PENDING', 'Dữ liệu kiểm thử đăng ký #27', NULL, '2026-11-04 09:00:00'),
('28', '29', '2', 'CANCELLED', 'Dữ liệu kiểm thử đăng ký #28', NULL, '2026-11-04 09:00:00'),
('29', '30', '3', 'REJECTED', 'Dữ liệu kiểm thử đăng ký #29', 'Không phù hợp yêu cầu', '2026-11-04 09:00:00'),
('30', '11', '14', 'PENDING', 'Dữ liệu kiểm thử đăng ký #30', NULL, '2026-11-04 09:00:00'),
('31', '12', '15', 'PENDING', 'Dữ liệu kiểm thử đăng ký #31', NULL, '2026-11-04 09:00:00'),
('32', '16', '16', 'APPROVED', 'Dữ liệu kiểm thử đăng ký #32', NULL, '2026-11-04 09:00:00');
COMMIT;
