-- Chạy trên MySQL hiện có. Sao lưu trước khi migration.
CREATE TABLE IF NOT EXISTS attendance_appeals (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    registration_id INT NOT NULL,
    user_id INT NOT NULL,
    reason TEXT NOT NULL,
    evidence_url VARCHAR(500) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    organizer_id INT NULL,
    review_note TEXT NULL,
    reviewed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_attendance_appeals_registration_id (registration_id),
    INDEX ix_attendance_appeals_user_id (user_id),
    CONSTRAINT fk_attendance_appeals_registration FOREIGN KEY (registration_id) REFERENCES registrations(id),
    CONSTRAINT fk_attendance_appeals_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_attendance_appeals_organizer FOREIGN KEY (organizer_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
