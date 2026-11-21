"""SQLite integration-like tests for attendance appeals services (no live MySQL)."""
import os
os.environ.setdefault('JWT_SECRET_KEY', 'local-test-secret-not-for-production')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from types import SimpleNamespace
import unittest
from fastapi import HTTPException
from sqlalchemy import create_engine
# DB layer is MySQL-only in production; replace its startup engine for isolated SQLite tests.
import sqlalchemy
_real_create_engine = sqlalchemy.create_engine
sqlalchemy.create_engine = lambda *args, **kwargs: _real_create_engine("sqlite:///:memory:")
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
sqlalchemy.create_engine = _real_create_engine
from app import models  # noqa
from app.models.users import UserModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.attendance_appeals import AttendanceAppealModel
from app.schemas.attendance_appeals import AttendanceAppealCreate, AttendanceAppealReview
from app.services.attendance_appeals import create_appeal, review_appeal, my_appeals, organizer_appeals

class AttendanceAppealsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            UserModel(id=1, email='vol@test.vn', password_hash='x', full_name='Volunteer', role='USER'),
            UserModel(id=2, email='org@test.vn', password_hash='x', full_name='Organizer', role='ORGANIZER'),
            UserModel(id=3, email='other@test.vn', password_hash='x', full_name='Other', role='ORGANIZER'),
        ])
        self.db.flush()
        self.db.add(OrganizationModel(id=1, name='Org', email='org@example.com', phone='123', owner_id=2, status=OrganizationStatus.APPROVED))
        self.db.flush()
        self.db.add(CampaignModel(id=1, organization_id=1, title='Campaign', description='A', category='Social', location='Hanoi', start_time=datetime(2026,11,1,8), end_time=datetime(2026,11,1,17), registration_deadline=datetime(2026,10,30), max_participants=20, estimated_hours=8, status='COMPLETED'))
        self.db.flush()
        self.db.add(RegistrationModel(id=1, user_id=1, campaign_id=1, status='APPROVED'))
        self.db.commit()
        self.user = SimpleNamespace(id=1)
        self.org = SimpleNamespace(id=2)
        self.other = SimpleNamespace(id=3)
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def submit(self):
        return create_appeal(self.db, AttendanceAppealCreate(registration_id=1, reason='Quên check-out lúc cuối buổi'), self.user)
    def test_missing_attendance_can_appeal_then_accept(self):
        a=self.submit()
        self.assertEqual(a.status,'PENDING')
        self.assertEqual(len(my_appeals(self.db,self.user)),1)
        self.assertEqual(len(organizer_appeals(self.db,self.org)),1)
        decision=AttendanceAppealReview(decision='ACCEPTED', review_note='Đã đối chiếu danh sách', check_in_at=datetime(2026,11,1,8),check_out_at=datetime(2026,11,1,16))
        review_appeal(self.db,a.id,decision,self.org)
        record=self.db.query(AttendanceModel).filter_by(registration_id=1).one()
        self.assertEqual(record.total_minutes,480)
        self.assertEqual(record.status,'PRESENT')
        self.assertEqual(self.db.query(AttendanceAppealModel).first().status,'ACCEPTED')
    def test_other_organizer_rejected_and_no_change(self):
        a=self.submit()
        with self.assertRaises(HTTPException) as ctx:
            review_appeal(self.db,a.id,AttendanceAppealReview(decision='REJECTED',review_note='Không phù hợp'),self.other)
        self.assertEqual(ctx.exception.status_code,403)
        self.assertEqual(self.db.query(AttendanceAppealModel).first().status,'PENDING')
    def test_prevent_duplicate_pending(self):
        self.submit()
        with self.assertRaises(HTTPException) as ctx: self.submit()
        self.assertEqual(ctx.exception.status_code,409)
    def test_accept_without_times_rejected(self):
        a=self.submit()
        with self.assertRaises(HTTPException) as ctx:
            review_appeal(self.db,a.id,AttendanceAppealReview(decision='ACCEPTED',review_note='Đã kiểm tra'),self.org)
        self.assertEqual(ctx.exception.status_code,422)
        self.assertEqual(self.db.query(AttendanceAppealModel).first().status,'PENDING')
    def test_accept_times_outside_campaign_rejected(self):
        a=self.submit()
        with self.assertRaises(HTTPException) as ctx:
            review_appeal(self.db,a.id,AttendanceAppealReview(decision='ACCEPTED', review_note='Đã kiểm tra',check_in_at=datetime(2026,11,1,7),check_out_at=datetime(2026,11,1,17)),self.org)
        self.assertEqual(ctx.exception.status_code,422)
    def test_completed_only(self):
        camp=self.db.get(CampaignModel,1)
        camp.status='CLOSED'
        self.db.commit()
        with self.assertRaises(HTTPException) as ctx: self.submit()
        self.assertEqual(ctx.exception.status_code,400)
    def test_missing_checkout_keep_recorded_checkin(self):
        self.db.add(AttendanceModel(registration_id=1, check_in_at=datetime(2026,11,1,8), total_minutes=0,status='PRESENT'))
        self.db.commit()
        a=self.submit()
        decision=AttendanceAppealReview(decision='ACCEPTED',review_note='Xác nhận ra về', check_out_at=datetime(2026,11,1,16,30))
        review_appeal(self.db,a.id,decision,self.org)
        rec=self.db.query(AttendanceModel).one()
        self.assertEqual(rec.total_minutes,510)

if __name__=='__main__': unittest.main()
