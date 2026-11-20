from uuid import uuid4
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.hourclaims import HourClaimModel
from app.schemas.certificates import CertificateDetails, CertificateResponse, IssueCertificate
from app.services.notifications import create_notification


def to_certificate_details(certificate: CertificateModel) -> CertificateDetails:
    return CertificateDetails(
        **CertificateResponse.model_validate(certificate).model_dump(),
        campaign_title=certificate.campaign.title,
    )


def get_my_certificates(db: Session, user_id: int) -> list[CertificateDetails]:
    items = (
        db.query(CertificateModel)
        .options(joinedload(CertificateModel.campaign))
        .filter(CertificateModel.user_id == user_id)
        .order_by(CertificateModel.id.desc())
        .all()
    )
    return [to_certificate_details(item) for item in items]


def get_issued_certificates(db: Session, owner_id: int) -> list[CertificateDetails]:
    items = (
        db.query(CertificateModel)
        .options(joinedload(CertificateModel.campaign))
        .join(CertificateModel.campaign)
        .join(CampaignModel.organization)
        .filter(OrganizationModel.owner_id == owner_id)
        .order_by(CertificateModel.id.desc())
        .all()
    )
    return [to_certificate_details(item) for item in items]


def get_eligible_recipients(db: Session, owner_id: int) -> list[dict]:
    """Only completed campaigns with a verified, positive hour claim qualify."""
    rows = (
        db.query(RegistrationModel, HourClaimModel)
        .join(RegistrationModel.campaign)
        .join(CampaignModel.organization)
        .join(HourClaimModel, HourClaimModel.registration_id == RegistrationModel.id)
        .options(joinedload(RegistrationModel.campaign), joinedload(RegistrationModel.user))
        .filter(
            OrganizationModel.owner_id == owner_id,
            CampaignModel.status == "COMPLETED",
            RegistrationModel.status == "APPROVED",
            HourClaimModel.status == "VERIFIED",
            HourClaimModel.approved_hours > 0,
            HourClaimModel.user_id == RegistrationModel.user_id,
            ~db.query(CertificateModel.id)
            .filter(
                CertificateModel.user_id == RegistrationModel.user_id,
                CertificateModel.campaign_id == RegistrationModel.campaign_id,
                CertificateModel.status == "ACTIVE",
            ).exists(),
        )
        .order_by(CampaignModel.title, RegistrationModel.id)
        .all()
    )
    # Hide ambiguous legacy data: more than one VERIFIED claim is not eligible.
    counts = {}
    for registration, _ in rows:
        counts[registration.id] = counts.get(registration.id, 0) + 1
    return [
        {
            "campaign_id": registration.campaign_id,
            "campaign_title": registration.campaign.title,
            "user_id": registration.user_id,
            "user_name": registration.user.full_name,
            "verified_hours": claim.approved_hours,
        }
        for registration, claim in rows
        if counts[registration.id] == 1
    ]


def issue_certificate(
    db: Session,
    payload: IssueCertificate,
    owner_id: int,
) -> CertificateDetails:
    campaign = (
        db.query(CampaignModel)