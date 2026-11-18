"""Script seed dữ liệu mẫu cho registrations và attendances.

Chạy: python seed_attendance.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel


def seed_attendance_data(db: Session):
    # 1. Tìm hoặc kiểm tra User (Tình nguyện viên) và Organizer
    volunteer = db.query(UserModel).filter(UserModel.email == "user@gmail.com").first()
    if not volunteer:
        volunteer = db.query(UserModel).filter(UserModel.role == "USER").first()

    organizer = db.query(UserModel).filter(UserModel.email == "organizer@gmail.com").first()
    if not organizer:
        organizer = db.query(UserModel).filter(UserModel.role == "ORGANIZER").first()

    if not volunteer:
        print("[!] Không tìm thấy tài khoản USER nào. Vui lòng chạy `python seed_user.py` trước!")
        return

    # 2. Tìm danh sách Campaign đã có trong hệ thống
    campaigns = db.query(CampaignModel).all()
    if not campaigns:
        print("[!] Không tìm thấy Campaign nào trong database. Vui lòng chạy `python seed_campaign.py` trước!")
        return

    print(f"[*] Tìm thấy Tình nguyện viên: {volunteer.full_name} ({volunteer.email})")
    print(f"[*] Tìm thấy {len(campaigns)} chiến dịch trong hệ thống.")

    created_reg_count = 0
    created_att_count = 0
    now = datetime.now().replace(microsecond=0)

    # Ưu tiên các campaign đã kết thúc hoặc đang diễn ra để giờ điểm danh thực tế và hợp lý nhất
    for campaign in campaigns:
        # Bỏ qua nếu đã duyệt đủ 5 campaign mẫu
        if created_att_count >= 5:
            break

        # Kiểm tra xem volunteer đã đăng ký campaign này chưa
        registration = db.query(RegistrationModel).filter(
            RegistrationModel.user_id == volunteer.id,
            RegistrationModel.campaign_id == campaign.id
        ).first()

        # Tính thời gian đăng ký: trước khi chiến dịch bắt đầu
        if campaign.start_time:
            reg_created_at = (campaign.start_time - timedelta(days=3)).replace(second=0, microsecond=0)
        else:
            reg_created_at = (now - timedelta(days=5)).replace(second=0, microsecond=0)

        if not registration:
            registration = RegistrationModel(
                user_id=volunteer.id,
                campaign_id=campaign.id,
                status="APPROVED",
                message=f"Đăng ký tham gia chiến dịch {campaign.title}",
                created_at=reg_created_at
            )
            db.add(registration)
            db.flush()  # Sinh registration.id
            created_reg_count += 1
            print(f"  [+] Đã tạo đơn đăng ký (APPROVED) cho chiến dịch: {campaign.title}")

        # Kiểm tra xem chiến dịch có đang diễn ra hôm nay không
        is_today_campaign = bool(campaign.start_time and campaign.end_time and (campaign.start_time <= now <= campaign.end_time))
        if is_today_campaign:
            if not campaign.attendance_code:
                campaign.attendance_code = "LIVE26"
                campaign.attendance_code_expires_at = now + timedelta(days=1)
            print(f"  [★] Chiến dịch '{campaign.title}' đang diễn ra HÔM NAY đã có đơn APPROVED & mã điểm danh: {campaign.attendance_code} (Chưa check-in để bạn test bấm nút trực tiếp trên Web)!")
            continue

        # Kiểm tra xem đã có bản ghi điểm danh cho registration này chưa
        existing_attendance = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == registration.id
        ).first()

        if not existing_attendance:
            # TÍNH TOÁN THỜI GIAN CHECK-IN VÀ CHECK-OUT CHUẨN XÁC:
            # Check-in và Check-out phải khớp chặt chẽ với thời gian bắt đầu và kết thúc của chính Campaign đó
            if campaign.start_time and campaign.end_time:
                check_in_time = campaign.start_time.replace(second=0, microsecond=0)
                check_out_time = campaign.end_time.replace(second=0, microsecond=0)
                
                # Nếu campaign ở tương lai, đưa mốc giờ điểm danh về quá khứ gần nhất tương ứng với thời lượng ca
                if check_out_time > now:
                    duration_hours = max(1.0, (check_out_time - check_in_time).total_seconds() / 3600)
                    check_in_time = (now - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                    check_out_time = check_in_time + timedelta(hours=duration_hours)
            else:
                # Nếu chiến dịch không có start_time, gán mặc định ca sáng 4 tiếng (08:00 -> 12:00)
                check_in_time = (now - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
                check_out_time = check_in_time + timedelta(hours=4)

            # Tính tổng số phút chuẩn xác: làm tròn phút
            total_seconds = (check_out_time - check_in_time).total_seconds()
            total_mins = max(0, int(round(total_seconds / 60)))

            attendance = AttendanceModel(
                registration_id=registration.id,
                check_in_at=check_in_time,
                check_out_at=check_out_time,
                total_minutes=total_mins,
                recorded_by=organizer.id if organizer else None,
                status="PRESENT",
                edit_reason=None
            )
            db.add(attendance)
            created_att_count += 1
            print(f"  [+] Đã tạo điểm danh: {check_in_time.strftime('%Y-%m-%d %H:%M')} -> {check_out_time.strftime('%H:%M')} ({total_mins} phút) | {campaign.title}")
        else:
            print(f"  [-] Chiến dịch {campaign.title} đã có điểm danh id={existing_attendance.id}")

    db.commit()
    print("\n" + "=" * 55)
    print("Hoàn tất seed dữ liệu điểm danh:")
    print(f"- Đơn đăng ký mới (Registrations): {created_reg_count}")
    print(f"- Lượt điểm danh mới (Attendances): {created_att_count}")
    print("=" * 55)


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
