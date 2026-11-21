"""Certificate endpoints: merge of feature and develop branches.

Certificate issuance is delegated to the validated service; no direct issuance
logic is reintroduced from develop.
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.certificate import CertificateModel
from app.models.users import UserModel
from app.schemas.certificates import (
    CertificateDetails,
    CertificateResponse,
    IssueCertificate,
)
from app.services.certificates import (
    get_eligible_recipients,
    get_issued_certificates,
    get_my_certificates,
    issue_certificate as issue_certificate_service,
    revoke_certificate as revoke_certificate_service,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/certificates", tags=["Certificates"])


class CertificatePublicVerification(BaseModel):
    certificate_code: str
    campaign_title: str
    total_hours: float
    status: Literal["ACTIVE", "REVOKED"]


class CertificateRevokeBody(BaseModel):
    revoked_reason: str = Field(min_length=1, max_length=1000)


# USER: original endpoint used by the current frontend.
@router.get("/me", response_model=list[CertificateDetails])
def my_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return get_my_certificates(db, current_user.id)


# Legacy alias from develop; same data, no duplicated query logic.
@router.get("/my-certificates", response_model=list[CertificateDetails])
def list_my_certificates(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER")),
):
    return get_my_certificates(db, current_user.id)


# ORGANIZER
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


@router.post("", response_model=CertificateDetails, status_code=201)
def issue_certificate(
    payload: IssueCertificate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    # This service enforces COMPLETED + VERIFIED hours + ownership.
    return issue_certificate_service(db, payload, current_user.id)


# PUBLIC: verify a certificate by its code, without exposing personal details.
@router.get("/verify/{certificate_code}", response_model=CertificatePublicVerification)
def verify_certificate(
    certificate_code: str,
    db: Session = Depends(get_db),
):
    certificate = (
        db.query(CertificateModel)
        .options(joinedload(CertificateModel.campaign))
        .filter(CertificateModel.certificate_code == certificate_code)
        .first()
    )
    if certificate is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng chỉ.")
    return CertificatePublicVerification(
        certificate_code=certificate.certificate_code,
        campaign_title=certificate.campaign.title,
        total_hours=float(certificate.total_hours),
        status=certificate.status,
    )


# ADMIN: list all certificates (develop endpoint).
@router.get("", response_model=list[CertificateResponse])
def list_all_certificates(
    certificate_status: Optional[Literal["ACTIVE", "REVOKED"]] = Query(default=None, alias="status"),
    campaign_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    query = db.query(CertificateModel)
    if certificate_status is not None:
        query = query.filter(CertificateModel.status == certificate_status)
    if campaign_id is not None:
        query = query.filter(CertificateModel.campaign_id == campaign_id)
    return query.order_by(CertificateModel.id.desc()).all()


# ADMIN: legacy revoke endpoint from develop.
# Note: /api/admin/certificates/{id}/revoke also exists; consider
# consolidating into one service after the merge.
@router.patch("/{certificate_id}/revoke", response_model=CertificateResponse)
def revoke_certificate_api(
    certificate_id: int,
    data: CertificateRevokeBody,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    reason = data.revoked_reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Vui lòng nhập lý do thu hồi chứng chỉ.")

    try:
        return revoke_certificate_service(
            db=db,
            certificate_id=certificate_id,
            admin_id=current_user.id,
            reason=reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
