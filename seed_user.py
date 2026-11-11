
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.users import UserModel
from app.core.security import hash_password


def seed_users(db: Session):
    users = [
        {
            "full_name": "Nguyễn Văn User",
            "email": "user@gmail.com",
            "password": "User@123456",
            "role": "USER"
        },
        {
            "full_name": "Nguyễn Văn Admin",
            "email": "admin@gmail.com",
            "password": "Admin@123456",
            "role": "ADMIN"
        },
        {
            "full_name": "Nguyễn Văn Organizer",
            "email": "organizer@gmail.com",
            "password": "Organizer@123456",
            "role": "ORGANIZER"
        }
    ]

    for data in users:
        existing = db.query(UserModel).filter(
            UserModel.email == data["email"]
        ).first()

        if existing:
            print(f"Đã tồn tại: {data['email']}")
            continue

        user = UserModel(
            full_name=data["full_name"],
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=data["role"],
            status="ACTIVE"
        )

        db.add(user)
        print(f"Đã tạo: {data['email']}")

    db.commit()


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
