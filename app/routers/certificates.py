from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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


@router.post("", response_model=CertificateDetails, status_code=201)
def issue_certificate(
    payload: IssueCertificate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    return issue_certificate_service(db, payload, current_user.id)
