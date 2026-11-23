"""Isolated SQLite tests for attendance code issuance, idempotency, history, and display status."""
import os
import sys
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("JWT_SECRET_KEY", "test_only")

import sqlalchemy

_real_create_engine = sqlalchemy.create_engine
with patch("sqlalchemy.create_engine", lambda *a, **kw: _real_create_engine("sqlite:///:memory:")):
    from app import models  # noqa: F401
    from app.db.session import Base
    from app.models.campaigns import CampaignModel, now_vietnam
    from app.models.notifications import NotificationModel
    from app.models.organizations import OrganizationModel, OrganizationStatus
    from app.models.users import UserModel
    from app.schemas.attendance_codes import AttendanceCodeCreate
    from app.schemas.campaigns import CampaignResponse
    from app.services.attendances import (
        create_attendance_code,
        get_attendance_code_history,
        get_current_attendance_code,
    )
    from app.services.campaigns import derive_display_status
    from app.services.notifications import notify_active_admins

from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker


class AttendanceCodePatchTests(unittest.TestCase):
    def setUp(self):
        self.engine = _real_create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_code_idempotency_history_and_display_status(self):
        admin = UserModel(email="admin@t.com", password_hash="x", full_name="A", role="ADMIN", status="ACTIVE")
        orguser = UserModel(email="org@t.com", password_hash="x", full_name="O", role="ORGANIZER", status="ACTIVE")
        self.db.add_all([admin, orguser])
        self.db.flush()

        org = OrganizationModel(
            name="demo", email="org@o.com", phone="0901234567",
            owner_id=orguser.id, status=OrganizationStatus.APPROVED,
        )
        self.db.add(org)
        self.db.flush()

        now = now_vietnam()
        camp = CampaignModel(
            organization_id=org.id, title="Test", description="Test",
            category="Test", location="Test",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            registration_deadline=now - timedelta(hours=2),
            max_participants=5, estimated_hours=2, status="CLOSED",
        )
        self.db.add(camp)
        self.db.commit()

        self.assertEqual(derive_display_status("CLOSED", camp.start_time, camp.end_time, camp.registration_deadline), "IN_PROGRESS")
        self.assertEqual(derive_display_status("CLOSED", now + timedelta(hours=1), now + timedelta(hours=3), now - timedelta(hours=1)), "REGISTRATION_CLOSED")
        self.assertEqual(derive_display_status("OPEN", now + timedelta(hours=1), now + timedelta(hours=3), now + timedelta(minutes=30)), "REGISTRATION_OPEN")
        self.assertEqual(derive_display_status("CANCELLED", camp.start_time, camp.end_time, camp.registration_deadline), "CANCELLED")
        self.assertEqual(CampaignResponse.model_validate(camp).model_dump()["display_status"], "IN_PROGRESS")

        data = AttendanceCodeCreate(campaign_id=camp.id, expires_minutes=10, code_type="CHECK_IN")
        a = create_attendance_code(self.db, data, orguser)
        b = create_attendance_code(self.db, data, orguser)
        self.assertEqual(a, b)
        self.assertEqual(len(get_attendance_code_history(self.db, camp.id, orguser)), 1)
        self.assertEqual(get_current_attendance_code(self.db, camp.id, orguser)["code"], a["code"])

        with self.assertRaises(HTTPException) as ctx:
            get_current_attendance_code(self.db, camp.id, admin)
        self.assertEqual(ctx.exception.status_code, 403)

        c = create_attendance_code(self.db, AttendanceCodeCreate(campaign_id=camp.id, code_type="CHECK_OUT"), orguser)
        self.assertEqual(c["code_type"], "CHECK_OUT")
        self.assertEqual(len(get_attendance_code_history(self.db, camp.id, orguser)), 2)
        self.assertFalse(get_attendance_code_history(self.db, camp.id, orguser)[1]["is_current"])
        self.assertEqual(create_attendance_code(self.db, AttendanceCodeCreate(campaign_id=camp.id, code_type="CHECK_OUT"), orguser), c)

        notify_active_admins(self.db, "test title", "message")
        self.db.commit()
        self.assertEqual(self.db.query(NotificationModel).filter_by(user_id=admin.id).count(), 1)
        self.assertEqual(self.db.query(NotificationModel).filter_by(user_id=orguser.id).count(), 0)


if __name__ == "__main__":
    unittest.main()
