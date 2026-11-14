INSERT INTO registrations
(id, user_id, campaign_id, status, message, rejection_reason, created_at)
VALUES
(1, 1, 1, 'APPROVED',
 'Tôi muốn tham gia hỗ trợ chiến dịch.',
 NULL, '2026-11-01 08:30:00'),

(2, 2, 1, 'APPROVED',
 'Tôi có kinh nghiệm tham gia tình nguyện.',
 NULL, '2026-11-01 09:15:00'),

(3, 3, 1, 'PENDING',
 'Mong được tham gia cùng mọi người.',
 NULL, '2026-11-02 10:00:00'),

(4, 4, 2, 'APPROVED',
 'Tôi có thể tham gia đầy đủ thời gian.',
 NULL, '2026-11-02 11:20:00'),

(5, 5, 2, 'REJECTED',
 'Tôi muốn hỗ trợ công tác tổ chức.',
 'Không đáp ứng yêu cầu của chiến dịch.',
 '2026-11-03 08:45:00'),

(6, 6, 3, 'APPROVED',
 'Tôi muốn đóng góp cho cộng đồng.',
 NULL, '2026-11-03 09:30:00'),

(7, 7, 3, 'PENDING',
 'Tôi có thể hỗ trợ vào cuối tuần.',
 NULL, '2026-11-03 14:00:00'),

(8, 8, 4, 'APPROVED',
 'Tôi từng tham gia hoạt động tương tự.',
 NULL, '2026-11-04 08:00:00'),

(9, 9, 4, 'CANCELLED',
 'Tôi muốn tham gia hoạt động này.',
 NULL, '2026-11-04 10:15:00'),

(10, 10, 5, 'APPROVED',
 'Tôi sẵn sàng hỗ trợ mọi công việc.',
 NULL, '2026-11-05 09:00:00'),

(11, 1, 6, 'PENDING',
 'Tôi muốn tham gia chiến dịch môi trường.',
 NULL, '2026-11-05 11:30:00'),

(12, 2, 7, 'APPROVED',
 'Tôi có thể hỗ trợ truyền thông.',
 NULL, '2026-11-06 08:20:00'),

(13, 3, 8, 'REJECTED',
 'Tôi mong muốn tham gia chiến dịch.',
 'Không đáp ứng điều kiện tham gia.',
 '2026-11-06 09:45:00'),

(14, 4, 9, 'APPROVED',
 'Tôi có kinh nghiệm làm việc nhóm.',
 NULL, '2026-11-07 10:00:00'),

(15, 5, 10, 'PENDING',
 'Tôi muốn hỗ trợ các hoạt động cộng đồng.',
 NULL, '2026-11-07 13:15:00'),

(16, 6, 11, 'APPROVED',
 'Tôi có thể tham gia toàn bộ chương trình.',
 NULL, '2026-11-08 08:30:00'),

(17, 7, 12, 'CANCELLED',
 'Tôi đăng ký tham gia chiến dịch.',
 NULL, '2026-11-08 09:20:00'),

(18, 8, 13, 'PENDING',
 'Tôi muốn tích lũy kinh nghiệm tình nguyện.',
 NULL, '2026-11-09 10:40:00'),

(19, 9, 14, 'APPROVED',
 'Tôi sẵn sàng hỗ trợ chiến dịch.',
 NULL, '2026-11-09 14:00:00'),

(20, 10, 15, 'PENDING',
 'Hy vọng được tham gia cùng tổ chức.',
 NULL, '2026-11-10 08:15:00');