"""Isolated SQLite tests for verified volunteer hours."""
import os
os.environ.setdefault('JWT_SECRET_KEY','local-test-secret-not-for-production')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
import unittest
import sqlalchemy
_real = sqlalchemy.create_engine
sqlalchemy.create_engine = lambda *a,**k: _real('sqlite:///:memory:')
from app.db.session import Base
sqlalchemy.create_engine = _real
from app import models
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.models.users import UserModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.hourclaims import HourClaimModel
from app.schemas.hourclaims import HourClaimCreate, HourClaimReview
from app.services.hour_claim_service import create_hour_claim,review_hour_claim

class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.engine=_real('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        self.db.add_all([UserModel(id=1,email='v@test.vn',password_hash='x',full_name='V',role='USER'),UserModel(id=2,email='o@test.vn',password_hash='x',full_name='O',role='ORGANIZER')])
        self.db.flush()
        self.db.add(OrganizationModel(id=1,name='Org',email='o@x.vn',phone='123',owner_id=2,status=OrganizationStatus.APPROVED))
        self.db.flush()
        self.db.add(CampaignModel(id=1,organization_id=1,title='C',description='D',category='Social',location='Hanoi',start_time=datetime(2026,11,1,8),end_time=datetime(2026,11,1,17),registration_deadline=datetime(2026,10,30),max_participants=20,estimated_hours=8,status='COMPLETED'))
        self.db.flush()
        self.db.add(RegistrationModel(id=1,user_id=1,campaign_id=1,status='APPROVED'))
        self.db.add(AttendanceModel(registration_id=1,check_in_at=datetime(2026,11,1,8),check_out_at=datetime(2026,11,1,10),total_minutes=120,status='PRESENT'))
        self.db.commit()
        self.user=SimpleNamespace(id=1,role='USER')
        self.org=SimpleNamespace(id=2,role='ORGANIZER')
    def tearDown(self):
        self.db.close();self.engine.dispose()
    def create(self,hours='3'):
        return create_hour_claim(self.db,HourClaimCreate(registration_id=1,claimed_hours=Decimal(hours)),self.user)
    def test_approve_above_attendance_rejected(self):
        claim=self.create()
        with self.assertRaises(HTTPException) as ctx:
            review_hour_claim(self.db,claim.id,HourClaimReview(status='VERIFIED',approved_hours=Decimal('3')),self.org)
        self.assertEqual(ctx.exception.status_code,422)
        self.assertEqual(self.db.get(HourClaimModel,claim.id).status,'PENDING')
    def test_default_approval_is_capped(self):
        claim=self.create('3')
        result=review_hour_claim(self.db,claim.id,HourClaimReview(status='VERIFIED'),self.org)
        self.assertEqual(result.approved_hours,Decimal('2.00'))
    def test_valid_lower_approval(self):
        claim=self.create('2')
        result=review_hour_claim(self.db,claim.id,HourClaimReview(status='VERIFIED',approved_hours=Decimal('1.50')),self.org)
        self.assertEqual(result.approved_hours,Decimal('1.50'))
    def test_inconsistent_attendance_blocks_submission(self):
        rec=self.db.query(AttendanceModel).one();rec.total_minutes=150;self.db.commit()
        with self.assertRaises(HTTPException) as ctx:self.create()
        self.assertEqual(ctx.exception.status_code,409)
    def test_inconsistent_attendance_blocks_review(self):
        claim=self.create('2')
        rec=self.db.query(AttendanceModel).one();rec.total_minutes=150;self.db.commit()
        with self.assertRaises(HTTPException) as ctx:
            review_hour_claim(self.db,claim.id,HourClaimReview(status='VERIFIED'),self.org)
        self.assertEqual(ctx.exception.status_code,409)
    def test_existing_verified_prevents_another_review(self):
        claim=self.create('2')
        self.db.add(HourClaimModel(registration_id=1,user_id=1,claimed_hours=Decimal('1'),actual_hours=Decimal('2'),status='VERIFIED',approved_hours=Decimal('1')))
        self.db.commit()
        with self.assertRaises(HTTPException) as ctx:review_hour_claim(self.db,claim.id,HourClaimReview(status='VERIFIED'),self.org)
        self.assertEqual(ctx.exception.status_code,409)

if __name__=='__main__':unittest.main()
