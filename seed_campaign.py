
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.campaigns import CampaignModel
from app.models.organizations import (
    OrganizationModel,
    OrganizationStatus
)


def seed_campaigns(db: Session):

    # Lấy danh sách tổ chức đã được duyệt
    organizations = db.query(OrganizationModel).filter(
        OrganizationModel.status == OrganizationStatus.APPROVED
    ).order_by(OrganizationModel.id).all()

    if not organizations:
        print(
            "Không có Organization APPROVED. "
            "Hãy tạo và duyệt tổ chức trước khi seed Campaign."
        )
        return

    # Thời gian theo máy chạy seed (nên cấu hình máy ở Asia/Ho_Chi_Minh)
    now = datetime.now()

    campaigns_data = [
        {
            "title": "Dọn vệ sinh Hồ Gươm",
            "category": "ENVIRONMENT",
            "location": "Hoàn Kiếm, Hà Nội",
            "days": 7,
            "status": "OPEN"
        },
        {
            "title": "Trồng cây xanh tại Ba Vì",
            "category": "ENVIRONMENT",
            "location": "Ba Vì, Hà Nội",
            "days": 12,
            "status": "OPEN"
        },
        {
            "title": "Tiếp sức mùa thi",
            "category": "EDUCATION",
            "location": "Cầu Giấy, Hà Nội",
            "days": 20,
            "status": "PENDING"
        },
        {
            "title": "Dạy học cho trẻ em khó khăn",
            "category": "EDUCATION",
            "location": "Long Biên, Hà Nội",
            "days": 15,
            "status": "OPEN"
        },
        {
            "title": "Ngày hội hiến máu nhân đạo",
            "category": "HEALTH",
            "location": "Đống Đa, Hà Nội",
            "days": 9,
            "status": "OPEN"
        },
        {
            "title": "Tặng sách cho trẻ em vùng cao",
            "category": "EDUCATION",
            "location": "Sa Pa, Lào Cai",
            "days": 25,
            "status": "DRAFT"
        },
        {
            "title": "Bữa cơm yêu thương",
            "category": "COMMUNITY",
            "location": "Hai Bà Trưng, Hà Nội",
            "days": 5,
            "status": "OPEN"
        },
        {
            "title": "Áo ấm mùa đông",
            "category": "COMMUNITY",
            "location": "Đồng Văn, Hà Giang",
            "days": 30,
            "status": "PENDING"
        },
        {
            "title": "Làm sạch bãi biển Mỹ Khê",
            "category": "ENVIRONMENT",
            "location": "Sơn Trà, Đà Nẵng",
            "days": 18,
            "status": "OPEN"
        },
        {
            "title": "Chăm sóc người cao tuổi",
            "category": "COMMUNITY",
            "location": "Thanh Xuân, Hà Nội",
            "days": 10,
            "status": "DRAFT"
        },
        {
            "title": "Ngày hội tái chế rác thải",
            "category": "ENVIRONMENT",
            "location": "Nam Từ Liêm, Hà Nội",
            "days": -10,
            "status": "COMPLETED"
        },
        {
            "title": "Trung thu cho em",
            "category": "COMMUNITY",
            "location": "Hà Đông, Hà Nội",
            "days": -30,
            "status": "COMPLETED"
        },
        {
            "title": "Hỗ trợ thư viện cộng đồng",
            "category": "EDUCATION",
            "location": "Lê Chân, Hải Phòng",
            "days": -5,
            "status": "CLOSED"
        },
        {
            "title": "Chạy bộ gây quỹ từ thiện",
            "category": "HEALTH",
            "location": "Tây Hồ, Hà Nội",
            "days": -15,
            "status": "CLOSED"
        },
        {
            "title": "Chiến dịch xanh cuối tuần",
            "category": "ENVIRONMENT",
            "location": "Gia Lâm, Hà Nội",
            "days": 35,
            "status": "CANCELLED"
        }
    ]

    created_count = 0
    skipped_count = 0

    try:
        for index, data in enumerate(campaigns_data):

            # Phân bổ chiến dịch cho các tổ chức đã duyệt
            organization = organizations[index % len(organizations)]

            # Kiểm tra trùng theo tổ chức và tiêu đề
            existing = db.query(CampaignModel).filter(
                CampaignModel.organization_id == organization.id,
                CampaignModel.title == data["title"]
            ).first()

            if existing:
                print(f"Đã tồn tại: {data['title']}")
                skipped_count += 1
                continue

            start_time = (
                now + timedelta(days=data["days"])
            ).replace(
                hour=8,
                minute=0,
                second=0,
                microsecond=0
            )

            end_time = start_time + timedelta(hours=4)

            registration_deadline = (
                start_time - timedelta(days=2)
            )

            campaign = CampaignModel(
                organization_id=organization.id,

                title=data["title"],

                description=(
                    f"Chiến dịch {data['title']} "
                    "nhằm hỗ trợ cộng đồng, lan tỏa "
                    "tinh thần tình nguyện và tạo ra "
                    "những giá trị tích cực cho xã hội."
                ),

                image_url=None,

                category=data["category"],

                location=data["location"],

                start_time=start_time,
                end_time=end_time,
                registration_deadline=registration_deadline,

                max_participants=20 + index * 5,

                requirements=(
                    "Có tinh thần trách nhiệm, "
                    "tham gia đúng giờ và tuân thủ "
                    "hướng dẫn của ban tổ chức."
                ),

                estimated_hours=4.0,

                status=data["status"],

                reason=(
                    "Chiến dịch bị hủy do thay đổi kế hoạch."
                    if data["status"] == "CANCELLED"
                    else None
                ),

                attendance_code=None,
                attendance_code_expires_at=None
            )

            db.add(campaign)

            created_count += 1

            print(
                f"Đã tạo: {data['title']} "
                f"| Organization: {organization.id} "
                f"| Status: {data['status']}"
            )

        db.commit()

        print("\n========== SEED CAMPAIGN ==========")
        print(f"Đã tạo: {created_count}")
        print(f"Bỏ qua: {skipped_count}")
        print("Seed hoàn tất!")

    except Exception:
        db.rollback()
        raise


def main():
    db = SessionLocal()

    try:
        seed_campaigns(db)

    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":

    main()

