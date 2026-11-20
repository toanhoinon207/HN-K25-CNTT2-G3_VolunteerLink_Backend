
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload


from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.users import UserModel

from app.schemas.certificates import CertificateDetails, IssueCertificate
from app.services.certificates import (
    get_eligible_recipients,
    get_issued_certificates,
    get_my_certificates,
    issue_certificate as issue_certificate_service,
)

from app.schemas.certificates import (
    CertificatePublicResponse,
    CertificateResponse,
    CertificateRevoke,
)
from app.services.certificates import (
    get_all_certificates,
    get_certificate_by_code,
    get_my_certificates,
    revoke_certificate,
)
from app.services.notifications import create_notification


router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/me", response_model=list[CertificateDetails])
def my_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return get_my_certificates(db, current_user.id)


@router.get("/issued", response_model=list[CertificateDetails])
def issued_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    return get_issued_certificates(db, current_user.id)


@router.get("/eligible")
def eligible_recipients(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    return get_eligible_recipients(db, current_user.id)


# =====================================================
# 1. USER: XEM DANH SÁCH CHỨNG NHẬN CỦA BẢN THÂN
# GET /certificates/my-certificates
# =====================================================

@router.get(
    "/my-certificates",
    response_model=list[CertificateResponse]
)
def list_my_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("USER")
    )
):
    return get_my_certificates(
        db,
        current_user.id
    )


# =====================================================
# 2. CÔNG KHAI: TRA CỨU CHỨNG NHẬN BẰNG MÃ
# GET /certificates/verify/{certificate_code}
# =====================================================

@router.get(
    "/verify/{certificate_code}",
    response_model=CertificatePublicResponse
)
def verify_certificate(
    certificate_code: str,
    db: Session = Depends(get_db)
):
    try:
        return get_certificate_by_code(
            db,
            certificate_code
        )

    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================================================
# 3. ADMIN: XEM DANH SÁCH TẤT CẢ CHỨNG NHẬN
# GET /certificates
# =====================================================

@router.get(
    "",
    response_model=list[CertificateResponse]
)
def list_all_certificates(
    certificate_status: Optional[str] = None,
    campaign_id: Optional[int] = None,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ADMIN")
    )
):
    return get_all_certificates(
        db,
        certificate_status,
        campaign_id
    )


@router.post("", response_model=CertificateDetails, status_code=201)
def issue_certificate(
    payload: IssueCertificate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    return issue_certificate_service(db, payload, current_user.id)

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


# =====================================================
# 4. ADMIN: THU HỒI CHỨNG NHẬN
# PATCH /certificates/{certificate_id}/revoke
# =====================================================

@router.patch(
    "/{certificate_id}/revoke",
    response_model=CertificateResponse
)
def revoke_certificate_api(
    certificate_id: int,
    data: CertificateRevoke,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ADMIN")
    )
):
    try:
        return revoke_certificate(
            db=db,
            certificate_id=certificate_id,
            admin_id=current_user.id,
            reason=data.revoked_reason
        )

    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 
