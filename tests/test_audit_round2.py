"""Regression tests for backend audit round 2 fixes and appeal escalation."""
import os
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import sqlalchemy
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

_real_create_engine = sqlalchemy.create_engine
with patch("sqlalchemy.create_engine", lambda *a, **kw: _real_create_engine("sqlite:///:memory:")):
    from app.db.session import Base
    from app import models  # noqa: F401
    from app.models.attendance_appeals import AttendanceAppealModel
    from app.models.attendances import AttendanceModel
    from app.models.campaigns import CampaignModel
    from app.models.certificate import CertificateModel
    from app.models.hourclaims import HourClaimModel
    from app.models.organizations import OrganizationModel, OrganizationStatus
    from app.models.registration import RegistrationModel
    from app.models.users import UserModel
    from app.schemas.attendance_appeals import (
        AttendanceAppealAdminReview,
        AttendanceAppealCreate,
        AttendanceAppealEscalate,
        AttendanceAppealReview,
    )
    from app.schemas.attendances import AttendanceStatusUpdate, AttendanceTimeUpdate
    from app.schemas.auth import LoginRequest
    from app.schemas.campaigns import CampaignCreate, CampaignUpdate
    from app.schemas.hourclaims import HourClaimAppealCreate, HourClaimAppealReview, HourClaimCreate, HourClaimReview
    from app.schemas.users import ChangePasswordRequest, UserCreate
    from app.services.attendance_appeals import (
        admin_appeals,
        admin_review_appeal,
        create_appeal,
        escalate_appeal,
        review_appeal,
    )
    from app.services.attendances import update_attendance_status, update_attendance_time
    from app.services.hour_claim_service import (
        create_hour_claim,
        create_hour_claim_appeal,
        review_hour_claim,
        review_hour_claim_appeal,
    )


class AuditRound2Tests(unittest.TestCase):
    def setUp(self):
        self.engine = _real_create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.admin = UserModel(id=1, email="admin@test.vn", password_hash="x", full_name="Admin", role="ADMIN")
        self.org_user = UserModel(id=2, email="org@test.vn", password_hash="x", full_name="Organizer", role="ORGANIZER")
        self.vol = UserModel(id=3, email="vol@test.vn", password_hash="x", full_name="Volunteer", role="USER")
        self.db.add_all([self.admin, self.org_user, self.vol])
        self.db.flush()

        self.org = OrganizationModel(
            id=1, name="Org", email="org@x.vn", phone="0900000000",
            owner_id=self.org_user.id, status=OrganizationStatus.APPROVED,
        )
        self.db.add(self.org)
        self.db.flush()

        self.camp = CampaignModel(
            id=1, organization_id=1, title="Camp", description="Desc",
            category="Social", location="Hanoi",
            start_time=datetime(2026, 11, 1, 8, 0),
            end_time=datetime(2026, 11, 1, 17, 0),
            registration_deadline=datetime(2026, 10, 30, 0, 0),
            max_participants=10, estimated_hours=8, status="COMPLETED",
        )
        self.db.add(self.camp)
        self.db.flush()

        self.reg = RegistrationModel(id=1, user_id=self.vol.id, campaign_id=1, status="APPROVED")
        self.db.add(self.reg)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_schema_hardening(self):
        long_pw = "a" * 73
        with self.assertRaises(ValidationError):
            UserCreate(email="a@b.com", password=long_pw, full_name="A")
        with self.assertRaises(ValidationError):
            LoginRequest(email="a@b.com", password=long_pw)
        with self.assertRaises(ValidationError):
            ChangePasswordRequest(old_password="oldpassword", new_password=long_pw)
        with self.assertRaises(ValidationError):
            CampaignCreate(
                title="T", description="D", image_url="javascript:alert(1)",
                category="C", location="L",
                start_time=datetime(2026, 11, 1, 8), end_time=datetime(2026, 11, 1, 10),
                registration_deadline=datetime(2026, 10, 30), max_participants=5, estimated_hours=2,
            )
        with self.assertRaises(ValidationError):
            CampaignUpdate(title="")
        with self.assertRaises(ValidationError):
            AttendanceAppealCreate(registration_id=1, reason="Quen check out luc ve", evidence_url="javascript:alert(1)")
        with self.assertRaises(ValidationError):
            HourClaimCreate(registration_id=1, claimed_hours=Decimal("10000.00"))

    def test_attendance_locked_after_verified_claim_and_time_bounds(self):
        att = AttendanceModel(
            registration_id=1,
            check_in_at=datetime(2026, 11, 1, 8, 0),
            check_out_at=datetime(2026, 11, 1, 12, 0),
            total_minutes=240,
            status="PRESENT",
        )
        self.db.add(att)
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx_out:
            update_attendance_time(
                self.db, att.id,
                AttendanceTimeUpdate(check_out_at=datetime(2026, 11, 1, 20, 0), reason="Sua gio"),
                self.org_user,
            )
        self.assertEqual(ctx_out.exception.status_code, 422)

        claim = create_hour_claim(self.db, HourClaimCreate(registration_id=1, claimed_hours=Decimal("4.00")), self.vol)
        review_hour_claim(self.db, claim.id, HourClaimReview(status="VERIFIED"), self.org_user)

        with self.assertRaises(HTTPException) as ctx_status:
            update_attendance_status(
                self.db, att.id, AttendanceStatusUpdate(status="ABSENT", reason="Huy"), self.org_user,
            )
        self.assertEqual(ctx_status.exception.status_code, 409)

        with self.assertRaises(HTTPException) as ctx_time:
            update_attendance_time(
                self.db, att.id,
                AttendanceTimeUpdate(check_out_at=datetime(2026, 11, 1, 13, 0), reason="Sua"),
                self.org_user,
            )
        self.assertEqual(ctx_time.exception.status_code, 409)

    def test_under_approved_hour_claim_can_appeal_to_admin_and_update_cert(self):
        att = AttendanceModel(
            registration_id=1,
            check_in_at=datetime(2026, 11, 1, 8, 0),
            check_out_at=datetime(2026, 11, 1, 14, 0),
            total_minutes=360,
            status="PRESENT",
        )
        self.db.add(att)
        self.db.commit()

        claim = create_hour_claim(self.db, HourClaimCreate(registration_id=1, claimed_hours=Decimal("6.00")), self.vol)
        review_hour_claim(
            self.db, claim.id,
            HourClaimReview(status="VERIFIED", approved_hours=Decimal("3.00")),
            self.org_user,
        )
        cert = self.db.query(CertificateModel).filter_by(user_id=self.vol.id, campaign_id=1).one()
        self.assertEqual(cert.total_hours, Decimal("3.00"))

        create_hour_claim_appeal(
            self.db, claim.id,
            HourClaimAppealCreate(appeal_reason="Toi lam du 6 gio theo diem danh"),
            self.vol,
        )
        with self.assertRaises(HTTPException) as ctx_over:
            review_hour_claim_appeal(
                self.db, claim.id,
                HourClaimAppealReview(appeal_status="ACCEPTED", approved_hours=Decimal("7.00"), admin_note="Vuot diem danh"),
                self.admin,
            )
        self.assertEqual(ctx_over.exception.status_code, 422)

        updated_claim = review_hour_claim_appeal(
            self.db, claim.id,
            HourClaimAppealReview(appeal_status="ACCEPTED", approved_hours=Decimal("6.00"), admin_note="Dong y"),
            self.admin,
        )
        self.assertEqual(updated_claim.approved_hours, Decimal("6.00"))
        self.db.refresh(cert)
        self.assertEqual(cert.total_hours, Decimal("6.00"))

    def test_attendance_appeal_escalation_to_admin(self):
        appeal = create_appeal(
            self.db,
            AttendanceAppealCreate(registration_id=1, reason="Quen quet ma check-out cuoi gio"),
            self.vol,
        )
        review_appeal(
            self.db, appeal.id,
            AttendanceAppealReview(decision="REJECTED", review_note="Khong thay ten trong danh sach"),
            self.org_user,
        )
        escalated = escalate_appeal(
            self.db, appeal.id,
            AttendanceAppealEscalate(escalation_reason="Toi co anh chup minh chung tham gia du buoi"),
            self.vol,
        )
        self.assertEqual(escalated.status, "ADMIN_PENDING")
        self.assertEqual(len(admin_appeals(self.db)), 1)

        resolved = admin_review_appeal(
            self.db, appeal.id,
            AttendanceAppealAdminReview(
                decision="ACCEPTED",
                admin_note="Minh chung hop le",
                check_in_at=datetime(2026, 11, 1, 8, 0),
                check_out_at=datetime(2026, 11, 1, 16, 0),
            ),
            self.admin,
        )
        self.assertEqual(resolved.status, "ADMIN_ACCEPTED")
        att = self.db.query(AttendanceModel).filter_by(registration_id=1).one()
        self.assertEqual(att.total_minutes, 480)


if __name__ == "__main__":
    unittest.main()
