from uuid import uuid4
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.campaigns import CampaignModel
from app.models.hourclaims import HourClaimModel
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
    """Only completed campaigns with one verified, positive hour claim qualify."""
    rows = (
        db.query(RegistrationModel, HourClaimModel)
        .join(RegistrationModel.campaign)
        .join(CampaignModel.organization)
        .join(HourClaimModel, HourClaimModel.registration_id == RegistrationModel.id)
        .options(joinedload(RegistrationModel.campaign), joinedload(RegistrationModel.user))
        .filter(
            OrganizationModel.owner_id == owner_id,
            RegistrationModel.status == "APPROVED",
            CampaignModel.status == "COMPLETED",
            HourClaimModel.status == "VERIFIED",
            HourClaimModel.approved_hours > 0,
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
    # An inconsistent database containing multiple VERIFIED claims must not
    # offer an ambiguous number of hours for issuing a certificate.
    counts = {}
    for registration, claim in rows:
        counts[registration.id] = counts.get(registration.id, 0) + 1
    return [
        {
            "campaign_id": registration.campaign_id,
            "campaign_title": registration.campaign.title,
            "user_id": registration.user_id,
            "user_name": registration.user.full_name,
            "approved_hours": claim.approved_hours,
        }
        for registration, claim in rows if counts[registration.id] == 1
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

    if campaign.status != "COMPLETED":
        raise HTTPException(400, "Chiến dịch chưa hoàn thành; không thể cấp chứng chỉ.")

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

    verified_claims = (
        db.query(HourClaimModel)
        .join(RegistrationModel, RegistrationModel.id == HourClaimModel.registration_id)
        .filter(
            RegistrationModel.campaign_id == campaign.id,
            RegistrationModel.user_id == payload.user_id,
            RegistrationModel.status == "APPROVED",
            HourClaimModel.status == "VERIFIED",
        )
        .all()
    )
    if len(verified_claims) != 1 or verified_claims[0].approved_hours is None:
        raise HTTPException(400, "Tình nguyện viên phải có đúng một yêu cầu giờ đã xác minh.")
    approved_hours = Decimal(str(verified_claims[0].approved_hours))
    if approved_hours <= 0:
        raise HTTPException(400, "Số giờ đã xác minh phải lớn hơn 0.")
    if payload.total_hours != approved_hours:
        raise HTTPException(422, "Số giờ trên chứng chỉ phải bằng số giờ đã xác minh.")

    certificate = CertificateModel(
        certificate_code=f"VL-{uuid4().hex.upper()}",
        user_id=payload.user_id,
        campaign_id=campaign.id,
        total_hours=approved_hours,
    )
    db.add(certificate)
    create_notification(
        db,
        payload.user_id,
        "Bạn đã được cấp chứng nhận",
        f'Chiến dịch "{campaign.title}" đã cấp chứng nhận {approved_hours} giờ.',
        f"user-dashboard.html?tab=certificates&certificate={certificate.certificate_code}",
    )
    db.commit()
    db.refresh(certificate)
    return to_certificate_details(certificate)
