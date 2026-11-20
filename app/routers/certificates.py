from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.schemas.certificates import CertificateResponse
from app.services.notifications import create_notification


router = APIRouter(prefix="/certificates", tags=["Certificates"])


class IssueCertificate(BaseModel):
    campaign_id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    total_hours: Decimal = Field(gt=0, max_digits=6, decimal_places=2)


class CertificateDetails(CertificateResponse):
    campaign_title: str


def details(certificate: CertificateModel) -> CertificateDetails:
    return CertificateDetails(
        **CertificateResponse.model_validate(certificate).model_dump(),
        campaign_title=certificate.campaign.title,
    )


@router.get("/me", response_model=list[CertificateDetails])
def my_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    items = db.query(CertificateModel).options(joinedload(CertificateModel.campaign)).filter(
        CertificateModel.user_id == current_user.id
    ).order_by(CertificateModel.id.desc()).all()
    return [details(item) for item in items]


@router.get("/issued", response_model=list[CertificateDetails])
def issued_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    items = db.query(CertificateModel).options(joinedload(CertificateModel.campaign)).join(
        CertificateModel.campaign
    ).join(CampaignModel.organization).filter(
        OrganizationModel.owner_id == current_user.id
    ).order_by(CertificateModel.id.desc()).all()
    return [details(item) for item in items]


@router.get("/eligible")
def eligible_recipients(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    rows = db.query(RegistrationModel).join(RegistrationModel.campaign).join(
        CampaignModel.organization
    ).options(joinedload(RegistrationModel.campaign), joinedload(RegistrationModel.user)).filter(
        OrganizationModel.owner_id == current_user.id,
        RegistrationModel.status == "APPROVED",
        ~db.query(CertificateModel.id).filter(
            CertificateModel.user_id == RegistrationModel.user_id,
            CertificateModel.campaign_id == RegistrationModel.campaign_id,
            CertificateModel.status == "ACTIVE",
        ).exists(),
    ).order_by(CampaignModel.title, RegistrationModel.id).all()
    return [
        {"campaign_id": row.campaign_id, "campaign_title": row.campaign.title,
         "user_id": row.user_id, "user_name": row.user.full_name}
        for row in rows
    ]


@router.post("", response_model=CertificateDetails, status_code=201)
def issue_certificate(
    payload: IssueCertificate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    campaign = db.query(CampaignModel).join(CampaignModel.organization).filter(
        CampaignModel.id == payload.campaign_id,
        OrganizationModel.owner_id == current_user.id,
    ).with_for_update().first()
    if campaign is None:
        raise HTTPException(403, "Bạn không có quyền cấp chứng nhận cho chiến dịch này.")
    approved = db.query(RegistrationModel.id).filter_by(
        campaign_id=campaign.id, user_id=payload.user_id, status="APPROVED"
    ).first()
    if approved is None:
        raise HTTPException(400, "Tình nguyện viên chưa được duyệt tham gia chiến dịch.")
    if db.query(CertificateModel.id).filter_by(
        campaign_id=campaign.id, user_id=payload.user_id, status="ACTIVE"
    ).first():
        raise HTTPException(409, "Tình nguyện viên đã có chứng nhận cho chiến dịch này.")

    certificate = CertificateModel(
        certificate_code=f"VL-{uuid4().hex.upper()}",
        user_id=payload.user_id,
        campaign_id=campaign.id,
        total_hours=payload.total_hours,
    )
    db.add(certificate)
    create_notification(
        db, payload.user_id,
        "Bạn đã được cấp chứng nhận",
        f'Chiến dịch "{campaign.title}" đã cấp chứng nhận {payload.total_hours} giờ.',
        f"user-dashboard.html?tab=certificates&certificate={certificate.certificate_code}",
    )
    db.commit()
    db.refresh(certificate)
    return details(certificate)
