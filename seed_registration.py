"""Script seed dữ liệu mẫu cho registrations (đủ các trạng thái).

Chạy: python seed_registration.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel


def _upsert_registration(
    db: Session,
    user: UserModel,
    campaign: CampaignModel,
    status: str,
    message: str,
    rejection_reason: str | None = None,
) -> bool:
    existing = db.query(RegistrationModel).filter(
        RegistrationModel.user_id == user.id,
        RegistrationModel.campaign_id == campaign.id,
    ).first()
    if existing:
        return False

    now = datetime.now().replace(microsecond=0)
    created_at = (
        (campaign.start_time - timedelta(days=3)).replace(second=0, microsecond=0)
        if campaign.start_time
        else now - timedelta(days=3)
    )

    reg = RegistrationModel(
        user_id=user.id,
        campaign_id=campaign.id,
        status=status,
        message=message,
        rejection_reason=rejection_reason,
        created_at=created_at,
    )
    db.add(reg)
    return True


def seed_registrations(db: Session):
    users_by_email = {
        u.email: u
        for u in db.query(UserModel).filter(UserModel.role == "USER").all()
    }
    if not users_by_email:
        print("[!] Không tìm thấy tài khoản USER nào. Vui lòng chạy `python seed_user.py` trước!")
        return

    campaigns = db.query(CampaignModel).order_by(CampaignModel.id).all()
    if not campaigns:
        print("[!] Không tìm thấy Campaign nào. Vui lòng chạy `python seed_campaign.py` trước!")
        return

    by_status: dict[str, list[CampaignModel]] = {}
    for c in campaigns:
        by_status.setdefault(c.status, []).append(c)

    open_campaigns = by_status.get("OPEN", [])
    completed_campaigns = by_status.get("COMPLETED", [])
    closed_campaigns = by_status.get("CLOSED", [])

    created = 0
    skipped = 0

    def add_reg(email: str, campaign: CampaignModel, status: str, msg: str, reason: str | None = None):
        nonlocal created, skipped
        user = users_by_email.get(email)
        if not user:
            skipped += 1
            return
        if _upsert_registration(db, user, campaign, status, msg, reason):
            created += 1
            print(f"  [+] {email} -> '{campaign.title}' ({status})")
        else:
            skipped += 1

    # 1. Chiến dịch COMPLETED: dùng cho Attendance, HourClaim, Certificate
    for c in completed_campaigns:
        add_reg("user@gmail.com", c, "APPROVED", f"Đăng ký tham gia {c.title}")
        add_reg("user2@gmail.com", c, "APPROVED", f"Rất mong được đóng góp cho {c.title}")
        add_reg("user3@gmail.com", c, "APPROVED", f"Tôi có kinh nghiệm hậu cần cho {c.title}")
        add_reg("user4@gmail.com", c, "REJECTED", "Đăng ký muộn", "Đã đủ số lượng tình nguyện viên cho đợt này.")

    # 2. Chiến dịch CLOSED: đã đóng đăng ký trước khi diễn ra
    for c in closed_campaigns:
        add_reg("user@gmail.com", c, "APPROVED", f"Đăng ký tham gia {c.title}")
        add_reg("user2@gmail.com", c, "APPROVED", f"Tham gia hỗ trợ {c.title}")
        add_reg("user5@gmail.com", c, "CANCELLED", "Bận lịch thi đột xuất nên xin hủy")

    # 3. Chiến dịch OPEN (bao gồm chiến dịch LIVE26 hôm nay và các chiến dịch sắp tới)
    if open_campaigns:
        today_campaign = next((c for c in open_campaigns if c.attendance_code), open_campaigns[0])
        add_reg("user@gmail.com", today_campaign, "APPROVED", "Đăng ký tham gia chiến dịch hôm nay")
        add_reg("user2@gmail.com", today_campaign, "APPROVED", "Sẵn sàng tham gia đúng giờ")
        add_reg("user3@gmail.com", today_campaign, "PENDING", "Mong ban tổ chức duyệt đơn giúp em")

        for idx, c in enumerate(open_campaigns[1:], start=1):
            add_reg("user@gmail.com", c, "PENDING" if idx % 2 == 1 else "APPROVED", f"Đăng ký tham gia {c.title}")
            add_reg("user2@gmail.com", c, "APPROVED", f"Tham gia cùng đội ngũ {c.title}")
            add_reg("user3@gmail.com", c, "WAITLISTED", f"Xin vào danh sách chờ {c.title}")
            add_reg("user4@gmail.com", c, "WAITLISTED", f"Đăng ký chờ slot {c.title}")
            add_reg("user5@gmail.com", c, "REJECTED", "Đăng ký", "Chưa phù hợp yêu cầu chuyên môn.")

    db.commit()
    print("\n========== SEED REGISTRATIONS ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_registrations(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
