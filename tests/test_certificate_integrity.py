"""Certificate issuance checks against the authoritative verified hour claim."""
import os
os.environ.setdefault('JWT_SECRET_KEY', 'local-test-secret-not-for-production')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from decimal import Decimal
import unittest
import sqlalchemy
real_create_engine = sqlalchemy.create_engine
sqlalchemy.create_engine = lambda *args, **kwargs: real_create_engine('sqlite:///:memory:')
from app.db.session import Base
sqlalchemy.create_engine = real_create_engine
from app import models
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.models.users import UserModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.hourclaims import HourClaimModel
from app.models.certificate import CertificateModel
from app.schemas.certificates import IssueCertificate
from app.services.certificates import get_eligible_recipients, issue_certificate

class CertificatesTests(unittest.TestCase):
    def setUp(self):
        self.engine = real_create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            UserModel(id=1, email='vol@test.vn', password_hash='x', full_name='Volunteer', role='USER'),
            UserModel(id=2, email='owner@test.vn', password_hash='x', full_name='Organizer', role='ORGANIZER'),
            UserModel(id=3, email='else@test.vn', password_hash='x', full_name='Other', role='ORGANIZER'),
        ])
        self.db.flush()
        self.db.add(OrganizationModel(id=1, name='Org', email='org@test.vn', phone='123', owner_id=2, status=OrganizationStatus.APPROVED))
        self.db.flush()
        self.db.add(CampaignModel(id=1, organization_id=1, title='Camp', description='Description', category='Social', location='Hanoi', start_time=datetime(2026, 11, 1, 8), end_time=datetime(2026, 11, 1, 17), registration_deadline=datetime(2026, 10, 30), max_participants=20, estimated_hours=8, status='COMPLETED'))
        self.db.flush()
        self.db.add(RegistrationModel(id=1, user_id=1, campaign_id=1, status='APPROVED'))
        self.db.commit()
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def payload(self, hours='2.50'):
        return IssueCertificate(campaign_id=1, user_id=1, total_hours=Decimal(hours))
    def verify(self, hours='2.50'):
        self.db.add(HourClaimModel(registration_id=1, user_id=1, claimed_hours=Decimal(hours), actual_hours=Decimal('3.00'), approved_hours=Decimal(hours), status='VERIFIED'))
        self.db.commit()
    def fails(self, code, hours='2.50', owner=2):
        with self.assertRaises(HTTPException) as ctx:
            issue_certificate(self.db, self.payload(hours), owner)
        self.assertEqual(ctx.exception.status_code, code)
    def test_no_verified_claim_blocks(self):
        self.assertEqual(get_eligible_recipients(self.db, 2), [])
        self.fails(400)
    def test_completed_required(self):
        self.verify()
        campaign = self.db.get(CampaignModel, 1)
        campaign.status = 'CLOSED'
        self.db.commit()
        self.assertEqual(get_eligible_recipients(self.db, 2), [])
        self.fails(400)
    def test_verified_hours_are_authoritative(self):
        self.verify()
        eligible = get_eligible_recipients(self.db, 2)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0]['approved_hours'], Decimal('2.50'))
        self.fails(422, '5.00')
        issued = issue_certificate(self.db, self.payload(), 2)
        self.assertEqual(issued.total_hours, Decimal('2.50'))
        self.fails(409)
        self.assertEqual(get_eligible_recipients(self.db, 2), [])
    def test_wrong_organizer_denied(self):
        self.verify()
        self.fails(403, owner=3)
    def test_rejected_claim_blocks(self):
        self.verify()
        self.db.query(HourClaimModel).update({'status':'REJECTED'})
        self.db.commit()
        self.fails(400)
    def test_ambiguous_multiple_verified_claims_blocks(self):
        self.verify()
        self.verify()
        self.assertEqual(get_eligible_recipients(self.db, 2), [])
        self.fails(400)

if __name__ == '__main__':
    unittest.main()
