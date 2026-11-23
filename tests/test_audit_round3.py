"""Regression tests for 12-item test-round fixes (reset password, checkout anytime, 8h cancel, waitlist, admin detail)."""
import io
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import sqlalchemy
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

_real_create_engine = sqlalchemy.create_engine
with patch("sqlalchemy.create_engine", lambda *a, **kw: _real_create_engine("sqlite:///:memory:")):
    from app.core.config import settings
    from app.core.security import verify_password
    from app.db.session import Base
    from app import models  # noqa: F401
    from app.models.auth_sessions import AuthSessionModel
    from app.models.campaigns import CampaignModel
    from app.models.organizations import OrganizationModel, OrganizationStatus
    from app.models.password_reset_tokens import PasswordResetTokenModel
    from app.models.registration import RegistrationModel
    from app.models.users import UserModel
    from app.models.waitlist_entry import WaitlistEntryModel
    from app.schemas.attendance_codes import AttendanceCodeCreate
    from app.services.attendances import create_attendance_code
    from app.services.auth import request_password_reset, reset_password_with_token
    from app.services.campaigns import get_admin_campaign_detail, upload_campaign_image
    from app.services.registrations import cancel_registration
    from app.services.waitlist import process_expired_invites, respond_to_invite
from app.routers.admin import AdminUserRoleUpdate, update_user_role
from app.routers.waitlist import join_waitlist
from app.schemas.attendances import AttendanceTimeUpdate, ManualAttendanceCreate
from app.schemas.organizations import OrganizationUpdate
from app.services.attendances import manual_attendance, update_attendance_time
from app.services.certificates import revoke_certificate
from app.services.organizations import OrganizationService, update_my_organization_service
from app.services.profile import get_total_hours
from decimal import Decimal
from app.models.hourclaims import HourClaimModel
from app.models.certificate import CertificateModel


class AuditRound3Tests(unittest.TestCase):
    def setUp(self):
        self.engine = _real_create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.org_user = UserModel(id=1, email="org@test.vn", password_hash="x", full_name="Org", role="ORGANIZER")
        self.vol1 = UserModel(id=2, email="v1@test.vn", password_hash="x", full_name="V1", role="USER")
        self.vol2 = UserModel(id=3, email="v2@test.vn", password_hash="x", full_name="V2", role="USER")
        self.db.add_all([self.org_user, self.vol1, self.vol2])
        self.db.flush()

        self.org = OrganizationModel(
            id=1, name="Org", email="org@x.vn", phone="0900000000",
            owner_id=self.org_user.id, status=OrganizationStatus.APPROVED,
        )
        self.db.add(self.org)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_password_reset_via_email_token_revokes_sessions(self):
        session = AuthSessionModel(
            id="s1", user_id=self.vol1.id, refresh_token_jti="jti1",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        )
        self.db.add(session)
        self.db.commit()

        sent = {}
        with patch.object(settings, "SMTP_HOST", "smtp.example.com"), \
             patch.object(settings, "SMTP_USER", "noreply@example.com"), \
             patch.object(settings, "SMTP_PASSWORD", "secret"), \
             patch("app.services.auth._send_reset_email", side_effect=lambda to, link: sent.update(to=to, link=link)):
            request_password_reset(self.db, self.vol1.email)

        self.assertEqual(sent["to"], self.vol1.email)
        raw_token = sent["link"].split("token=")[-1]
        reset_password_with_token(self.db, raw_token, "NewPass123!")

        self.db.refresh(self.vol1)
        self.db.refresh(session)
        self.assertTrue(verify_password("NewPass123!", self.vol1.password_hash))
        self.assertIsNotNone(session.revoked_at)

        with self.assertRaises(HTTPException) as ctx:
            reset_password_with_token(self.db, raw_token, "AnotherPass123!")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_checkout_code_can_be_issued_while_checkin_active(self):
        now = datetime.now()
        camp = CampaignModel(
            id=10, organization_id=1, title="Live", description="D", category="Social", location="HN",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            registration_deadline=now - timedelta(hours=2),
            max_participants=10, estimated_hours=4, status="CLOSED",
        )
        self.db.add(camp)
        self.db.commit()

        in_res = create_attendance_code(
            self.db, AttendanceCodeCreate(campaign_id=10, expires_minutes=30, code_type="CHECK_IN"), self.org_user,
        )
        self.assertEqual(in_res["code_type"], "CHECK_IN")

        out_res = create_attendance_code(
            self.db, AttendanceCodeCreate(campaign_id=10, expires_minutes=15, code_type="CHECK_OUT"), self.org_user,
        )
        self.assertEqual(out_res["code_type"], "CHECK_OUT")
        self.assertNotEqual(in_res["code"], out_res["code"])

    def test_cancel_registration_8_hours_rule(self):
        now = datetime.now()
        camp_ok = CampaignModel(
            id=20, organization_id=1, title="C1", description="D", category="Social", location="HN",
            start_time=now + timedelta(hours=10), end_time=now + timedelta(hours=14),
            registration_deadline=now + timedelta(hours=5), max_participants=5, estimated_hours=4, status="OPEN",
        )
        camp_late = CampaignModel(
            id=21, organization_id=1, title="C2", description="D", category="Social", location="HN",
            start_time=now + timedelta(hours=6), end_time=now + timedelta(hours=10),
            registration_deadline=now + timedelta(hours=2), max_participants=5, estimated_hours=4, status="OPEN",
        )
        reg_ok = RegistrationModel(id=20, user_id=self.vol1.id, campaign_id=20, status="APPROVED")
        reg_late = RegistrationModel(id=21, user_id=self.vol1.id, campaign_id=21, status="APPROVED")
        self.db.add_all([camp_ok, camp_late, reg_ok, reg_late])
        self.db.commit()

        cancelled = cancel_registration(self.db, reg_ok.id, self.vol1.id)
        self.assertEqual(cancelled.status, "CANCELLED")

        with self.assertRaises(HTTPException) as ctx:
            cancel_registration(self.db, reg_late.id, self.vol1.id)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_admin_can_view_pending_campaign_detail_and_upload_image_checks_magic_bytes(self):
        now = datetime.now()
        camp = CampaignModel(
            id=30, organization_id=1, title="Pending Camp", description="D", category="Social", location="HN",
            start_time=now + timedelta(days=2), end_time=now + timedelta(days=3),
            registration_deadline=now + timedelta(days=1), max_participants=5, estimated_hours=4, status="PENDING",
        )
        self.db.add(camp)
        self.db.commit()

        detail = get_admin_campaign_detail(self.db, 30)
        self.assertEqual(detail.status, "PENDING")

        bad = UploadFile(filename="x.png", file=io.BytesIO(b"not-a-png"), headers={"content-type": "image/png"})
        with self.assertRaises(HTTPException) as ctx:
            upload_campaign_image(bad)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_process_expired_invites_handles_multiple_overdue_entries(self):
        now = datetime.now()
        camp = CampaignModel(
            id=40, organization_id=1, title="WL", description="D", category="Social", location="HN",
            start_time=now + timedelta(days=3), end_time=now + timedelta(days=4),
            registration_deadline=now + timedelta(days=2), max_participants=5, estimated_hours=4, status="OPEN",
        )
        w1 = WaitlistEntryModel(
            user_id=self.vol1.id, campaign_id=40, position=1, status="INVITED",
            invited_at=now - timedelta(hours=30), response_deadline=now - timedelta(hours=6),
        )
        w2 = WaitlistEntryModel(
            user_id=self.vol2.id, campaign_id=40, position=2, status="INVITED",
            invited_at=now - timedelta(hours=28), response_deadline=now - timedelta(hours=4),
        )
        self.db.add_all([camp, w1, w2])
        self.db.commit()

        res = process_expired_invites(self.db)
        self.assertEqual(res["processed"], 2)
        self.db.refresh(w1)
        self.db.refresh(w2)
        self.assertEqual(w1.status, "EXPIRED")
        self.assertEqual(w2.status, "EXPIRED")

    def test_rejected_registration_cannot_bypass_via_waitlist(self):
        now = datetime.now()
        camp = CampaignModel(
            id=50, organization_id=1, title="Full Camp", description="D", category="Social", location="HN",
            start_time=now + timedelta(days=3), end_time=now + timedelta(days=4),
            registration_deadline=now + timedelta(days=2), max_participants=1, estimated_hours=4, status="OPEN",
        )
        reg_approved = RegistrationModel(id=50, user_id=self.vol1.id, campaign_id=50, status="APPROVED")
        reg_rejected = RegistrationModel(id=51, user_id=self.vol2.id, campaign_id=50, status="REJECTED", rejection_reason="Khong phu hop")
        self.db.add_all([camp, reg_approved, reg_rejected])
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            join_waitlist(50, self.db, self.vol2)
        self.assertEqual(ctx.exception.status_code, 409)

        wl = WaitlistEntryModel(
            id=50, user_id=self.vol2.id, campaign_id=50, position=1, status="INVITED",
            invited_at=now, response_deadline=now + timedelta(hours=12),
        )
        self.db.add(wl)
        reg_approved.status = "CANCELLED"
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx_resp:
            respond_to_invite(self.db, wl.id, self.vol2.id, "ACCEPTED")
        self.assertEqual(ctx_resp.exception.status_code, 409)
        self.db.refresh(reg_rejected)
        self.assertEqual(reg_rejected.status, "REJECTED")

    def test_verified_hours_and_revoked_certificate_do_not_fallback_to_raw_attendance(self):
        now = datetime.now()
        camp = CampaignModel(
            id=60, organization_id=1, title="Done Camp", description="D", category="Social", location="HN",
            start_time=now - timedelta(days=2, hours=4), end_time=now - timedelta(days=2),
            registration_deadline=now - timedelta(days=3), max_participants=5, estimated_hours=4, status="COMPLETED",
        )
        reg = RegistrationModel(id=60, user_id=self.vol1.id, campaign_id=60, status="APPROVED")
        self.db.add_all([camp, reg])
        self.db.flush()

        # Raw attendance alone must not count as verified hours
        from app.models.attendances import AttendanceModel
        att = AttendanceModel(
            registration_id=60,
            check_in_at=camp.start_time,
            check_out_at=camp.end_time,
            total_minutes=240,
            status="PRESENT",
        )
        self.db.add(att)
        self.db.commit()
        self.assertEqual(get_total_hours(self.db, self.vol1.id), 0.0)

        cert = CertificateModel(
            id=60, certificate_code="VL-TEST-060", user_id=self.vol1.id,
            campaign_id=60, total_hours=Decimal("4.00"), status="ACTIVE",
        )
        claim = HourClaimModel(
            registration_id=60, user_id=self.vol1.id,
            actual_hours=Decimal("4.00"), claimed_hours=Decimal("4.00"),
            approved_hours=Decimal("4.00"), status="VERIFIED",
        )
        self.db.add_all([cert, claim])
        self.db.commit()
        self.assertEqual(get_total_hours(self.db, self.vol1.id), 4.0)

        # When revoked, hours for that campaign must drop to 0.0
        admin = UserModel(id=99, email="adm@test.vn", password_hash="x", full_name="Adm", role="ADMIN")
        self.db.add(admin)
        self.db.commit()
        revoke_certificate(self.db, cert.id, admin.id, "Gian lan")
        self.assertEqual(get_total_hours(self.db, self.vol1.id), 0.0)

    def test_pending_org_cannot_be_edited_and_admin_cannot_promote_user_without_approved_org(self):
        admin = UserModel(id=98, email="adm2@test.vn", password_hash="x", full_name="Adm2", role="ADMIN")
        pending_org = OrganizationModel(
            id=2, name="Pending Org", email="p@x.vn", phone="0901112222",
            owner_id=self.vol1.id, status=OrganizationStatus.PENDING,
        )
        self.db.add_all([admin, pending_org])
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx_edit:
            update_my_organization_service(self.db, OrganizationUpdate(name="Hacked"), self.vol1.id)
        self.assertEqual(ctx_edit.exception.status_code, 409)

        with self.assertRaises(HTTPException) as ctx_role:
            update_user_role(self.vol2.id, AdminUserRoleUpdate(role="ORGANIZER"), self.db, admin)
        self.assertEqual(ctx_role.exception.status_code, 400)

        # Approving the pending org promotes vol1 to ORGANIZER
        reviewed = OrganizationService.review_organization(self.db, pending_org.id, "APPROVE")
        self.assertEqual(reviewed.status, OrganizationStatus.APPROVED)
        self.db.refresh(self.vol1)
        self.assertEqual(self.vol1.role, "ORGANIZER")

    def test_manual_attendance_after_end_time_clamps_checkin_and_allows_checkout_edit(self):
        now = datetime.now()
        camp = CampaignModel(
            id=70, organization_id=1, title="Past Camp", description="D", category="Social", location="HN",
            start_time=now - timedelta(hours=5), end_time=now - timedelta(hours=1),
            registration_deadline=now - timedelta(hours=6), max_participants=5, estimated_hours=4, status="CLOSED",
        )
        reg = RegistrationModel(id=70, user_id=self.vol1.id, campaign_id=70, status="APPROVED")
        self.db.add_all([camp, reg])
        self.db.commit()

        att = manual_attendance(self.db, 70, ManualAttendanceCreate(registration_id=70, status="PRESENT"), self.org_user)
        self.assertLessEqual(att.check_in_at, camp.end_time)

        updated = update_attendance_time(
            self.db, att.id,
            AttendanceTimeUpdate(
                check_in_at=camp.start_time,
                check_out_at=camp.end_time,
                reason="Cap nhat gio thuc te",
            ),
            self.org_user,
        )
        self.assertEqual(updated.total_minutes, 240)


if __name__ == "__main__":
    unittest.main()
