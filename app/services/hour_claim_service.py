from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.hourclaims import HourClaimModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel
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

        attendance = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == registration.id
        ).first()

        if attendance is None:
            raise HTTPException(
                status_code=400,
                detail="Bạn chưa có dữ liệu điểm danh"
            )

        if attendance.status != "PRESENT":
            raise HTTPException(
                status_code=400,
                detail="Bạn không có trạng thái điểm danh hợp lệ"
            )

        if (
            attendance.check_in_at is None
            or attendance.check_out_at is None
            or attendance.total_minutes <= 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Dữ liệu điểm danh chưa đầy đủ"
            )

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

        # Tính giờ thực tế
        actual_hours = (
            Decimal(attendance.total_minutes) / Decimal("60")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
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

    return query.order_by(
        HourClaimModel.created_at.desc()
    ).all()


# =====================================================
# 3. LẤY CHI TIẾT YÊU CẦU
# =====================================================

def get_hour_claim_detail(
    db: Session,
    claim_id: int,
    current_user
):

    claim = get_claim(db, claim_id)

    check_claim_access(
        db,
        claim,
        current_user
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
            raise HTTPException(
                status_code=400,
                detail="Yêu cầu này đã được xử lý trước đó"
            )

        now = now_vietnam()

        if data.status == "VERIFIED":

            approved_hours = (
                data.approved_hours
                if data.approved_hours is not None
                else claim.claimed_hours
            )

            if approved_hours <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số giờ được công nhận phải lớn hơn 0"
                )

            claim.status = "VERIFIED"
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

        db.commit()
        db.refresh(claim)

       # Tự động cấp chứng nhận sau khi xác minh thành công
        if claim.status == "VERIFIED":

            issue_certificate(
                db=db,
                user_id=claim.user_id,
                campaign_id=registration.campaign_id,
                verified_hours=claim.approved_hours
    )

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

        if claim.status != "REJECTED":
            raise HTTPException(
                status_code=400,
                detail="Chỉ được khiếu nại yêu cầu đã bị từ chối"
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

            approved_hours = (
                data.approved_hours
                if data.approved_hours is not None
                else claim.claimed_hours
            )

            if approved_hours <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Số giờ được công nhận phải lớn hơn 0"
                )

            claim.appeal_status = "ACCEPTED"

            # Khiếu nại được chấp nhận:
            # Yêu cầu giờ đóng góp chuyển sang VERIFIED
            claim.status = "VERIFIED"
            claim.approved_hours = approved_hours

            claim.verified_at = now
            claim.rejection_reason = None

        elif data.appeal_status == "REJECTED":

            claim.appeal_status = "REJECTED"

            # Giữ nguyên trạng thái REJECTED của yêu cầu
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

        db.commit()
        db.refresh(claim)
        if claim.appeal_status == "ACCEPTED" and claim.status == "VERIFIED":

            issue_certificate(
                db=db,
                user_id=claim.user_id,
                campaign_id=registration.campaign_id,
                verified_hours=claim.approved_hours
            )
        return claim

    except Exception:
        db.rollback()
        raise 