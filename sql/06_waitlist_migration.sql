-- Run once on databases that already have waitlist_entries from the earlier model.
-- Back up the database and check for duplicate (user_id, campaign_id) rows first.
ALTER TABLE waitlist_entries
    ADD COLUMN responded_at DATETIME NULL AFTER response_deadline,
    ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at,
    ADD CONSTRAINT uq_waitlist_user_campaign UNIQUE (user_id, campaign_id);
