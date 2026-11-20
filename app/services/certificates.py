
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


from datetime import datetime
from decimal import Decimal, InvalidOperation
from secrets import token_hex
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.certificate import CertificateModel


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


# =====================================================
# 1. TẠO MÃ CHỨNG NHẬN
# =====================================================

def generate_certificate_code():
    """
    Tạo mã chứng nhận có tính duy nhất cao.
    Ví dụ: VL-2026-A82F91C3
    """
    year = now_vietnam().year
    random_code = token_hex(4).upper()

    return f"VL-{year}-{random_code}"


# =====================================================
# 2. TỰ ĐỘNG CẤP CHỨNG NHẬN
# =====================================================

def issue_certificate(
    db: Session,
    user_id: int,
    campaign_id: int,
    verified_hours
):
    """
    Cấp chứng nhận cho tình nguyện viên.

    Hàm này chỉ được gọi sau khi module xác minh
    giờ đóng góp đã xác nhận thành công.

    Mỗi user chỉ có một chứng nhận cho mỗi campaign.
    Chứng nhận đã thu hồi cũng không được cấp lại.
    """

    try:
        total_hours = Decimal(str(verified_hours))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Số giờ xác minh không hợp lệ.")

    if not total_hours.is_finite() or total_hours <= 0:
        raise ValueError(
            "Số giờ đóng góp đã xác minh phải lớn hơn 0."
        )

    if total_hours > Decimal("9999.99"):
        raise ValueError(
            "Số giờ vượt quá giới hạn lưu trữ chứng nhận."
        )

    # Kiểm tra chứng nhận đã tồn tại
    existing_certificate = db.query(
        CertificateModel
    ).filter(
        CertificateModel.user_id == user_id,
        CertificateModel.campaign_id == campaign_id
    ).first()

    if existing_certificate:
        raise ValueError(
            "Tình nguyện viên đã có chứng nhận cho chiến dịch này. "
            "Không thể cấp lại, kể cả khi chứng nhận đã bị thu hồi."
        )

    # Tạo chứng nhận mới
    certificate = CertificateModel(
        certificate_code=generate_certificate_code(),
        user_id=user_id,
        campaign_id=campaign_id,
        total_hours=total_hours,
        status="ACTIVE"
    )

    db.add(certificate)

    try:
        db.commit()
        db.refresh(certificate)

        return certificate

    except IntegrityError:
        db.rollback()

        # Kiểm tra lại nếu một request khác đã cấp đồng thời
        existing_certificate = db.query(
            CertificateModel
        ).filter(
            CertificateModel.user_id == user_id,
            CertificateModel.campaign_id == campaign_id
        ).first()

        if existing_certificate:
            raise ValueError(
                "Chứng nhận cho tình nguyện viên và chiến dịch "
                "này đã tồn tại."
            )

        raise


# =====================================================
# 3. THU HỒI CHỨNG NHẬN
# =====================================================

def revoke_certificate(
    db: Session,
    certificate_id: int,
    admin_id: int,
    reason: str
):
    """
    Admin thu hồi chứng nhận.

    Router phải kiểm tra quyền ADMIN trước khi gọi hàm này.
    """

    certificate = db.query(
        CertificateModel
    ).filter(
        CertificateModel.id == certificate_id
    ).first()

    if not certificate:
        raise LookupError("Không tìm thấy chứng nhận.")

    if certificate.status == "REVOKED":
        raise ValueError(
            "Chứng nhận này đã được thu hồi trước đó."
        )

    reason = reason.strip() if reason else ""

    if not reason:
        raise ValueError(
            "Vui lòng nhập lý do thu hồi chứng nhận."
        )

    certificate.status = "REVOKED"
    certificate.revoked_reason = reason
    certificate.revoked_at = now_vietnam()
    certificate.revoked_by = admin_id

    try:
        db.commit()
        db.refresh(certificate)

        return certificate

    except Exception:
        db.rollback()
        raise


# =====================================================
# 4. TRA CỨU CHỨNG NHẬN CÔNG KHAI
# =====================================================

def get_certificate_by_code(
    db: Session,
    certificate_code: str
):
    """
    Tra cứu chứng nhận bằng mã công khai.

    Trả về thông tin chứng nhận cùng tên tình nguyện viên
    và tên chiến dịch.
    """

    certificate_code = (
        certificate_code.strip()
        if certificate_code
        else ""
    )

    if not certificate_code:
        raise ValueError("Vui lòng nhập mã chứng nhận.")

    certificate = db.query(
        CertificateModel
    ).filter(
        CertificateModel.certificate_code == certificate_code
    ).first()

    if not certificate:
        raise LookupError(
            "Không tìm thấy chứng nhận với mã đã cung cấp."
        )

    return {
        "certificate_code": certificate.certificate_code,
        "volunteer_name": certificate.user.full_name,
        "campaign_name": certificate.campaign.title,
        "total_hours": certificate.total_hours,
        "issued_at": certificate.issued_at,
        "status": certificate.status,
        "revoked_at": certificate.revoked_at,
        "revoked_reason": certificate.revoked_reason
    }


# =====================================================
# 5. DANH SÁCH CHỨNG NHẬN CỦA TÌNH NGUYỆN VIÊN
# =====================================================

def get_my_certificates(
    db: Session,
    user_id: int
):
    """
    Lấy danh sách chứng nhận của tình nguyện viên.
    """

    return db.query(
        CertificateModel
    ).filter(
        CertificateModel.user_id == user_id
    ).order_by(
        CertificateModel.issued_at.desc()
    ).all()


# =====================================================
# 6. ADMIN: DANH SÁCH TẤT CẢ CHỨNG NHẬN
# =====================================================

def get_all_certificates(
    db: Session,
    certificate_status=None,
    campaign_id=None
):
    """
    Admin xem danh sách tất cả chứng nhận.

    Có thể lọc theo trạng thái và chiến dịch.
    """

    query = db.query(CertificateModel)

    if certificate_status:
        if certificate_status not in ["ACTIVE", "REVOKED"]:
            raise ValueError(
                "Trạng thái chứng nhận không hợp lệ."
            )

        query = query.filter(
            CertificateModel.status == certificate_status
        )

    if campaign_id is not None:
        query = query.filter(
            CertificateModel.campaign_id == campaign_id
        )

    return query.order_by(
        CertificateModel.issued_at.desc()
    ).all()
 
