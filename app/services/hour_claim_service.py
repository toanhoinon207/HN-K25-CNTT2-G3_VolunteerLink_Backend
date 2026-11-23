from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from app.services.notifications import create_notification, notify_campaign_organizer, notify_active_admins
from sqlalchemy.orm import Session, joinedload

from app.models.hourclaims import HourClaimModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.organizations import OrganizationModel
from app.schemas.certificates import IssueCertificate
from app.services.certificates import issue_certificate

from app.schemas.hourclaims import (
    HourClaimCreate,
    HourClaimReview,
    HourClaimAppealCreate,
    HourClaimAppealReview
)


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


# =====================================================
# HÀM HỖ TRỢ
# =====================================================

def get_claim(db: Session, claim_id: int):

    claim = db.query(HourClaimModel).filter(
        HourClaimModel.id == claim_id
    ).first()

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy yêu cầu xác minh giờ đóng góp"
        )

    return claim


def check_organizer_campaign(
    db: Session,
    campaign_id: int,
    current_user
):

    campaign = db.query(CampaignModel).filter(
        CampaignModel.id == campaign_id
    ).first()

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Chiến dịch không tồn tại"
        )

    organization = db.query(OrganizationModel).filter(
        OrganizationModel.id == campaign.organization_id,
        OrganizationModel.owner_id == current_user.id
    ).first()

    if organization is None:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền quản lý chiến dịch này"
        )

    return campaign


def check_claim_access(
    db: Session,
    claim: HourClaimModel,
    current_user
):

    if current_user.role == "ADMIN":
        return

    if current_user.role == "USER":

        if claim.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền truy cập yêu cầu này"
            )

        return

    if current_user.role == "ORGANIZER":

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == claim.registration_id
        ).first()

        if registration is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy thông tin đăng ký"
            )

        check_organizer_campaign(
            db,
            registration.campaign_id,
            current_user
        )

        return

    raise HTTPException(
        status_code=403,
        detail="Bạn không có quyền truy cập"
    )


def verified_attendance_hours(db: Session, registration_id: int):
    """Return decimal hours supported by a complete, consistent attendance record."""
    attendance = db.query(AttendanceModel).filter(
        AttendanceModel.registration_id == registration_id
    ).first()
    if not attendance or attendance.status != "PRESENT":
        raise HTTPException(400, "Không có điểm danh hợp lệ để xác minh giờ")
    start, end = attendance.check_in_at, attendance.check_out_at
    if start is None or end is None or end <= start:
        raise HTTPException(400, "Điểm danh CHECK-IN/CHECK-OUT chưa hợp lệ")
    minutes = int(round((end - start).total_seconds() / 60))
    if minutes <= 0 or attendance.total_minutes != minutes:
        raise HTTPException(409, "Số phút điểm danh không khớp mốc thời gian; cần kiểm tra dữ liệu")
    return (Decimal(minutes) / Decimal("60")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


# =====================================================
# 1. TNV: TẠO YÊU CẦU XÁC MINH GIỜ
# =====================================================

def create_hour_claim(
    db: Session,
    data: HourClaimCreate,
    current_user
):

    try:

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == data.registration_id,
            RegistrationModel.user_id == current_user.id
        ).with_for_update().first()

        if registration is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy đăng ký của bạn"
            )

        if registration.status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail="Đăng ký chưa được Organizer duyệt"
            )

        campaign = db.query(CampaignModel).filter(
            CampaignModel.id == registration.campaign_id
        ).first()

        if campaign is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy chiến dịch"
            )

        if campaign.status != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail="Chỉ được xác minh giờ khi chiến dịch đã hoàn thành"
            )

        actual_hours = verified_attendance_hours(db, registration.id)

        # Kiểm tra yêu cầu cũ
        existing_claims = db.query(HourClaimModel).filter(
            HourClaimModel.registration_id == registration.id
        ).all()

        for claim in existing_claims:

            if claim.status == "VERIFIED":
                raise HTTPException(
                    status_code=409,
                    detail="Đăng ký này đã có yêu cầu được xác minh"
                )

            if claim.status == "PENDING":
                raise HTTPException(
                    status_code=409,
                    detail="Bạn đang có yêu cầu chờ Organizer xử lý"
                )

            if claim.appeal_status == "PENDING":
                raise HTTPException(
                    status_code=409,
                    detail="Bạn đang có khiếu nại chờ Admin xử lý"
                )

        claimed_hours = (
            data.claimed_hours
            if data.claimed_hours is not None
            else actual_hours
        )

        if claimed_hours <= 0:
            raise HTTPException(
                status_code=400,
                detail="Số giờ đề nghị phải lớn hơn 0"
            )

        claim = HourClaimModel(
            registration_id=registration.id,
            user_id=current_user.id,

            actual_hours=actual_hours,
            claimed_hours=claimed_hours,

            note=data.note.strip() if data.note else None,
            evidence_url=data.evidence_url,

            status="PENDING"
        )

        db.add(claim)
        notify_campaign_organizer(db, registration.campaign_id, "Có yêu cầu xác minh giờ",
                                  f'Yêu cầu xác minh giờ mới cho chiến dịch #{registration.campaign_id}.',
                                  "organizer-dashboard.html?tab=certificates")
        db.commit()
        db.refresh(claim)

        return claim

    except Exception:
        db.rollback()
        raise


# =====================================================
# 2. LẤY DANH SÁCH YÊU CẦU
# =====================================================

def get_hour_claims(
    db: Session,
    current_user,
    claim_status=None,
    appeal_status=None
):

    query = db.query(HourClaimModel)

    if current_user.role == "USER":

        query = query.filter(
            HourClaimModel.user_id == current_user.id
        )

    elif current_user.role == "ORGANIZER":

        query = query.join(
            RegistrationModel,
            HourClaimModel.registration_id == RegistrationModel.id
        ).join(
            CampaignModel,
            RegistrationModel.campaign_id == CampaignModel.id
        ).join(
            OrganizationModel,
            CampaignModel.organization_id == OrganizationModel.id
        ).filter(
            OrganizationModel.owner_id == current_user.id
        )

    elif current_user.role == "ADMIN":
        pass

    else:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền truy cập"
        )

    if claim_status:
        query = query.filter(
            HourClaimModel.status == claim_status
        )

    if appeal_status:
        query = query.filter(
            HourClaimModel.appeal_status == appeal_status
        )

    claims = (
        query.options(
            joinedload(HourClaimModel.user),
            joinedload(HourClaimModel.registration).joinedload(RegistrationModel.campaign),
        )
        .order_by(HourClaimModel.created_at.desc())
        .all()
    )
    for c in claims:
        setattr(c, "user_name", c.user.full_name if c.user else None)
        setattr(
            c,
            "campaign_title",
            c.registration.campaign.title if c.registration and c.registration.campaign else None,
        )
    return claims


# =====================================================
# 3. LẤY CHI TIẾT YÊU CẦU
# =====================================================

def get_hour_claim_detail(
    db: Session,
    claim_id: int,
    current_user
):

    claim = (
        db.query(HourClaimModel)
        .options(
            joinedload(HourClaimModel.user),
            joinedload(HourClaimModel.registration).joinedload(RegistrationModel.campaign),
        )
        .filter(HourClaimModel.id == claim_id)
        .first()
    )
    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy yêu cầu xác minh giờ đóng góp"
        )

    check_claim_access(
        db,
        claim,
        current_user
    )

    setattr(claim, "user_name", claim.user.full_name if claim.user else None)
    setattr(
        claim,
        "campaign_title",
        claim.registration.campaign.title if claim.registration and claim.registration.campaign else None,
    )
    return claim


# =====================================================
# 4. ORGANIZER: DUYỆT / TỪ CHỐI
# =====================================================

def review_hour_claim(
    db: Session,
    claim_id: int,
    data: HourClaimReview,
    current_user
):

    try:

        claim = db.query(HourClaimModel).filter(
            HourClaimModel.id == claim_id
        ).with_for_update().first()

        if claim is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu"
            )

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == claim.registration_id
        ).first()

        if registration is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy đăng ký"
            )

        check_organizer_campaign(
            db,
            registration.campaign_id,
            current_user
        )

        if claim.status != "PENDING":
            raise HTTPException(400, "Yêu cầu này đã được xử lý trước đó")

        campaign = db.query(CampaignModel).filter(
            CampaignModel.id == registration.campaign_id
        ).first()
        if campaign is None or campaign.status != "COMPLETED":
            raise HTTPException(400, "Chiến dịch chưa hoàn thành")

        # Một registration không thể có hai kết quả xác minh cùng tồn tại.
        other_verified = db.query(HourClaimModel.id).filter(
            HourClaimModel.registration_id == registration.id,
            HourClaimModel.id != claim.id,
            HourClaimModel.status == "VERIFIED",
        ).first()
        if other_verified:
            raise HTTPException(409, "Đã tồn tại yêu cầu xác minh giờ được duyệt")

        now = now_vietnam()

        if data.status == "VERIFIED":
            actual_hours = verified_attendance_hours(db, registration.id)
            approved_hours = (
                data.approved_hours
                if data.approved_hours is not None
                else min(claim.claimed_hours, actual_hours)
            )

            if approved_hours > actual_hours:
                raise HTTPException(422, "Giờ duyệt vượt quá giờ điểm danh hợp lệ")

            if approved_hours <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số giờ được công nhận phải lớn hơn 0"
                )

            claim.status = "VERIFIED"
            claim.actual_hours = actual_hours
            claim.approved_hours = approved_hours
            claim.verified_by = current_user.id
            claim.verified_at = now
            claim.rejection_reason = None

        elif data.status == "REJECTED":

            if (
                not data.rejection_reason
                or not data.rejection_reason.strip()
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Bắt buộc nhập lý do từ chối"
                )

            claim.status = "REJECTED"
            claim.approved_hours = None
            claim.verified_by = current_user.id
            claim.verified_at = now

            claim.rejection_reason = (
                data.rejection_reason.strip()
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Trạng thái xử lý không hợp lệ"
            )

        claim.updated_at = now
        create_notification(db, claim.user_id, "Yêu cầu xác minh giờ đã xử lý",
                            f'Yêu cầu #{claim.id}: {claim.status}.',
                            "user-dashboard.html?tab=certificates")

        # Tự động cấp chứng nhận trong cùng transaction sau khi xác minh thành công
        if claim.status == "VERIFIED":
            db.flush()
            issue_certificate(
                db=db,
                payload=IssueCertificate(
                    campaign_id=registration.campaign_id,
                    user_id=claim.user_id,
                    total_hours=claim.approved_hours,
                ),
                owner_id=current_user.id,
                commit=False,
            )

        db.commit()
        db.refresh(claim)
        return claim

    except Exception:
        db.rollback()
        raise


# =====================================================
# 5. TNV: GỬI KHIẾU NẠI
# =====================================================

def create_hour_claim_appeal(
    db: Session,
    claim_id: int,
    data: HourClaimAppealCreate,
    current_user
):

    try:

        claim = db.query(HourClaimModel).filter(
            HourClaimModel.id == claim_id
        ).with_for_update().first()

        if claim is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu"
            )

        if claim.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền khiếu nại yêu cầu này"
            )

        is_rejected = claim.status == "REJECTED"
        is_under_approved = (
            claim.status == "VERIFIED"
            and claim.approved_hours is not None
            and claim.approved_hours < claim.claimed_hours
        )
        if not (is_rejected or is_under_approved):
            raise HTTPException(
                status_code=400,
                detail="Chỉ được khiếu nại yêu cầu bị từ chối hoặc được duyệt ít hơn số giờ đề nghị"
            )

        if claim.appeal_status is not None:
            raise HTTPException(
                status_code=409,
                detail="Yêu cầu này đã được gửi khiếu nại"
            )

        if not data.appeal_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Vui lòng nhập nội dung khiếu nại"
            )

        claim.appeal_reason = data.appeal_reason.strip()

        claim.appeal_evidence_url = (
            data.appeal_evidence_url
        )

        claim.appeal_status = "PENDING"
        claim.updated_at = now_vietnam()
        notify_active_admins(db, "Có khiếu nại giờ đóng góp",
                             f'Có khiếu nại mới cho yêu cầu giờ #{claim.id}.',
                             "admin-dashboard.html?tab=appeals")

        db.commit()
        db.refresh(claim)

        return claim

    except Exception:
        db.rollback()
        raise


# =====================================================
# 6. ADMIN: XỬ LÝ KHIẾU NẠI
# =====================================================

def review_hour_claim_appeal(
    db: Session,
    claim_id: int,
    data: HourClaimAppealReview,
    current_user
):

    try:

        claim = db.query(HourClaimModel).filter(
            HourClaimModel.id == claim_id
        ).with_for_update().first()

        if claim is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu"
            )
        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == claim.registration_id).first()

        if registration is None:
            raise HTTPException(
            status_code=404,
            detail="Không tìm thấy thông tin đăng ký"
    )

        if claim.appeal_status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Khiếu nại không tồn tại hoặc đã được xử lý"
            )

        now = now_vietnam()

        if data.appeal_status == "ACCEPTED":
            duplicate = db.query(HourClaimModel.id).filter(
                HourClaimModel.registration_id == claim.registration_id,
                HourClaimModel.id != claim.id,
                HourClaimModel.status == "VERIFIED",
            ).first()
            if duplicate:
                raise HTTPException(409, "Đã tồn tại yêu cầu được xác minh cho đăng ký này")
            campaign = db.query(CampaignModel).filter(
                CampaignModel.id == registration.campaign_id
            ).first()
            if campaign is None:
                raise HTTPException(404, "Không tìm thấy chiến dịch")
            campaign_seconds = max(0.0, (campaign.end_time - campaign.start_time).total_seconds())
            campaign_max_hours = (
                Decimal(str(campaign_seconds)) / Decimal("3600")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            actual_hours = verified_attendance_hours(db, claim.registration_id)
            max_allowed_hours = min(actual_hours, campaign_max_hours)
            approved_hours = (
                data.approved_hours
                if data.approved_hours is not None
                else min(claim.claimed_hours, max_allowed_hours)
            )
            if approved_hours > actual_hours:
                raise HTTPException(
                    422,
                    "Giờ duyệt vượt quá giờ điểm danh hợp lệ; nếu thiếu điểm danh hãy xử lý khiếu nại điểm danh trước",
                )
            if approved_hours > campaign_max_hours:
                raise HTTPException(422, "Giờ duyệt vượt quá thời lượng tối đa của chiến dịch")

            if approved_hours <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số giờ được công nhận phải lớn hơn 0"
                )

            claim.appeal_status = "ACCEPTED"

            # Khiếu nại được chấp nhận:
            # Yêu cầu giờ đóng góp chuyển sang VERIFIED
            claim.status = "VERIFIED"
            claim.actual_hours = actual_hours
            claim.approved_hours = approved_hours

            claim.verified_at = now
            claim.rejection_reason = None

        elif data.appeal_status == "REJECTED":

            claim.appeal_status = "REJECTED"

            # Chỉ chuyển về REJECTED nếu trước đó claim chưa được VERIFIED
            if claim.status != "VERIFIED":
                claim.status = "REJECTED"

        else:
            raise HTTPException(
                status_code=400,
                detail="Trạng thái khiếu nại không hợp lệ"
            )

        claim.admin_id = current_user.id

        claim.admin_note = (
            data.admin_note.strip()
            if data.admin_note
            else None
        )

        claim.resolved_at = now
        claim.updated_at = now
        create_notification(db, claim.user_id, "Khiếu nại giờ đã được xử lý",
                            f'Khiếu nại yêu cầu #{claim.id}: {claim.appeal_status}.',
                            "user-dashboard.html?tab=certificates")

        if claim.appeal_status == "ACCEPTED" and claim.status == "VERIFIED":
            existing_cert = (
                db.query(CertificateModel)
                .filter(
                    CertificateModel.campaign_id == registration.campaign_id,
                    CertificateModel.user_id == claim.user_id,
                )
                .with_for_update()
                .first()
            )
            if existing_cert is not None:
                if existing_cert.status == "REVOKED":
                    raise HTTPException(
                        status_code=409,
                        detail="Chứng chỉ của chiến dịch này đã bị thu hồi; không thể tự động cập nhật.",
                    )
                existing_cert.total_hours = claim.approved_hours
                create_notification(
                    db=db,
                    user_id=claim.user_id,
                    title="Chứng nhận đã được cập nhật giờ",
                    content=f'Chứng nhận {existing_cert.certificate_code} đã được cập nhật thành {claim.approved_hours} giờ.',
                    link=f"user-dashboard.html?tab=certificates&certificate={existing_cert.certificate_code}",
                )
            else:
                org_owner_id = (
                    db.query(OrganizationModel.owner_id)
                    .join(CampaignModel, CampaignModel.organization_id == OrganizationModel.id)
                    .filter(CampaignModel.id == registration.campaign_id)
                    .scalar()
                )
                if org_owner_id is not None:
                    db.flush()
                    issue_certificate(
                        db=db,
                        payload=IssueCertificate(
                            campaign_id=registration.campaign_id,
                            user_id=claim.user_id,
                            total_hours=claim.approved_hours,
                        ),
                        owner_id=org_owner_id,
                        commit=False,
                    )

        db.commit()
        db.refresh(claim)
        return claim

    except Exception:
        db.rollback()
        raise 