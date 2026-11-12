USE volunteerlink_db;

-- Mật khẩu mặc định:
-- user@gmail.com        -> User@123456
-- admin@gmail.com       -> Admin@123456
-- organizer@gmail.com   -> Organizer@123456
-- organizer2@gmail.com  -> Organizer@123456
-- organizer3@gmail.com  -> Organizer@123456
-- organizer4@gmail.com  -> Organizer@123456 (role USER vì tổ chức đang PENDING)
-- organizer5@gmail.com  -> Organizer@123456 (role USER vì tổ chức đang REJECTED)

INSERT INTO users (
    id, email, password_hash, full_name, phone, role, status, created_at, updated_at
) VALUES
(
    1,
    'user@gmail.com',
    '$2b$12$NTAmkmevU6TxMnAx3UeLauVcmdWyYH7w0uvMI/diJlW5XGwwrQ6mm',
    'Nguyễn Văn User',
    '0901000001',
    'USER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    2,
    'admin@gmail.com',
    '$2b$12$EH8d7a.ZSxNA3c8oNMUrNeU0zbIkANJCPMq6MsAJ3wJ8rt.3JV4Zq',
    'Nguyễn Văn Admin',
    '0901000002',
    'ADMIN',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    3,
    'organizer@gmail.com',
    '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry',
    'Nguyễn Văn Organizer 1',
    '0901000003',
    'ORGANIZER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    4,
    'organizer2@gmail.com',
    '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry',
    'Trần Thị Organizer 2',
    '0901000004',
    'ORGANIZER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    5,
    'organizer3@gmail.com',
    '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry',
    'Lê Văn Organizer 3',
    '0901000005',
    'ORGANIZER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    6,
    'organizer4@gmail.com',
    '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry',
    'Phạm Thị User 4',
    '0901000006',
    'USER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
),
(
    7,
    'organizer5@gmail.com',
    '$2b$12$Sdj46v4CxONKT7k3NPuA0.jzJ33fyfnLpTnyo1ZUe1sSHqcIoz0Ry',
    'Hoàng Văn User 5',
    '0901000007',
    'USER',
    'ACTIVE',
    '2026-11-01 08:00:00',
    '2026-11-01 08:00:00'
);

