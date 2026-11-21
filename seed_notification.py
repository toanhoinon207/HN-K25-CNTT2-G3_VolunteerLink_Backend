"""Script seed dữ liệu mẫu cho notifications.

Chạy: python seed_notification.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.notifications import NotificationModel


def seed_notifications(db: Session):
    now = datetime.now().replace(microsecond=0)

    notifications_plan = [
        {
            "email": "user@gmail.com",
            "items": [
                {
                    "title": "Đơn đăng ký đã được duyệt",
                    "content": "Đơn đăng ký chiến dịch Dọn vệ sinh Hồ Gươm của bạn đã được ban tổ chức phê duyệt.",
                    "link": "/pages/my-registrations.html",
                    "is_read": False,
                    "hours_ago": 3,
                },
                {
                    "title": "Chứng nhận tình nguyện mới",
                    "content": "Bạn đã nhận được chứng nhận hoàn thành chiến dịch Ngày hội tái chế rác thải.",
                    "link": "/pages/certificates.html",
                    "is_read": True,
                    "hours_ago": 48,
                },
            ],
        },
        {
            "email": "user3@gmail.com",
            "items": [
                {
                    "title": "Lời mời từ danh sách chờ",
                    "content": "Có slot trống mới cho chiến dịch bạn đã đăng ký chờ. Vui lòng phản hồi trước hạn.",
                    "link": "/pages/my-registrations.html",
                    "is_read": False,
                    "hours_ago": 2,
                },
            ],
        },
        {
            "email": "organizer@gmail.com",
            "items": [
                {
                    "title": "Có yêu cầu xác nhận giờ mới",
                    "content": "Tình nguyện viên vừa gửi yêu cầu xác nhận giờ cần bạn xem xét.",
                    "link": "/pages/organizer-dashboard.html",
                    "is_read": False,
                    "hours_ago": 5,
                },
                {
                    "title": "Chiến dịch mới đã được duyệt",
                    "content": "Chiến dịch Dọn vệ sinh Hồ Gươm đã được Admin phê duyệt và mở đăng ký.",
                    "link": "/pages/organizer-dashboard.html",
                    "is_read": True,
                    "hours_ago": 72,
                },
            ],
        },
        {
            "email": "admin@gmail.com",
            "items": [
                {
                    "title": "Hồ sơ tổ chức chờ duyệt",
                    "content": "Tổ chức Ánh Sáng Tri Thức đang chờ Admin xem xét phê duyệt.",
                    "link": "/pages/admin-dashboard.html",
                    "is_read": False,
                    "hours_ago": 6,
                },
                {
                    "title": "Khiếu nại giờ tình nguyện mới",
                    "content": "Có khiếu nại xác nhận giờ đang chờ Admin phân xử.",
                    "link": "/pages/admin-dashboard.html",
                    "is_read": False,
                    "hours_ago": 4,
                },
            ],
        },
    ]

    created = 0
    skipped = 0

    for group in notifications_plan:
        user = db.query(UserModel).filter(UserModel.email == group["email"]).first()
        if not user:
            skipped += len(group["items"])
            continue

        for item in group["items"]:
            existing = db.query(NotificationModel).filter(
                NotificationModel.user_id == user.id,
                NotificationModel.title == item["title"],
            ).first()
            if existing:
                skipped += 1
                continue

            notif = NotificationModel(
                user_id=user.id,
                title=item["title"],
                content=item["content"],
                link=item["link"],
                is_read=item["is_read"],
                created_at=now - timedelta(hours=item["hours_ago"]),
            )
            db.add(notif)
            created += 1
            print(f"  [+] Notification -> {user.email}: {item['title']}")

    db.commit()
    print("\n========== SEED NOTIFICATIONS ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_notifications(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
