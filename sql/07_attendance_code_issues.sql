-- MySQL 8+, run ONCE after backup on the VolunteerLink database.
-- Stores future code issuance history; previously overwritten codes cannot be recovered.
CREATE TABLE IF NOT EXISTS attendance_code_issues (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    issued_by INT NOT NULL,
    code VARCHAR(6) NOT NULL,
    code_type VARCHAR(10) NOT NULL,
    issued_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    INDEX ix_attendance_code_issues_campaign_id (campaign_id),
    INDEX ix_code_issue_campaign_type (campaign_id, code_type),
    CONSTRAINT fk_att_code_issue_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    CONSTRAINT fk_att_code_issue_issuer FOREIGN KEY (issued_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
