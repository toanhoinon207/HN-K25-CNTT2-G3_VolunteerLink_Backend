import io
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import sqlalchemy
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

_real_create_engine = sqlalchemy.create_engine
with patch("sqlalchemy.create_engine", lambda *a, **kw: _real_create_engine("sqlite:///:memory:")):
    from app.db.session import Base
    from app import models  # noqa: F401
    from app.models.auth_sessions import AuthSessionModel
    from app.models.campaigns import CampaignModel
    from app.models.organizations import OrganizationModel
    from app.models.registration import RegistrationModel
    from app.models.user_moderation import UserModerationHistoryModel
    from app.models.users import UserModel
    from app.models.waitlist_entry import WaitlistEntryModel
    from app.routers.admin import (
        AdminUserRoleUpdate,
        AdminUserStatusUpdate,
        update_user_role,
        update_user_status,
    )
    from app.schemas.campaigns import CampaignCancelRequest
    from app.schemas.hourclaims import HourClaimCreate
    from app.schemas.organizations import OrganizationCreate
    from app.schemas.users import UserProfileUpdate
    from app.services.admin_dashboard import AdminDashboardService
    from app.services.campaigns import cancel_campaign
    from app.services.organizations import create_organization_service
    from app.services.profile import upload_user_avatar


class AuditRegressionTests(unittest.TestCase):
    def setUp(self):
        self.engine = _real_create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.admin1 = UserModel(
            id=1, email="admin1@example.com", password_hash="x",
            full_name="Admin 1", role="ADMIN", status="ACTIVE",
        )
        self.admin2 = UserModel(
            id=2, email="admin2@example.com", password_hash="x",
            full_name="Admin 2", role="ADMIN", status="ACTIVE",
        )
        self.org_owner = UserModel(
            id=3, email="org@example.com", password_hash="x",
            full_name="Org Owner", role="ORGANIZER", status="ACTIVE",
        )
        self.vol1 = UserModel(
            id=4, email="vol1@example.com", password_hash="x",
            full_name="Vol 1", role="USER", status="ACTIVE",
        )
        self.vol2 = UserModel(
            id=5, email="vol2@example.com", password_hash="x",
            full_name="Vol 2", role="USER", status="LOCKED",
        )
        self.db.add_all([self.admin1, self.admin2, self.org_owner, self.vol1, self.vol2])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_create_organization_notifies_admins(self):
        payload = OrganizationCreate(
            name="Green Org",
            email="green@example.com",
            phone="0901234567",
            address="Hanoi",
            description="Env",
        )
        org = create_organization_service(self.db, payload, owner_id=self.vol1.id)
        self.assertEqual(org.name, "Green Org")
        self.assertEqual(org.status.value, "PENDING")

    def test_cancel_campaign_cancels_waitlisted_and_expires_waitlist(self):
        org = OrganizationModel(
            id=1, name="Org", email="o@example.com", phone="0900000001",
            owner_id=self.org_owner.id, status="APPROVED",
        )
        now = datetime.now()
        camp = CampaignModel(
            id=1, organization_id=1, title="Camp", description="Test campaign",
            category="ENVIRONMENT", location="Hanoi", estimated_hours=4,
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=3),
            registration_deadline=now + timedelta(days=1),
            max_participants=1, status="OPEN",
        )
        reg_approved = RegistrationModel(id=1, user_id=self.vol1.id, campaign_id=1, status="APPROVED")
        reg_wait = RegistrationModel(id=2, user_id=self.vol2.id, campaign_id=1, status="WAITLISTED")
        wl_entry = WaitlistEntryModel(id=1, user_id=self.vol2.id, campaign_id=1, position=1, status="INVITED")
        self.db.add_all([org, camp, reg_approved, reg_wait, wl_entry])
        self.db.commit()

        cancel_campaign(self.db, 1, CampaignCancelRequest(reason="Thời tiết xấu"), self.org_owner)
        self.db.refresh(reg_approved)
        self.db.refresh(reg_wait)
        self.db.refresh(wl_entry)
        self.assertEqual(reg_approved.status, "CANCELLED")
        self.assertEqual(reg_wait.status, "CANCELLED")
        self.assertEqual(wl_entry.status, "EXPIRED")

    def test_admin_cannot_lock_or_demote_other_admin_and_revokes_sessions(self):
        with self.assertRaises(HTTPException) as ctx_lock:
            update_user_status(self.admin2.id, AdminUserStatusUpdate(status="LOCKED"), self.db, self.admin1)
        self.assertEqual(ctx_lock.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx_role:
            update_user_role(self.admin2.id, AdminUserRoleUpdate(role="USER"), self.db, self.admin1)
        self.assertEqual(ctx_role.exception.status_code, 400)

        session = AuthSessionModel(
            id="sess-1", user_id=self.vol1.id, refresh_token_jti="jti-1",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        )
        self.db.add(session)
        self.db.commit()

        update_user_status(self.vol1.id, AdminUserStatusUpdate(status="LOCKED"), self.db, self.admin1)
        self.db.refresh(session)
        self.assertIsNotNone(session.revoked_at)
        logs = self.db.query(UserModerationHistoryModel).filter_by(user_id=self.vol1.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "LOCK")

    def test_admin_dashboard_is_active_reflects_status(self):
        stats = AdminDashboardService.get_admin_dashboard_stats(self.db)
        by_id = {a["id"]: a for a in stats["accounts"]["items"]}
        self.assertTrue(by_id[self.vol1.id]["is_active"])
        self.assertFalse(by_id[self.vol2.id]["is_active"])

    def test_url_validators_and_avatar_magic_bytes(self):
        with self.assertRaises(ValidationError):
            UserProfileUpdate(avatar_url="javascript:alert(1)")
        with self.assertRaises(ValidationError):
            OrganizationCreate(
                name="X", email="x@example.com", phone="0901112223",
                document_url="javascript:alert(1)",
            )
        with self.assertRaises(ValidationError):
            HourClaimCreate(registration_id=1, evidence_url="javascript:alert(1)")

        fake_png = UploadFile(
            filename="evil.png",
            file=io.BytesIO(b"<script>alert(1)</script>"),
            headers={"content-type": "image/png"},
        )
        with self.assertRaises(HTTPException) as ctx:
            upload_user_avatar(self.db, self.vol1, fake_png)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
