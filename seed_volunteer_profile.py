"""Script seed dữ liệu mẫu cho volunteer_profiles.

Chạy: python seed_volunteer_profile.py
"""
from datetime import date
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.volunteer_profiles import VolunteerProfileModel


def seed_volunteer_profiles(db: Session):
    profiles_data = [
        {
            "email": "user@gmail.com",
            "date_of_birth": date(2002, 5, 15),
            "skills": "Giao tiếp, Tổ chức sự kiện, Sơ cứu cơ bản",
            "area": "Hoàn Kiếm, Hà Nội",
        },
        {
            "email": "user2@gmail.com",
            "date_of_birth": date(2003, 8, 22),
            "skills": "Dạy học, Thiết kế đồ họa, Chụp ảnh",
            "area": "Cầu Giấy, Hà Nội",
        },
        {
            "email": "user3@gmail.com",
            "date_of_birth": date(2001, 11, 3),
            "skills": "Nấu ăn, Hậu cần, Điều phối nhóm",
            "area": "Đống Đa, Hà Nội",
        },
        {
            "email": "user4@gmail.com",
            "date_of_birth": date(2004, 2, 19),
            "skills": "Tiếng Anh, Truyền thông, Viết nội dung",
            "area": "Thanh Xuân, Hà Nội",
        },
        {
            "email": "user5@gmail.com",
            "date_of_birth": date(2000, 9, 10),
            "skills": "Y tế cộng đồng, Vận động thể chất",
            "area": "Hai Bà Trưng, Hà Nội",
        },
        {
            "email": "locked_user@gmail.com",
            "date_of_birth": date(2002, 1, 1),
            "skills": "Hậu cần",
            "area": "Long Biên, Hà Nội",
        },
    ]

    created = 0
    skipped = 0

    for data in profiles_data:
        user = db.query(UserModel).filter(UserModel.email == data["email"]).first()
        if not user:
            print(f"[!] Chưa có tài khoản {data['email']}, bỏ qua.")
            skipped += 1
            continue

        existing = db.query(VolunteerProfileModel).filter(
            VolunteerProfileModel.user_id == user.id
        ).first()
        if existing:
            print(f"Đã tồn tại profile: {data['email']}")
            skipped += 1
            continue

        profile = VolunteerProfileModel(
            user_id=user.id,
            date_of_birth=data["date_of_birth"],
            skills=data["skills"],
            area=data["area"],
        )
        db.add(profile)
        created += 1
        print(f"Đã tạo profile: {data['email']}")

    db.commit()
    print("\n========== SEED VOLUNTEER PROFILES ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_volunteer_profiles(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
