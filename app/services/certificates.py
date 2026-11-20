from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
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
    rows = (
        db.query(RegistrationModel)
        .join(RegistrationModel.campaign)
        .join(CampaignModel.organization)
        .options(joinedload(RegistrationModel.campaign), joinedload(RegistrationModel.user))
        .filter(
            OrganizationModel.owner_id == owner_id,
            RegistrationModel.status == "APPROVED",
            ~db.query(CertificateModel.id)
            .filter(
                CertificateModel.user_id == RegistrationModel.user_id,
                CertificateModel.campaign_id == RegistrationModel.campaign_id,
                CertificateModel.status == "ACTIVE",
            )
            .exists(),
        )
        .order_by(CampaignModel.title, RegistrationModel.id)
        .all()
    )
    return [
        {
            "campaign_id": row.campaign_id,
            "campaign_title": row.campaign.title,
            "user_id": row.user_id,
            "user_name": row.user.full_name,
        }
        for row in rows
    ]


def issue_certificate(
    db: Session,
    payload: IssueCertificate,
    owner_id: int,
) -> CertificateDetails:
    campaign = (
        db.query(CampaignModel)
        .join(CampaignModel.organization)
        .filter(
            CampaignModel.id == payload.campaign_id,
            OrganizationModel.owner_id == owner_id,
        )
        .with_for_update()
        .first()
    )
    if campaign is None:
        raise HTTPException(403, "Bạn không có quyền cấp chứng nhận cho chiến dịch này.")

    approved = (
        db.query(RegistrationModel.id)
        .filter_by(campaign_id=campaign.id, user_id=payload.user_id, status="APPROVED")
        .first()
    )
    if approved is None:
        raise HTTPException(400, "Tình nguyện viên chưa được duyệt tham gia chiến dịch.")

    if (
        db.query(CertificateModel.id)
        .filter_by(campaign_id=campaign.id, user_id=payload.user_id, status="ACTIVE")
        .first()
    ):
        raise HTTPException(409, "Tình nguyện viên đã có chứng nhận cho chiến dịch này.")

    certificate = CertificateModel(
        certificate_code=f"VL-{uuid4().hex.upper()}",
        user_id=payload.user_id,
        campaign_id=campaign.id,
        total_hours=payload.total_hours,
    )
    db.add(certificate)
    create_notification(
        db,
        payload.user_id,
        "Bạn đã được cấp chứng nhận",
        f'Chiến dịch "{campaign.title}" đã cấp chứng nhận {payload.total_hours} giờ.',
        f"user-dashboard.html?tab=certificates&certificate={certificate.certificate_code}",
    )
    db.commit()
    db.refresh(certificate)
    return to_certificate_details(certificate)
