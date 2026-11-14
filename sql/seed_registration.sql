USE volunteerlink_db;

INSERT INTO registrations (
    user_id,
    campaign_id,
    status,
    message,
    rejection_reason,
    created_at
)
VALUES
-- Chiến dịch 1
(6, 1, 'APPROVED',
 'Tôi muốn tham gia hoạt động tình nguyện.',
 NULL, '2026-11-10 08:30:00'),

(7, 1, 'APPROVED',
 'Tôi có thể tham gia đầy đủ thời gian.',
 NULL, '2026-11-10 09:00:00') 