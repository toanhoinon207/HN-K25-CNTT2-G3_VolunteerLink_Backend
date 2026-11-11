
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.users import UserModel
from app.models.organizations import (
    OrganizationModel,
    OrganizationStatus
)


def seed_organizations(db: Session):

    organizations_data = [
        {
            "name": "VolunteerLink Hà Nội",
            "email": "contact@volunteerlink.vn",
            "phone": "0241234567",
            "address": "Hoàn Kiếm, Hà Nội",
            "description": "Tổ chức hoạt động tình nguyện vì cộng đồng tại Hà Nội.",
            "owner_email": "organizer@gmail.com",
            "status": OrganizationStatus.APPROVED
        },
        {
            "name": "Cộng đồng Xanh Việt Nam",
            "email": "contact@congdongxanh.vn",
            "phone": "0242345678",
            "address": "Cầu Giấy, Hà Nội",
            "description": "Tổ chức các hoạt động bảo vệ môi trường.",
            "owner_email": "organizer2@gmail.com",
            "status": OrganizationStatus.APPROVED
        },
        {
            "name": "Kết Nối Yêu Thương",
            "email": "contact@ketnoiyeuthuong.vn",
            "phone": "0243456789",
            "address": "Đống Đa, Hà Nội",
            "description": "Hỗ trợ trẻ em và người có hoàn cảnh khó khăn.",
            "owner_email": "organizer3@gmail.com",
            "status": OrganizationStatus.APPROVED
        },
        {
            "name": "Ánh Sáng Tri Thức",
            "email": "contact@anhsangtrithuc.vn",
            "phone": "0244567890",
            "address": "Thanh Xuân, Hà Nội",
            "description": "Tổ chức các chương trình giáo dục cộng đồng.",
            "owner_email": "organizer4@gmail.com",
            "status": OrganizationStatus.PENDING
        },
        {
            "name": "Nhịp Cầu Nhân Ái",
            "email": "contact@nhipcaunhanai.vn",
            "phone": "0245678901",
            "address": "Long Biên, Hà Nội",
            "description": "Tổ chức các chương trình thiện nguyện và hỗ trợ cộng đồng.",
            "owner_email": "organizer5@gmail.com",
            "status": OrganizationStatus.REJECTED
        }
    ]

    created = 0
    skipped = 0

    try:
        for data in organizations_data:

            owner = db.query(UserModel).filter(
                UserModel.email == data["owner_email"],
                UserModel.role == "ORGANIZER"
            ).first()

            if not owner:
                print(
                    f"Bỏ qua {data['name']}: "
                    f"chưa có tài khoản {data['owner_email']} "
                    "với role ORGANIZER"
                )
                skipped += 1
                continue

            existing = db.query(OrganizationModel).filter(
                OrganizationModel.owner_id == owner.id
            ).first()

            if existing:
                print(
                    f"Bỏ qua {data['name']}: "
                    f"Organizer {owner.email} đã sở hữu tổ chức"
                )
                skipped += 1
                continue

            existing_email = db.query(OrganizationModel).filter(
                OrganizationModel.email == data["email"]
            ).first()

            if existing_email:
                print(
                    f"Bỏ qua {data['name']}: "
                    "email tổ chức đã tồn tại"
                )
                skipped += 1
                continue

            organization = OrganizationModel(
                name=data["name"],
                description=data["description"],
                logo_url=None,
                address=data["address"],
                email=data["email"],
                phone=data["phone"],
                document_url=None,
                status=data["status"],
                owner_id=owner.id,
                rejection_reason=(
                    "Hồ sơ chưa đáp ứng yêu cầu xác minh."
                    if data["status"] == OrganizationStatus.REJECTED
                    else None
                )
            )

            db.add(organization)
            created += 1

            print(
                f"Đã thêm: {data['name']} "
                f"| Owner: {owner.email} "
                f"| Status: {data['status'].value}"
            )

        db.commit()

        print("\n========== SEED ORGANIZATION ==========")
        print(f"Đã tạo: {created}")
        print(f"Bỏ qua: {skipped}")
        print("Seed hoàn tất!")

    except Exception:
        db.rollback()
        raise


def main():
    db = SessionLocal()

    try:
        seed_organizations(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()