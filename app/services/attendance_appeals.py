"""Khiếu nại điểm danh độc lập với khiếu nại xác minh giờ.

Không tự công nhận giờ: Organizer xác nhận các mốc thời gian rồi TNV tạo hour claim.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.attendance_appeals import AttendanceAppealModel
from app.models.attendances import AttendanceModel
from app.models.registration import RegistrationModel
from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel
from app.models.hourclaims import HourClaimModel


def normalize_time(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    return value


def find_registration(db, registration_id):
    reg = db.query(RegistrationModel).filter(RegistrationModel.id == registration_id).first()
    if reg is None:
        raise HTTPException(404, "Không tìm thấy đơn đăng ký")
    return reg


def ensure_completed(db, campaign_id):
    camp = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if camp is None:
        raise HTTPException(404, "Không tìm thấy chiến dịch")
    if camp.status != "COMPLETED":
        raise HTTPException(400, "Chỉ khiếu nại điểm danh sau khi chiến dịch hoàn thành")
    return camp


def create_appeal(db: Session, data, user):
    reg = find_registration(db, data.registration_id)
    if reg.user_id != user.id or reg.status != "APPROVED":
        raise HTTPException(403, "Chỉ người được duyệt tham gia mới có quyền khiếu nại")
    ensure_completed(db, reg.campaign_id)
    attendance = db.query(AttendanceModel).filter(AttendanceModel.registration_id == reg.id).first()
    if attendance and attendance.status == "PRESENT" and attendance.check_in_at and attendance.check_out_at:
        raise HTTPException(409, "Điểm danh đã đầy đủ; sử dụng khiếu nại giờ nếu cần điều chỉnh số giờ")
    if db.query(AttendanceAppealModel).filter(AttendanceAppealModel.registration_id == reg.id, AttendanceAppealModel.status == "PENDING").first():
        raise HTTPException(409, "Đã có khiếu nại điểm danh đang chờ xử lý")
    appeal = AttendanceAppealModel(
        registration_id=reg.id, user_id=user.id,
        reason=data.reason.strip(), evidence_url=data.evidence_url or None,
    )
    try:
        db.add(appeal)
        db.commit()
        db.refresh(appeal)
        return appeal
    except Exception:
        db.rollback()
        raise


def my_appeals(db: Session, user):
    return db.query(AttendanceAppealModel).filter(AttendanceAppealModel.user_id == user.id).order_by(AttendanceAppealModel.id.desc()).all()


def organizer_appeals(db: Session, user, campaign_id=None):
    q = db.query(AttendanceAppealModel).join(
        RegistrationModel, RegistrationModel.id == AttendanceAppealModel.registration_id
    ).join(CampaignModel, CampaignModel.id == RegistrationModel.campaign_id).join(
        OrganizationModel, OrganizationModel.id == CampaignModel.organization_id
    ).filter(OrganizationModel.owner_id == user.id)
    if campaign_id is not None:
        q = q.filter(CampaignModel.id == campaign_id)
    return q.order_by(AttendanceAppealModel.id.desc()).all()


def review_appeal(db: Session, appeal_id: int, data, user):
    try:
        appeal = db.query(AttendanceAppealModel).filter(AttendanceAppealModel.id == appeal_id).with_for_update().first()
        if appeal is None:
            raise HTTPException(404, "Không tìm thấy khiếu nại")
        reg = find_registration(db, appeal.registration_id)
        camp = ensure_completed(db, reg.campaign_id)
        owner = db.query(OrganizationModel).filter(
            OrganizationModel.id == camp.organization_id, OrganizationModel.owner_id == user.id
        ).first()
        if owner is None:
            raise HTTPException(403, "Không được xử lý khiếu nại của tổ chức khác")
        if appeal.status != "PENDING":
            raise HTTPException(409, "Khiếu nại đã xử lý")
        if data.decision == "ACCEPTED":
            # Không sửa điểm danh đã được dùng để xác minh giờ, tránh bất nhất giữa 2 bảng.
            verified = db.query(HourClaimModel).filter(
                HourClaimModel.registration_id == reg.id, HourClaimModel.status == "VERIFIED"
            ).first()
            if verified:
                raise HTTPException(409, "Đã xác minh giờ; phải xử lý điều chỉnh giờ bằng quy trình riêng")
            attendance = db.query(AttendanceModel).filter(
                AttendanceModel.registration_id == reg.id
            ).with_for_update().first()
            start = normalize_time(data.check_in_at) or (normalize_time(attendance.check_in_at) if attendance else None)
            end = normalize_time(data.check_out_at) or (normalize_time(attendance.check_out_at) if attendance else None)
            if start is None or end is None:
                raise HTTPException(422, "Cần cung cấp đủ giờ CHECK-IN/CHECK-OUT còn thiếu để chấp nhận")
            if not (camp.start_time <= start < end <= camp.end_time):
                raise HTTPException(422, "Thời gian phải nằm trong khoảng diễn ra chiến dịch và CHECK-OUT sau CHECK-IN")
            # Không cho thay đổi mốc đã ghi nhận qua mã hợp lệ bằng khiếu nại thiếu điểm danh.
            if attendance and ((attendance.check_in_at and start != attendance.check_in_at) or
                               (attendance.check_out_at and end != attendance.check_out_at)):
                raise HTTPException(409, "Không thay đổi mốc điểm danh đã ghi nhận; sử dụng quy trình điều chỉnh riêng")
            if attendance is None:
                attendance = AttendanceModel(registration_id=reg.id, recorded_by=user.id)
                db.add(attendance)
            attendance.status = "PRESENT"
            attendance.check_in_at = start
            attendance.check_out_at = end
            attendance.total_minutes = max(1, int(round((end - start).total_seconds() / 60)))
            attendance.updated_by = user.id
            attendance.updated_at = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
            attendance.edit_reason = f"Duyệt khiếu nại điểm danh #{appeal.id}: {data.review_note.strip()}"
        appeal.status = data.decision
        appeal.organizer_id = user.id
        appeal.review_note = data.review_note.strip()
        appeal.reviewed_at = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
        db.commit()
        db.refresh(appeal)
        return appeal
    except Exception:
        db.rollback()
        raise
