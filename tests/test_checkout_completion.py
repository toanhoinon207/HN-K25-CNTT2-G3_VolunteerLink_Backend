"""Chạy: python -m unittest discover -s tests -v (tại thư mục BE)."""
import unittest
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Không yêu cầu MySQL/PyMySQL cho bài kiểm thử logic in-memory.
from unittest.mock import patch
with patch("sqlalchemy.create_engine", side_effect=lambda *_a, **_kw: create_engine("sqlite+pysqlite:///:memory:")):
    from app import models  # noqa: F401
from app.db.session import Base
from app.models.campaigns import CampaignModel, now_vietnam
from app.services.campaigns import complete_expired_checkout_campaigns
from app.services.attendances import validate_code
from fastapi import HTTPException


class CheckoutCompletionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def campaign(self, status, code_type, expiry):
        now = now_vietnam()
        row = CampaignModel(
            organization_id=1, title="Kiểm thử", description="Thử", category="Khác",
            location="Hà Nội", start_time=now - timedelta(hours=2),
            end_time=now + timedelta(hours=2), registration_deadline=now - timedelta(hours=3),
            max_participants=10, estimated_hours=2, status=status,
            attendance_code=f"C{self.db.query(CampaignModel).count():05d}", attendance_code_type=code_type,
            attendance_code_expires_at=expiry,
        )
        self.db.add(row)
        self.db.commit()
        return row

    def test_only_expired_checkout_completes(self):
        now = now_vietnam()
        rows = [
            self.campaign("OPEN", "CHECK_OUT", now - timedelta(minutes=1)),
            self.campaign("CLOSED", "CHECK_OUT", now - timedelta(minutes=1)),
            self.campaign("OPEN", "CHECK_IN", now - timedelta(minutes=1)),
            self.campaign("OPEN", None, now - timedelta(minutes=1)),
            self.campaign("OPEN", "CHECK_OUT", now + timedelta(minutes=5)),
            self.campaign("CANCELLED", "CHECK_OUT", now - timedelta(minutes=1)),
        ]
        self.assertEqual(complete_expired_checkout_campaigns(self.db), 2)
        self.db.expire_all()
        self.assertEqual([r.status for r in rows], [
            "COMPLETED", "COMPLETED", "OPEN", "OPEN", "OPEN", "CANCELLED"
        ])
        self.assertEqual(complete_expired_checkout_campaigns(self.db), 0)

    def test_code_type_rejects_wrong_checkin_checkout(self):
        now = now_vietnam()
        campaign = self.campaign("OPEN", "CHECK_IN", now + timedelta(minutes=2))
        validate_code(campaign, campaign.attendance_code, now, "CHECK_IN")
        with self.assertRaises(HTTPException):
            validate_code(campaign, campaign.attendance_code, now, "CHECK_OUT")
        campaign.attendance_code_type = "CHECK_OUT"
        validate_code(campaign, campaign.attendance_code, now, "CHECK_OUT")
        with self.assertRaises(HTTPException):
            validate_code(campaign, campaign.attendance_code, now, "CHECK_IN")


if __name__ == "__main__":
    unittest.main()
