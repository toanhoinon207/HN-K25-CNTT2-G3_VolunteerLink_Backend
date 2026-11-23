"""Script seed dữ liệu mẫu cho hour_claims (đủ trạng thái PENDING, VERIFIED, REJECTED và appeal_*).

Chạy: python seed_hour_claim.py
"""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.hourclaims import HourClaimModel


def seed_hour_claims(db: Session):
    organizer = db.query(UserModel).filter(UserModel.email == "organizer@gmail.com").first()
    if not organizer:
        organizer = db.query(UserModel).filter(UserModel.role == "ORGANIZER").first()
    admin = db.query(UserModel).filter(UserModel.role == "ADMIN").first()

    # Chỉ tạo HourClaim cho đơn APPROVED trên chiến dịch COMPLETED có điểm danh PRESENT
    eligible_rows = (
        db.query(RegistrationModel, AttendanceModel, CampaignModel)
        .join(AttendanceModel, AttendanceModel.registration_id == RegistrationModel.id)
        .join(CampaignModel, RegistrationModel.campaign_id == CampaignModel.id)
        .filter(
            RegistrationModel.status == "APPROVED",
            CampaignModel.status == "COMPLETED",
            AttendanceModel.status == "PRESENT",
        )
        .order_by(RegistrationModel.id)
        .all()
    )

    if not eligible_rows:
        print("[!] Không có dữ liệu đủ điều kiện (APPROVED + COMPLETED + PRESENT). Chạy `seed_attendance.py` trước.")
        return

    now = datetime.now().replace(microsecond=0)
    created = 0
    skipped = 0

    # Các kịch bản mẫu xoay vòng để phủ hết các trạng thái HourClaim & Appeal
    scenarios = [
        "VERIFIED",
        "PENDING",
        "REJECTED_NO_APPEAL",
        "REJECTED_APPEAL_PENDING",
        "REJECTED_APPEAL_ACCEPTED",
        "REJECTED_APPEAL_REJECTED",
    ]

    for idx, (reg, att, campaign) in enumerate(eligible_rows):
        existing = db.query(HourClaimModel).filter(
            HourClaimModel.registration_id == reg.id
        ).first()
        if existing:
            skipped += 1
            continue

        actual_hours = Decimal(str(round(att.total_minutes / 60.0, 2)))
        scenario = scenarios[idx % len(scenarios)]

        claim = HourClaimModel(
            registration_id=reg.id,
            user_id=reg.user_id,
            actual_hours=actual_hours,
            claimed_hours=actual_hours,
            evidence_url=f"https://volunteerlink.vn/evidences/claim_{reg.id}.jpg",
            note=f"Đề nghị xác nhận giờ tham gia chiến dịch {campaign.title}",
        )

        if scenario == "VERIFIED":
            claim.status = "VERIFIED"
            claim.approved_hours = actual_hours
            claim.verified_by = organizer.id if organizer else None
            claim.verified_at = now - timedelta(days=2)

        elif scenario == "PENDING":
            claim.status = "PENDING"
            claim.claimed_hours = actual_hours + Decimal("1.00")
            claim.note = "Xin cộng thêm 1 giờ hỗ trợ dọn dẹp sau sự kiện."

        elif scenario == "REJECTED_NO_APPEAL":
            claim.status = "REJECTED"
            claim.claimed_hours = actual_hours + Decimal("2.00")
            claim.verified_by = organizer.id if organizer else None
            claim.verified_at = now - timedelta(days=3)
            claim.rejection_reason = "Số giờ yêu cầu vượt quá thời gian điểm danh thực tế."

        elif scenario == "REJECTED_APPEAL_PENDING":
            claim.status = "REJECTED"
            claim.claimed_hours = actual_hours + Decimal("1.50")
            claim.verified_by = organizer.id if organizer else None
            claim.verified_at = now - timedelta(days=2)
            claim.rejection_reason = "Thiếu minh chứng làm thêm giờ."
            claim.appeal_reason = "Em có ở lại hỗ trợ kiểm kê vật tư, đính kèm ảnh chụp biên bản."
            claim.appeal_evidence_url = f"https://volunteerlink.vn/evidences/appeal_{reg.id}.jpg"
            claim.appeal_status = "PENDING"

        elif scenario == "REJECTED_APPEAL_ACCEPTED":
            claim.status = "VERIFIED"
            claim.claimed_hours = actual_hours
            claim.verified_by = organizer.id if organizer else None
            claim.verified_at = now - timedelta(days=5)
            claim.rejection_reason = None
            claim.appeal_reason = "Đính kèm xác nhận của trưởng nhóm hậu cần."
            claim.appeal_evidence_url = f"https://volunteerlink.vn/evidences/appeal_{reg.id}.jpg"
            claim.appeal_status = "ACCEPTED"
            claim.admin_id = admin.id if admin else None
            claim.admin_note = "Đã đối chiếu biên bản, chấp nhận đủ giờ điểm danh thực tế."
            claim.approved_hours = actual_hours
            claim.resolved_at = now - timedelta(days=1)

        elif scenario == "REJECTED_APPEAL_REJECTED":
            claim.status = "REJECTED"
            claim.claimed_hours = actual_hours + Decimal("3.00")
            claim.verified_by = organizer.id if organizer else None
            claim.verified_at = now - timedelta(days=6)
            claim.rejection_reason = "Minh chứng không hợp lệ."
            claim.appeal_reason = "Xin xem xét lại giờ tham gia."
            claim.appeal_evidence_url = f"https://volunteerlink.vn/evidences/appeal_{reg.id}.jpg"
            claim.appeal_status = "REJECTED"
            claim.admin_id = admin.id if admin else None
            claim.admin_note = "Ảnh minh chứng không khớp thời gian chiến dịch."
            claim.approved_hours = None
            claim.resolved_at = now - timedelta(days=1)

        db.add(claim)
        created += 1
        print(f"  [+] HourClaim reg_id={reg.id} | scenario={scenario} | status={claim.status} | appeal={claim.appeal_status}")

    db.commit()
    print("\n========== SEED HOUR CLAIMS ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_hour_claims(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
