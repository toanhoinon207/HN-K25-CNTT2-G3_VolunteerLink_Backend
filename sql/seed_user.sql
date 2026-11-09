INSERT INTO users (email, password_hash, full_name, phone, role, status, created_at, updated_at)
VALUES
(
    'admin@volunteerlink.com',
    '$2b$12$KIXQ4J6rXKZQhY9R3uQJzeX1w1T6vN8eQK7sW0LqGmY5F2bH9C3aO',
    'System Admin',
    '0900000001',
    'ADMIN',
    'ACTIVE',
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
),
(
    'user1@volunteerlink.com',
    '$2b$12$KIXQ4J6rXKZQhY9R3uQJzeX1w1T6vN8eQK7sW0LqGmY5F2bH9C3aO',
    'Nguyen Van A',
    '0900000002',
    'USER',
    'ACTIVE',
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
),
(
    'user2@volunteerlink.com',
    '$2b$12$KIXQ4J6rXKZQhY9R3uQJzeX1w1T6vN8eQK7sW0LqGmY5F2bH9C3aO',
    'Tran Thi B',
    '0900000003',
    'USER',
    'ACTIVE',
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
),
(
    'user3@volunteerlink.com',
    '$2b$12$KIXQ4J6rXKZQhY9R3uQJzeX1w1T6vN8eQK7sW0LqGmY5F2bH9C3aO',
    'Le Van C',
    '0900000004',
    'USER',
    'ACTIVE',
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
);
