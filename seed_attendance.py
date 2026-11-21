"""Script seed dữ liệu mẫu cho attendances (dựa trên các registration APPROVED).

Chạy: python seed_attendance.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel


def seed_attendance_data(db: Session):
    organizer = db.query(UserModel).filter(UserModel.email == "organizer@gmail.com").first()
    if not organizer:
        organizer = db.query(UserModel).filter(UserModel.role == "ORGANIZER").first()

    approved_regs = (
        db.query(RegistrationModel)
        .join(CampaignModel, RegistrationModel.campaign_id == CampaignModel.id)
        .filter(
            RegistrationModel.status == "APPROVED",
            CampaignModel.status.in_(["COMPLETED", "CLOSED", "OPEN"]),
        )
        .order_by(RegistrationModel.id)
        .all()
    )

    if not approved_regs:
        print("[!] Chưa có đơn APPROVED nào. Vui lòng chạy `python seed_registration.py` trước!")
        return

    now = datetime.now().replace(microsecond=0)
    created_att_count = 0
    skipped_count = 0

    for idx, reg in enumerate(approved_regs):
        campaign = reg.campaign
        user = reg.user

        # Giữ chiến dịch đang diễn ra hôm nay (OPEN + có attendance_code) chưa check-in cho user@gmail.com để test trên Web
        is_today_campaign = bool(
            campaign.start_time and campaign.end_time and (campaign.start_time <= now <= campaign.end_time)
        )
        if is_today_campaign and campaign.status == "OPEN":
            if not campaign.attendance_code:
                campaign.attendance_code = "LIVE26"
                campaign.attendance_code_expires_at = now + timedelta(days=1)
            if user and user.email == "user@gmail.com":
                print(
                    f"  [★] Giữ '{campaign.title}' ({campaign.attendance_code}) chưa check-in "
                    f"cho {user.email} để test trực tiếp trên Web."
                )
                skipped_count += 1
                continue

        # Chỉ seed điểm danh sẵn cho chiến dịch đã kết thúc/đóng (hoặc các đơn không phải hôm nay của user phụ)
        if campaign.status == "OPEN" and not is_today_campaign:
            skipped_count += 1
            continue

        existing_attendance = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == reg.id
        ).first()
        if existing_attendance:
            skipped_count += 1
            continue

        # Tạo 1 mẫu ABSENT cho user3 ở lượt đầu tiên để test đủ 2 trạng thái PRESENT / ABSENT
        is_absent = bool(user and user.email == "user3@gmail.com" and idx % 2 == 0)

        if is_absent:
            attendance = AttendanceModel(
                registration_id=reg.id,
                check_in_at=None,
                check_out_at=None,
                total_minutes=0,
                recorded_by=organizer.id if organizer else None,
                status="ABSENT",
                edit_reason="Vắng mặt không lý do",
            )
        else:
            if campaign.start_time and campaign.end_time:
                check_in_time = campaign.start_time.replace(second=0, microsecond=0)
                check_out_time = campaign.end_time.replace(second=0, microsecond=0)
                if check_out_time > now:
                    duration_hours = max(1.0, (check_out_time - check_in_time).total_seconds() / 3600)
                    check_in_time = (now - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                    check_out_time = check_in_time + timedelta(hours=duration_hours)
            else:
                check_in_time = (now - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                check_out_time = check_in_time + timedelta(hours=4)

            total_mins = max(0, int(round((check_out_time - check_in_time).total_seconds() / 60)))
            attendance = AttendanceModel(
                registration_id=reg.id,
                check_in_at=check_in_time,
                check_out_at=check_out_time,
                total_minutes=total_mins,
                recorded_by=organizer.id if organizer else None,
                status="PRESENT",
                edit_reason=None,
            )

        db.add(attendance)
        created_att_count += 1
        print(
            f"  [+] Attendance ({attendance.status}) | {user.email if user else reg.user_id} "
            f"| {campaign.title} ({attendance.total_minutes} phút)"
        )

    db.commit()
    print("\n========== SEED ATTENDANCES ==========")
    print(f"Đã tạo: {created_att_count} | Bỏ qua: {skipped_count}")


def main():
    db = SessionLocal()
    try:
        seed_attendance_data(db)
    except Exception as e:
        db.rollback()
        print(f"[X] Lỗi khi seed dữ liệu điểm danh: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
