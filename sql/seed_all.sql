-- ============================================================================
-- VolunteerLink - Bộ dữ liệu seed tổng hợp đầy đủ (13 bảng nghiệp vụ)
-- Mật khẩu mặc định cho tất cả tài khoản: 12345678
-- Chạy trên database trống bằng MySQL Workbench / MySQL CLI hoặc qua app/db/seed.py
-- ============================================================================

SET NAMES utf8mb4;
USE volunteerlink_db;

START TRANSACTION;

-- ----------------------------------------------------------------------------
-- 1. USERS (ADMIN, ORGANIZER, USER ACTIVE, USER LOCKED)
-- ----------------------------------------------------------------------------
INSERT INTO users (id, email, password_hash, full_name, phone, avatar_url, role, status, created_at, updated_at) VALUES
(1,  'admin@gmail.com',       '$2b$12$bb1Cdn/7DH7jrJ2Z0nPRDOw5Rnp8yzJWxMBzUjYynV2w4SEGbC3tu', 'Nguyễn Văn Admin',       '0901000001', NULL, 'ADMIN',     'ACTIVE', DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 30 DAY)),
(2,  'organizer@gmail.com',   '$2b$12$40NolNrh2hRQ6iXC0OJHX.pNSqL/zz.WmcXi9xAiRTe8FkVLOS5ae', 'Nguyễn Văn Organizer',   '0902000001', NULL, 'ORGANIZER', 'ACTIVE', DATE_SUB(NOW(), INTERVAL 29 DAY), DATE_SUB(NOW(), INTERVAL 29 DAY)),
(3,  'organizer2@gmail.com',  '$2b$12$l6jwMi79L4P7gLaIbecUd.tlKtBsOXrk5RNAWNGpTmiHNaCCbN4cC', 'Trần Thị Organizer 2',   '0902000002', NULL, 'ORGANIZER', 'ACTIVE', DATE_SUB(NOW(), INTERVAL 28 DAY), DATE_SUB(NOW(), INTERVAL 28 DAY)),
(4,  'organizer3@gmail.com',  '$2b$12$80DqvTB74.BcLrC6GaZyfOXrplt9MNspuqkZpTyKJe7xU8cmx5nkK', 'Lê Minh Organizer 3',    '0902000003', NULL, 'ORGANIZER', 'ACTIVE', DATE_SUB(NOW(), INTERVAL 27 DAY), DATE_SUB(NOW(), INTERVAL 27 DAY)),
(5,  'organizer4@gmail.com',  '$2b$12$ogQozfAS38lwLniL2zLYKeZoM7EhNuEIvd1BOLOs1cQHXmb8HPPwK', 'Phạm Thu Organizer 4',   '0902000004', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 26 DAY), DATE_SUB(NOW(), INTERVAL 26 DAY)),
(6,  'organizer5@gmail.com',  '$2b$12$GpXaePKgHtLsAmT3B7RbgO7Ouwtev67JyOrKjC0TCjLSM9XoDzKyq', 'Hoàng Đức Organizer 5',  '0902000005', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 25 DAY)),
(7,  'user@gmail.com',        '$2b$12$WBIgZyfGS.ypY3/6./FF1eNlyxqnIWh2K9UFKJbe5FIkKoDo/GKlu', 'Nguyễn Minh Anh',        '0903000001', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 24 DAY), DATE_SUB(NOW(), INTERVAL 24 DAY)),
(8,  'user2@gmail.com',       '$2b$12$Irtny8PYTww2SQmy2d457.a12UWA2RwxmxNuQlEM1vGchsQg991la', 'Trần Lan Anh',           '0903000002', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 23 DAY), DATE_SUB(NOW(), INTERVAL 23 DAY)),
(9,  'user3@gmail.com',       '$2b$12$WR.xnY60SwgqIVlo6sXPW.LU3NR8v9A2SjeFonl7vH3XL6lcZa7v6', 'Lê Quốc Bảo',            '0903000003', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 22 DAY), DATE_SUB(NOW(), INTERVAL 22 DAY)),
(10, 'user4@gmail.com',       '$2b$12$uuuV6DlE4MySrEvbaV86z.Z.inZH3bMa8OZ3g5jBnE33jgWaZIE2W', 'Phạm Minh Châu',         '0903000004', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 21 DAY), DATE_SUB(NOW(), INTERVAL 21 DAY)),
(11, 'user5@gmail.com',       '$2b$12$dqmYZY5.z/rTYlLT3q/zJOO9Ws5ecQNe8KW47wnZNQffwcC/bLgDy', 'Đỗ Hải Đăng',            '0903000005', NULL, 'USER',      'ACTIVE', DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 20 DAY)),
(12, 'locked_user@gmail.com', '$2b$12$NVBKj2QP3JE3KhpYy5cyieIji9cMtNxt1RoiystB/EtGBfktHkVDi', 'Tài Khoản Bị Khóa',      '0903000099', NULL, 'USER',      'LOCKED', DATE_SUB(NOW(), INTERVAL 19 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY));

-- ----------------------------------------------------------------------------
-- 2. USER MODERATION LOGS (LOCK / UNLOCK)
-- ----------------------------------------------------------------------------
INSERT INTO user_moderation_logs (id, user_id, admin_id, action, reason, created_at) VALUES
(1, 11, 1, 'LOCK',   'Tạm khóa để xác minh thông tin đăng ký trùng lặp.', DATE_SUB(NOW(), INTERVAL 12 DAY)),
(2, 11, 1, 'UNLOCK', 'Đã xác minh thông tin hợp lệ, mở khóa tài khoản.', DATE_SUB(NOW(), INTERVAL 11 DAY)),
(3, 12, 1, 'LOCK',   'Vi phạm quy định cộng đồng nhiều lần khi tham gia chiến dịch.', DATE_SUB(NOW(), INTERVAL 5 DAY));

-- ----------------------------------------------------------------------------
-- 3. VOLUNTEER PROFILES
-- ----------------------------------------------------------------------------
INSERT INTO volunteer_profiles (id, user_id, date_of_birth, skills, area) VALUES
(1, 7,  '2002-05-15', 'Giao tiếp, Tổ chức sự kiện, Sơ cứu cơ bản', 'Hoàn Kiếm, Hà Nội'),
(2, 8,  '2003-08-22', 'Dạy học, Thiết kế đồ họa, Chụp ảnh',       'Cầu Giấy, Hà Nội'),
(3, 9,  '2001-11-03', 'Nấu ăn, Hậu cần, Điều phối nhóm',           'Đống Đa, Hà Nội'),
(4, 10, '2004-02-19', 'Tiếng Anh, Truyền thông, Viết nội dung',    'Thanh Xuân, Hà Nội'),
(5, 11, '2000-09-10', 'Y tế cộng đồng, Vận động thể chất',         'Hai Bà Trưng, Hà Nội'),
(6, 12, '2002-01-01', 'Hậu cần',                                   'Long Biên, Hà Nội');

-- ----------------------------------------------------------------------------
-- 4. ORGANIZATIONS (APPROVED, PENDING, REJECTED)
-- ----------------------------------------------------------------------------
INSERT INTO organizations (id, name, description, logo_url, address, email, phone, document_url, status, owner_id, rejection_reason, created_at, updated_at) VALUES
(1, 'VolunteerLink Hà Nội',     'Tổ chức hoạt động tình nguyện vì cộng đồng tại Hà Nội.',       NULL, 'Hoàn Kiếm, Hà Nội',  'contact@volunteerlink.vn',   '0241234567', NULL, 'APPROVED', 2, NULL,                                      DATE_SUB(NOW(), INTERVAL 28 DAY), DATE_SUB(NOW(), INTERVAL 27 DAY)),
(2, 'Cộng đồng Xanh Việt Nam',  'Tổ chức các hoạt động bảo vệ môi trường và trồng cây.',       NULL, 'Cầu Giấy, Hà Nội',   'contact@congdongxanh.vn',    '0242345678', NULL, 'APPROVED', 3, NULL,                                      DATE_SUB(NOW(), INTERVAL 27 DAY), DATE_SUB(NOW(), INTERVAL 26 DAY)),
(3, 'Kết Nối Yêu Thương',       'Hỗ trợ trẻ em và người có hoàn cảnh khó khăn.',               NULL, 'Đống Đa, Hà Nội',    'contact@ketnoiyeuthuong.vn', '0243456789', NULL, 'APPROVED', 4, NULL,                                      DATE_SUB(NOW(), INTERVAL 26 DAY), DATE_SUB(NOW(), INTERVAL 25 DAY)),
(4, 'Ánh Sáng Tri Thức',        'Tổ chức các chương trình giáo dục cộng đồng.',                NULL, 'Thanh Xuân, Hà Nội', 'contact@anhsangtrithuc.vn',  '0244567890', NULL, 'PENDING',  5, NULL,                                      DATE_SUB(NOW(), INTERVAL 4 DAY),  DATE_SUB(NOW(), INTERVAL 4 DAY)),
(5, 'Nhịp Cầu Nhân Ái',         'Tổ chức các chương trình thiện nguyện và hỗ trợ cộng đồng.',  NULL, 'Long Biên, Hà Nội',  'contact@nhipcaunhanai.vn',   '0245678901', NULL, 'REJECTED', 6, 'Hồ sơ chưa đáp ứng yêu cầu xác minh.',    DATE_SUB(NOW(), INTERVAL 8 DAY),  DATE_SUB(NOW(), INTERVAL 6 DAY));

-- ----------------------------------------------------------------------------
-- 5. CAMPAIGNS (DRAFT, PENDING, OPEN, CLOSED, COMPLETED, CANCELLED)
-- ----------------------------------------------------------------------------
-- ----------------------------------------------------------------------------
-- 5. CAMPAIGNS (DRAFT, PENDING, OPEN, CLOSED, COMPLETED, CANCELLED)
-- ----------------------------------------------------------------------------
INSERT INTO campaigns (
    id, organization_id, title, description, image_url, category, location,
    start_time, end_time, registration_deadline, max_participants,
    requirements, estimated_hours, status, reason,
    created_at, updated_at, attendance_code, attendance_code_expires_at, attendance_code_type
) VALUES
-- #1: OPEN hôm nay (để test điểm danh check-in / check-out trực tiếp với mã LIVE26)
(1, 1, 'Dọn vệ sinh Hồ Gươm',
 'Chiến dịch Dọn vệ sinh Hồ Gươm nhằm bảo vệ cảnh quan đô thị và lan tỏa ý thức giữ gìn môi trường.',
 'https://images.unsplash.com/photo-1758599668547-2b1192c10abb', 'ENVIRONMENT', 'Hoàn Kiếm, Hà Nội',
 TIMESTAMP(CURDATE(), '00:00:00'),
 TIMESTAMP(CURDATE(), '23:59:59'),
 DATE_SUB(NOW(), INTERVAL 2 HOUR),
 20, 'Có tinh thần trách nhiệm, tham gia đúng giờ và tuân thủ hướng dẫn của ban tổ chức.', 4.0,
 'OPEN', NULL, DATE_SUB(NOW(), INTERVAL 15 DAY), NOW(),
 'LIVE26', DATE_ADD(NOW(), INTERVAL 1 DAY), 'CHECK_IN'),

-- #2: OPEN sắp diễn ra (để test đăng ký & waitlist: max_participants=1 đã đủ chỗ)
(2, 2, 'Trồng cây xanh tại Ba Vì',
 'Chiến dịch Trồng cây xanh tại Ba Vì góp phần phủ xanh đồi trọc và nâng cao nhận thức sinh thái.',
 'https://images.unsplash.com/photo-1779049624287-90ff257b2fc7', 'ENVIRONMENT', 'Ba Vì, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 10 DAY), '08:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 10 DAY), '12:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 8 DAY),  '23:59:00'),
 1, 'Sức khỏe tốt, mang giày thể thao và tuân thủ hướng dẫn an toàn.', 4.0,
 'OPEN', NULL, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY),
 NULL, NULL, NULL),

-- #3: OPEN sắp diễn ra (còn nhiều chỗ)
(3, 3, 'Dạy học cho trẻ em khó khăn',
 'Chiến dịch hỗ trợ ôn tập kiến thức cơ bản cho các em nhỏ có hoàn cảnh khó khăn.',
 'https://images.unsplash.com/photo-1499808009608-201e28a68a5a', 'EDUCATION', 'Long Biên, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 14 DAY), '08:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 14 DAY), '12:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 12 DAY), '23:59:00'),
 25, 'Kiên nhẫn, yêu trẻ và chuẩn bị giáo án ngắn gọn theo phân công.', 4.0,
 'OPEN', NULL, DATE_SUB(NOW(), INTERVAL 9 DAY), DATE_SUB(NOW(), INTERVAL 9 DAY),
 NULL, NULL, NULL),

-- #4: OPEN sắp diễn ra (lĩnh vực HEALTH)
(4, 1, 'Ngày hội hiến máu nhân đạo',
 'Chiến dịch hỗ trợ điều phối, chăm sóc người hiến máu và truyền thông nâng cao nhận thức.',
 'https://images.unsplash.com/photo-1536856136534-bb679c52a9aa', 'HEALTH', 'Đống Đa, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 18 DAY), '08:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 18 DAY), '12:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 16 DAY), '23:59:00'),
 30, 'Nhiệt tình, giao tiếp tốt và tuân thủ quy trình y tế.', 4.0,
 'OPEN', NULL, DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY),
 NULL, NULL, NULL),

-- #5: OPEN sắp diễn ra (lĩnh vực COMMUNITY)
(5, 3, 'Bữa cơm yêu thương',
 'Chuẩn bị và trao tặng suất ăn miễn phí cho bệnh nhân và người lao động khó khăn.',
 'https://images.unsplash.com/photo-1517486808906-6ca8b3f04846', 'COMMUNITY', 'Hai Bà Trưng, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 7 DAY), '09:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 7 DAY), '13:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 5 DAY), '23:59:00'),
 15, 'Đảm bảo vệ sinh an toàn thực phẩm và đúng giờ tập trung.', 4.0,
 'OPEN', NULL, DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY),
 NULL, NULL, NULL),

-- #6: PENDING (chờ Admin duyệt)
(6, 2, 'Tiếp sức mùa thi',
 'Hỗ trợ thí sinh và phụ huynh tại các điểm thi trên địa bàn quận Cầu Giấy.',
 'https://images.unsplash.com/photo-1488161628813-04466f872be2', 'EDUCATION', 'Cầu Giấy, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 22 DAY), '07:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 22 DAY), '11:30:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 20 DAY), '23:59:00'),
 40, 'Năng động, đúng giờ và có mặt đầy đủ trong buổi tập huấn.', 4.5,
 'PENDING', NULL, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY),
 NULL, NULL, NULL),

-- #7: DRAFT (bản nháp của Organizer)
(7, 1, 'Tặng sách cho trẻ em vùng cao',
 'Quyên góp, phân loại và đóng gói sách giáo khoa gửi tới học sinh vùng cao.',
 'https://images.unsplash.com/photo-1559305289-4c31700ba9cb', 'EDUCATION', 'Sa Pa, Lào Cai',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 30 DAY), '08:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 30 DAY), '16:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 25 DAY), '23:59:00'),
 20, 'Cẩn thận, có kinh nghiệm phân loại sách và đóng gói vận chuyển.', 8.0,
 'DRAFT', NULL, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY),
 NULL, NULL, NULL),

-- #8: CLOSED (đã đóng đăng ký, sắp/đã qua hạn đăng ký)
(8, 2, 'Chạy bộ gây quỹ từ thiện',
 'Điều phối cung đường chạy bộ gây quỹ ủng hộ trẻ em khuyết tật.',
 'https://images.unsplash.com/photo-1613936360976-8f35cf0e5461', 'HEALTH', 'Tây Hồ, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '06:30:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '10:30:00'),
 DATE_SUB(NOW(), INTERVAL 1 DAY),
 25, 'Có mặt trước giờ xuất phát 30 phút để nhận áo và phân khu.', 4.0,
 'CLOSED', NULL, DATE_SUB(NOW(), INTERVAL 14 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY),
 NULL, NULL, NULL),

-- #9: COMPLETED (đã hoàn thành - dùng cho Attendance, Appeals, HourClaims, Certificates)
(9, 1, 'Ngày hội tái chế rác thải',
 'Thu gom, phân loại rác thải nhựa và hướng dẫn người dân tái chế tại khu dân cư.',
 'https://images.unsplash.com/photo-1611284446314-60a58ac0deb9', 'ENVIRONMENT', 'Nam Từ Liêm, Hà Nội',
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '08:00:00'),
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '12:00:00'),
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 12 DAY), '23:59:00'),
 20, 'Tuân thủ phân loại rác đúng hướng dẫn.', 4.0,
 'COMPLETED', NULL, DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY),
 NULL, NULL, NULL),

-- #10: COMPLETED (đã hoàn thành)
(10, 3, 'Trung thu cho em',
 'Tổ chức đêm hội trăng rằm, rước đèn và trao quà cho trẻ em tại nhà văn hóa.',
 'https://images.unsplash.com/photo-1681034494427-35b291a34385', 'COMMUNITY', 'Hà Đông, Hà Nội',
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '17:00:00'),
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '21:00:00'),
 TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 22 DAY), '23:59:00'),
 20, 'Hòa đồng, yêu trẻ em và hỗ trợ dọn dẹp sau chương trình.', 4.0,
 'COMPLETED', NULL, DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 20 DAY),
 NULL, NULL, NULL),

-- #11: CANCELLED (đã hủy có lý do)
(11, 1, 'Chiến dịch xanh cuối tuần',
 'Dọn dẹp khu vực ven sông Hồng và trồng hoa ven đường.',
 'https://images.unsplash.com/photo-1580600301354-0ce8faef576c', 'ENVIRONMENT', 'Gia Lâm, Hà Nội',
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 28 DAY), '08:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 28 DAY), '12:00:00'),
 TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 26 DAY), '23:59:00'),
 20, 'Trang phục gọn gàng, mang găng tay bảo hộ.', 4.0,
 'CANCELLED', 'Chiến dịch tạm hủy do điều chỉnh kế hoạch phối hợp địa phương.', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY),
 NULL, NULL, NULL);
-- ----------------------------------------------------------------------------
-- 6. ATTENDANCE CODE ISSUES (Lịch sử cấp mã điểm danh)
-- ----------------------------------------------------------------------------
INSERT INTO attendance_code_issues (id, campaign_id, issued_by, code, code_type, issued_at, expires_at, revoked_at) VALUES
(1, 1, 2, 'LIVE26', 'CHECK_IN',  DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_ADD(NOW(), INTERVAL 1 DAY), NULL),
(2, 9, 2, 'RC1001', 'CHECK_IN',  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '07:45:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '09:30:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '09:30:00')),
(3, 9, 2, 'RC1002', 'CHECK_OUT', TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '11:45:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '13:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '13:00:00'));

-- ----------------------------------------------------------------------------
-- 7. REGISTRATIONS (PENDING, APPROVED, REJECTED, CANCELLED, WAITLISTED)
-- ----------------------------------------------------------------------------
INSERT INTO registrations (id, user_id, campaign_id, status, message, rejection_reason, created_at) VALUES
-- Campaign #1 (OPEN hôm nay - LIVE26): user 7 & 8 APPROVED (chưa điểm danh để test trên web), user 9 PENDING
(1,  7,  1,  'APPROVED',   'Đăng ký tham gia chiến dịch hôm nay',                NULL, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(2,  8,  1,  'APPROVED',   'Sẵn sàng tham gia đúng giờ',                          NULL, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(3,  9,  1,  'PENDING',    'Mong ban tổ chức duyệt đơn giúp em',                  NULL, DATE_SUB(NOW(), INTERVAL 3 DAY)),

-- Campaign #2 (OPEN max_participants=1 - đã đủ chỗ, có waitlist)
(4,  7,  2,  'APPROVED',   'Đăng ký tham gia trồng cây Ba Vì',                    NULL, DATE_SUB(NOW(), INTERVAL 6 DAY)),
(5,  9,  2,  'WAITLISTED', 'Xin vào danh sách chờ chiến dịch Ba Vì',              NULL, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(6,  10, 2,  'WAITLISTED', 'Đăng ký chờ slot nếu có người hủy',                  NULL, DATE_SUB(NOW(), INTERVAL 4 DAY)),

-- Campaign #3 (OPEN)
(7,  7,  3,  'PENDING',    'Em muốn tham gia dạy học cuối tuần',                  NULL, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(8,  8,  3,  'APPROVED',   'Có kinh nghiệm gia sư môn Toán',                      NULL, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(9,  11, 3,  'REJECTED',   'Đăng ký tham gia dạy học',                            'Chưa phù hợp yêu cầu chuyên môn đợt này.', DATE_SUB(NOW(), INTERVAL 4 DAY)),

-- Campaign #8 (CLOSED)
(10, 7,  8,  'APPROVED',   'Đăng ký điều phối giải chạy gây quỹ',                NULL, DATE_SUB(NOW(), INTERVAL 10 DAY)),
(11, 8,  8,  'APPROVED',   'Tham gia hỗ trợ tiếp nước đường chạy',                NULL, DATE_SUB(NOW(), INTERVAL 10 DAY)),
(12, 11, 8,  'CANCELLED',  'Bận lịch thi đột xuất nên xin hủy đăng ký',          NULL, DATE_SUB(NOW(), INTERVAL 9 DAY)),

-- Campaign #9 (COMPLETED - Ngày hội tái chế rác thải)
(13, 7,  9,  'APPROVED',   'Tham gia phân loại rác thải nhựa',                    NULL, DATE_SUB(NOW(), INTERVAL 18 DAY)),
(14, 8,  9,  'APPROVED',   'Hỗ trợ truyền thông ngày hội tái chế',                NULL, DATE_SUB(NOW(), INTERVAL 18 DAY)),
(15, 9,  9,  'APPROVED',   'Hỗ trợ hậu cần và thu gom',                           NULL, DATE_SUB(NOW(), INTERVAL 18 DAY)),
(16, 10, 9,  'APPROVED',   'Tham gia hướng dẫn tái chế tại khu dân cư',           NULL, DATE_SUB(NOW(), INTERVAL 18 DAY)),
(17, 11, 9,  'REJECTED',   'Đăng ký muộn',                                        'Đã đủ số lượng tình nguyện viên cho đợt này.', DATE_SUB(NOW(), INTERVAL 17 DAY)),

-- Campaign #10 (COMPLETED - Trung thu cho em)
(18, 7,  10, 'APPROVED',   'Tham gia tổ chức đêm hội Trung thu',                  NULL, DATE_SUB(NOW(), INTERVAL 25 DAY)),
(19, 8,  10, 'APPROVED',   'Hỗ trợ trang trí sân khấu và phát quà',              NULL, DATE_SUB(NOW(), INTERVAL 25 DAY)),
(20, 9,  10, 'APPROVED',   'Hỗ trợ hậu cần đêm hội Trung thu',                    NULL, DATE_SUB(NOW(), INTERVAL 25 DAY)),
(21, 10, 10, 'APPROVED',   'Tham gia quản trò và đón các em nhỏ',                 NULL, DATE_SUB(NOW(), INTERVAL 25 DAY)),
(22, 11, 10, 'APPROVED',   'Hỗ trợ âm thanh ánh sáng chương trình',               NULL, DATE_SUB(NOW(), INTERVAL 25 DAY));

-- ----------------------------------------------------------------------------
-- 8. WAITLIST ENTRIES (INVITED, WAITING)
-- ----------------------------------------------------------------------------
INSERT INTO waitlist_entries (id, user_id, campaign_id, position, status, invited_at, response_deadline, responded_at, created_at, updated_at) VALUES
(1, 9,  2, 1, 'INVITED', DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_ADD(NOW(), INTERVAL 22 HOUR), NULL, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, 10, 2, 2, 'WAITING', NULL, NULL, NULL, DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY));

-- ----------------------------------------------------------------------------
-- 9. ATTENDANCES (PRESENT đầy đủ, PRESENT chỉnh sửa, PRESENT chưa check-out, ABSENT)
-- ----------------------------------------------------------------------------
INSERT INTO attendances (id, registration_id, check_in_at, check_out_at, total_minutes, recorded_by, updated_by, updated_at, edit_reason, status) VALUES
-- Campaign #9 (COMPLETED)
(1, 13, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '08:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '12:00:00'), 240, 2, NULL, NULL, NULL, 'PRESENT'),
(2, 14, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '08:15:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '11:45:00'), 210, 2, 2, DATE_SUB(NOW(), INTERVAL 9 DAY), 'Điều chỉnh theo biên bản điểm danh thực tế.', 'PRESENT'),
(3, 15, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '08:10:00'), NULL, 0, 2, NULL, NULL, NULL, 'PRESENT'),
(4, 16, NULL, NULL, 0, 2, 2, DATE_SUB(NOW(), INTERVAL 9 DAY), 'Vắng mặt không báo trước.', 'ABSENT'),

-- Campaign #10 (COMPLETED)
(5, 18, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '17:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '21:00:00'), 240, 4, NULL, NULL, NULL, 'PRESENT'),
(6, 19, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '17:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '20:30:00'), 210, 4, NULL, NULL, NULL, 'PRESENT'),
(7, 20, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '17:10:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '20:40:00'), 210, 4, NULL, NULL, NULL, 'PRESENT'),
(8, 21, NULL, NULL, 0, 4, NULL, NULL, 'Chưa ghi nhận check-in tại điểm tập kết.', 'ABSENT'),
(9, 22, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 20 DAY), '17:05:00'), NULL, 0, 4, NULL, NULL, NULL, 'PRESENT');

-- ----------------------------------------------------------------------------
-- 10. ATTENDANCE APPEALS (PENDING, ACCEPTED, REJECTED, ADMIN_PENDING, ADMIN_ACCEPTED, ADMIN_REJECTED)
-- ----------------------------------------------------------------------------
INSERT INTO attendance_appeals (
    id, registration_id, user_id, reason, evidence_url, status,
    organizer_id, review_note, reviewed_at,
    escalation_reason, escalated_at,
    admin_id, admin_note, admin_resolved_at, created_at
) VALUES
-- #1: PENDING (chờ Organizer duyệt - reg 15 chưa check-out)
(1, 15, 9,
 'Em có tham gia đến hết buổi nhưng điện thoại hết pin nên chưa quét mã check-out.',
 'https://volunteerlink.vn/evidences/att_appeal_1.jpg',
 'PENDING', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, DATE_SUB(NOW(), INTERVAL 2 DAY)),

-- #2: ADMIN_PENDING (Organizer từ chối reg 16 ABSENT -> user khiếu nại lên Admin)
(2, 16, 10,
 'Em có đến muộn 15 phút và đã báo với trưởng nhóm hậu cần, xin cập nhật lại điểm danh.',
 'https://volunteerlink.vn/evidences/att_appeal_2.jpg',
 'ADMIN_PENDING', 2, 'Không tìm thấy tên trong danh sách check-in tại bàn đón tiếp.', DATE_SUB(NOW(), INTERVAL 3 DAY),
 'Em có ảnh chụp có mặt tại khu vực phân loại rác cùng nhóm 2 lúc 08:30.', DATE_SUB(NOW(), INTERVAL 1 DAY),
 NULL, NULL, NULL, DATE_SUB(NOW(), INTERVAL 4 DAY)),

-- #3: ADMIN_ACCEPTED (reg 21 ở campaign 10 đã được Admin chấp nhận)
(3, 21, 10,
 'Em tham gia hỗ trợ từ 17:00 đến 20:30 nhưng bị đánh dấu vắng do lỗi nhập liệu.',
 'https://volunteerlink.vn/evidences/att_appeal_3.jpg',
 'ADMIN_ACCEPTED', 4, 'Không có xác nhận tại quầy check-in.', DATE_SUB(NOW(), INTERVAL 14 DAY),
 'Đính kèm ảnh chụp bàn giao quà Trung thu có xác nhận của trưởng ban.', DATE_SUB(NOW(), INTERVAL 13 DAY),
 1, 'Đã đối chiếu ảnh và xác nhận trưởng ban, chấp nhận khiếu nại.', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY)),

-- #4: ADMIN_REJECTED (reg 22 ở campaign 10 bị Admin từ chối)
(4, 22, 11,
 'Em quên check-out lúc 21:00, mong được bổ sung giờ ra.',
 'https://volunteerlink.vn/evidences/att_appeal_4.jpg',
 'ADMIN_REJECTED', 4, 'Không thấy tình nguyện viên ở lại sau 19:00.', DATE_SUB(NOW(), INTERVAL 14 DAY),
 'Xin Admin xem xét lại giúp em.', DATE_SUB(NOW(), INTERVAL 13 DAY),
 1, 'Minh chứng không thể hiện thời gian có mặt đến cuối chương trình.', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY));

-- ----------------------------------------------------------------------------
-- 11. HOUR CLAIMS (VERIFIED, PENDING, REJECTED, + appeal_status PENDING / ACCEPTED / REJECTED)
-- ----------------------------------------------------------------------------
INSERT INTO hour_claims (
    id, registration_id, claimed_hours, evidence_url, status, verified_by,
    user_id, actual_hours, approved_hours, note, verified_at, rejection_reason,
    appeal_reason, appeal_evidence_url, appeal_status, admin_id, admin_note, resolved_at,
    created_at, updated_at
) VALUES
-- #1: VERIFIED (reg 13 - Campaign #9)
(1, 13, 4.00, 'https://volunteerlink.vn/evidences/claim_13.jpg', 'VERIFIED', 2,
 7, 4.00, 4.00, 'Đề nghị xác nhận giờ tham gia Ngày hội tái chế rác thải.', DATE_SUB(NOW(), INTERVAL 8 DAY), NULL,
 NULL, NULL, NULL, NULL, NULL, NULL,
 DATE_SUB(NOW(), INTERVAL 9 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY)),

-- #2: PENDING (reg 14 - Campaign #9)
(2, 14, 4.50, 'https://volunteerlink.vn/evidences/claim_14.jpg', 'PENDING', NULL,
 8, 3.50, NULL, 'Xin cộng thêm 1 giờ hỗ trợ dọn dẹp thiết bị sau sự kiện.', NULL, NULL,
 NULL, NULL, NULL, NULL, NULL, NULL,
 DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),

-- #3: REJECTED (không khiếu nại - reg 19 - Campaign #10)
(3, 19, 5.50, 'https://volunteerlink.vn/evidences/claim_19.jpg', 'REJECTED', 4,
 8, 3.50, NULL, 'Đề nghị xác nhận 5.5 giờ cho đêm hội Trung thu.', DATE_SUB(NOW(), INTERVAL 15 DAY), 'Số giờ yêu cầu vượt quá thời gian điểm danh thực tế.',
 NULL, NULL, NULL, NULL, NULL, NULL,
 DATE_SUB(NOW(), INTERVAL 17 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY)),

-- #4: REJECTED + appeal_status PENDING (reg 20 - Campaign #10)
(4, 20, 5.00, 'https://volunteerlink.vn/evidences/claim_20.jpg', 'REJECTED', 4,
 9, 3.50, NULL, 'Xin xác nhận thêm giờ ở lại kiểm kê quà tặng.', DATE_SUB(NOW(), INTERVAL 12 DAY), 'Thiếu minh chứng làm thêm giờ.',
 'Em có ở lại hỗ trợ kiểm kê vật tư, đính kèm ảnh chụp biên bản.', 'https://volunteerlink.vn/evidences/appeal_20.jpg', 'PENDING', NULL, NULL, NULL,
 DATE_SUB(NOW(), INTERVAL 14 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY)),

-- #5: VERIFIED + appeal_status ACCEPTED (reg 18 - Campaign #10)
(5, 18, 4.00, 'https://volunteerlink.vn/evidences/claim_18.jpg', 'VERIFIED', 4,
 7, 4.00, 4.00, 'Đề nghị xác nhận đủ 4 giờ tham gia Trung thu cho em.', DATE_SUB(NOW(), INTERVAL 16 DAY), NULL,
 'Đính kèm xác nhận của trưởng nhóm hậu cần.', 'https://volunteerlink.vn/evidences/appeal_18.jpg', 'ACCEPTED', 1, 'Đã đối chiếu biên bản, chấp nhận đủ giờ điểm danh thực tế.', DATE_SUB(NOW(), INTERVAL 14 DAY),
 DATE_SUB(NOW(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 14 DAY));

-- ----------------------------------------------------------------------------
-- 12. CERTIFICATES (ACTIVE, REVOKED)
-- ----------------------------------------------------------------------------
INSERT INTO certificates (id, certificate_code, user_id, campaign_id, total_hours, issued_at, status, revoked_reason, revoked_at, revoked_by) VALUES
(1, 'VL-2026-009-0007', 7, 9,  4.00, DATE_SUB(NOW(), INTERVAL 8 DAY),  'ACTIVE',  NULL, NULL, NULL),
(2, 'VL-2026-010-0007', 7, 10, 4.00, DATE_SUB(NOW(), INTERVAL 14 DAY), 'REVOKED', 'Thu hồi mẫu để kiểm tra trạng thái chứng nhận bị thu hồi.', DATE_SUB(NOW(), INTERVAL 5 DAY), 1);

-- ----------------------------------------------------------------------------
-- 13. NOTIFICATIONS (Đã đọc & chưa đọc cho USER, ORGANIZER, ADMIN)
-- ----------------------------------------------------------------------------
INSERT INTO notifications (id, user_id, title, content, link, is_read, created_at) VALUES
(1, 7, 'Đơn đăng ký đã được duyệt',
 'Đơn đăng ký chiến dịch Dọn vệ sinh Hồ Gươm của bạn đã được ban tổ chức phê duyệt.',
 'user-dashboard.html?tab=overview', 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(2, 7, 'Chứng nhận tình nguyện mới',
 'Bạn đã nhận được chứng nhận hoàn thành chiến dịch Ngày hội tái chế rác thải.',
 'user-dashboard.html?tab=certificates', 1, DATE_SUB(NOW(), INTERVAL 48 HOUR)),
(3, 9, 'Lời mời từ danh sách chờ',
 'Chiến dịch "Trồng cây xanh tại Ba Vì" đã có chỗ. Vui lòng phản hồi lời mời trong vòng 24 giờ.',
 'campaign_detail.html?id=2', 0, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(4, 2, 'Có yêu cầu xác nhận giờ mới',
 'Tình nguyện viên vừa gửi yêu cầu xác nhận giờ cho chiến dịch Ngày hội tái chế rác thải.',
 'organizer-dashboard.html?tab=certificates', 0, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(5, 2, 'Chiến dịch mới đã được duyệt',
 'Chiến dịch Dọn vệ sinh Hồ Gươm đã được Admin phê duyệt và mở đăng ký.',
 'organizer-dashboard.html?tab=campaigns', 1, DATE_SUB(NOW(), INTERVAL 72 HOUR)),
(6, 1, 'Hồ sơ tổ chức chờ duyệt',
 'Tổ chức Ánh Sáng Tri Thức đang chờ Admin xem xét phê duyệt.',
 'admin-dashboard.html?tab=organizations', 0, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
(7, 1, 'Khiếu nại điểm danh chuyển lên Admin',
 'Có khiếu nại điểm danh đang chờ Quản trị viên phân xử trong 48 giờ.',
 'admin-dashboard.html?tab=appeals', 0, DATE_SUB(NOW(), INTERVAL 4 HOUR));

COMMIT;
