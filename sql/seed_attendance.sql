USE volunteerlink_db;
INSERT INTO attendances (
    registration_id,
    check_in_at,
    check_out_at,
    total_minutes,
    status,
    recorded_by,
    updated_by,
    updated_at,
    edit_reason
)
VALUES

(1, '2026-11-14 07:30:00', '2026-11-14 11:30:00',
 240, 'PRESENT', 7, NULL, NULL, NULL),


(2, '2026-11-14 07:45:00', '2026-11-14 11:45:00',
 240, 'PRESENT', 7, NULL, NULL, NULL),

