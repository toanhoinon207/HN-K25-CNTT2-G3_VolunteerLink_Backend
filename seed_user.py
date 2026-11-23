from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.users import UserModel
from app.core.security import hash_password

DEFAULT_PASSWORD = "12345678"


def seed_users(db: Session):
    users = [
        {
            "full_name": "Nguyễn Văn Admin",
            "email": "admin@gmail.com",
            "phone": "0901000001",
            "role": "ADMIN",
            "status": "ACTIVE",
        },
        {
            "full_name": "Nguyễn Văn Organizer",
            "email": "organizer@gmail.com",
            "phone": "0902000001",
            "role": "ORGANIZER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Trần Thị Organizer 2",
            "email": "organizer2@gmail.com",
            "phone": "0902000002",
            "role": "ORGANIZER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Lê Minh Organizer 3",
            "email": "organizer3@gmail.com",
            "phone": "0902000003",
            "role": "ORGANIZER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Phạm Thu Organizer 4",
            "email": "organizer4@gmail.com",
            "phone": "0902000004",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Hoàng Đức Organizer 5",
            "email": "organizer5@gmail.com",
            "phone": "0902000005",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Nguyễn Văn User",
            "email": "user@gmail.com",
            "phone": "0903000001",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Trần Lan Anh",
            "email": "user2@gmail.com",
            "phone": "0903000002",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Lê Quốc Bảo",
            "email": "user3@gmail.com",
            "phone": "0903000003",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Phạm Minh Châu",
            "email": "user4@gmail.com",
            "phone": "0903000004",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Đỗ Hải Đăng",
            "email": "user5@gmail.com",
            "phone": "0903000005",
            "role": "USER",
            "status": "ACTIVE",
        },
        {
            "full_name": "Tài Khoản Bị Khóa",
            "email": "locked_user@gmail.com",
            "phone": "0903000099",
            "role": "USER",
            "status": "LOCKED",
        },
    ]

    created = 0
    skipped = 0

    for data in users:
        existing = db.query(UserModel).filter(
            UserModel.email == data["email"]
        ).first()

        if existing:
            print(f"Đã tồn tại: {data['email']}")
            skipped += 1
            continue

        # Gọi hash_password riêng cho từng user để mỗi tài khoản có salt & hash khác nhau
        user = UserModel(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            password_hash=hash_password(DEFAULT_PASSWORD),
            role=data["role"],
            status=data["status"],
        )

        db.add(user)
        created += 1
        print(f"Đã tạo: {data['email']} ({data['role']} / {data['status']})")

    db.commit()
    print(f"\n========== SEED USERS ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()

    try:
        seed_users(db)
        print("Seed hoàn tất!")
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":

    main()