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
    campaign = certificate.campaign
    organization_name = (
        campaign.organization.name
        if campaign is not None and campaign.organization is not None
        else None
    )
    volunteer_name = certificate.user.full_name if certificate.user is not None else None
    return CertificateDetails(
        **CertificateResponse.model_validate(certificate).model_dump(),
        campaign_title=campaign.title if campaign is not None else "",
        organization_name=organization_name,
        volunteer_name=volunteer_name,
    )


def get_my_certificates(db: Session, user_id: int) -> list[CertificateDetails]:
    items = (
        db.query(CertificateModel)
        .options(
            joinedload(CertificateModel.campaign).joinedload(CampaignModel.organization),
            joinedload(CertificateModel.user),
        )
        .filter(CertificateModel.user_id == user_id)
        .order_by(CertificateModel.id.desc())
        .all()
    )
    return [to_certificate_details(item) for item in items]


def get_issued_certificates(db: Session, owner_id: int) -> list[CertificateDetails]:
    items = (
        db.query(CertificateModel)
        .options(
            joinedload(CertificateModel.campaign).joinedload(CampaignModel.organization),
            joinedload(CertificateModel.user),
        )
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

    if campaign.status != "COMPLETED":
        raise HTTPException(400, "Chỉ cấp chứng nhận khi chiến dịch đã hoàn thành.")

    verified_claims = (
        db.query(HourClaimModel)
        .join(RegistrationModel, RegistrationModel.id == HourClaimModel.registration_id)
        .filter(
            RegistrationModel.campaign_id == campaign.id,
            RegistrationModel.user_id == payload.user_id,
            HourClaimModel.user_id == payload.user_id,
            HourClaimModel.status == "VERIFIED",
        )
        .all()
    )
    if len(verified_claims) != 1 or verified_claims[0].approved_hours is None:
        raise HTTPException(400, "Cần đúng một yêu cầu giờ đã xác minh trước khi cấp chứng nhận.")

    verified_hours = Decimal(str(verified_claims[0].approved_hours))
    if verified_hours <= 0:
        raise HTTPException(400, "Số giờ đã xác minh phải lớn hơn 0.")
    if payload.total_hours != verified_hours:
        raise HTTPException(422, "Số giờ chứng nhận phải khớp số giờ đã xác minh.")

    # Không tự phát hành lại chứng chỉ đã bị thu hồi: cần quy trình riêng.
    if (
        db.query(CertificateModel.id)
        .filter_by(campaign_id=campaign.id, user_id=payload.user_id)
        .first()
    ):
        raise HTTPException(409, "Chiến dịch và tình nguyện viên này đã có chứng chỉ (kể cả đã thu hồi).")

    certificate = CertificateModel(
        certificate_code=f"VL-{uuid4().hex.upper()}",
        user_id=payload.user_id,
        campaign_id=campaign.id,
        total_hours=verified_hours,
    )
    db.add(certificate)
    create_notification(
        db,
        payload.user_id,
        "Bạn đã được cấp chứng nhận",
        f'Chiến dịch "{campaign.title}" đã cấp chứng nhận {verified_hours} giờ.',
        f"user-dashboard.html?tab=certificates&certificate={certificate.certificate_code}",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Không thể cấp chứng chỉ do xung đột dữ liệu.")
    db.refresh(certificate)
    loaded = (
        db.query(CertificateModel)
        .options(
            joinedload(CertificateModel.campaign).joinedload(CampaignModel.organization),
            joinedload(CertificateModel.user),
        )
        .filter(CertificateModel.id == certificate.id)
        .first()
    )
    return to_certificate_details(loaded or certificate)


# Các hàm bổ sung từ develop, giữ tương thích schema/model hiện tại.
def get_certificate_by_code(db: Session, certificate_code: str) -> dict:
    code = (certificate_code or "").strip()
    if not code:
        raise ValueError("Vui lòng nhập mã chứng chỉ.")
    certificate = (
        db.query(CertificateModel)
        .options(joinedload(CertificateModel.user), joinedload(CertificateModel.campaign))
        .filter(CertificateModel.certificate_code == code)
        .first()
    )
    if certificate is None:
        raise LookupError("Không tìm thấy chứng chỉ.")
    return {
        "certificate_code": certificate.certificate_code,
        "volunteer_name": certificate.user.full_name,
        "campaign_name": certificate.campaign.title,
        "total_hours": certificate.total_hours,
        "issued_at": certificate.issued_at,
        "status": certificate.status,
        "revoked_reason": certificate.revoked_reason,
    }


def get_all_certificates(
    db: Session, certificate_status: str | None = None, campaign_id: int | None = None
) -> list[CertificateModel]:
    query = db.query(CertificateModel)
    if certificate_status is not None:
        certificate_status = certificate_status.upper()
        if certificate_status not in {"ACTIVE", "REVOKED"}:
            raise ValueError("Trạng thái chứng chỉ không hợp lệ.")
        query = query.filter(CertificateModel.status == certificate_status)
    if campaign_id is not None:
        query = query.filter(CertificateModel.campaign_id == campaign_id)
    return query.order_by(CertificateModel.id.desc()).all()


def revoke_certificate(
    db: Session, certificate_id: int, admin_id: int, reason: str
) -> CertificateModel:
    """Router chịu trách nhiệm xác thực quyền ADMIN.

    Không dùng revoked_at/revoked_by vì chúng chưa có trên model hiện tại.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("Vui lòng nhập lý do thu hồi chứng chỉ.")
    certificate = (
        db.query(CertificateModel)
        .filter(CertificateModel.id == certificate_id)
        .with_for_update()
        .first()
    )
    if certificate is None:
        raise LookupError("Không tìm thấy chứng chỉ.")
    if certificate.status == "REVOKED":
        raise ValueError("Chứng chỉ đã bị thu hồi.")
    certificate.status = "REVOKED"
    certificate.revoked_reason = reason
    create_notification(
        db=db,
        user_id=certificate.user_id,
        title="Chứng chỉ đã bị thu hồi",
        content=f"Chứng chỉ mã {certificate.certificate_code} đã bị thu hồi. Lý do: {reason}",
        link="user-dashboard.html?tab=certificates",
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(certificate)
    return certificate
