
"""
Auto-seed dữ liệu mẫu VolunteerLink khi server khởi động.

Thứ tự:
Users -> Organizations -> Campaigns -> Attendances

Chỉ thêm dữ liệu chưa tồn tại, không xóa dữ liệu cũ.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.users import UserModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel


# ============================================================
# 1. USERS
# ============================================================

_USERS = [
    # USER
    {
        "full_name": "Nguyễn Văn User",
        "email": "user@gmail.com",
        "password": "User@123456",
        "role": "USER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Trần Minh Anh",
        "email": "user2@gmail.com",
        "password": "User@123456",
        "role": "USER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Lê Hoàng Nam",
        "email": "user3@gmail.com",
        "password": "User@123456",
        "role": "USER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Phạm Thu Hà",
        "email": "user4@gmail.com",
        "password": "User@123456",
        "role": "USER",
        "status": "LOCKED",
    },
    {
        "full_name": "Đỗ Quang Huy",
        "email": "user5@gmail.com",
        "password": "User@123456",
        "role": "USER",
        "status": "ACTIVE",
    },

    # ORGANIZER
    {
        "full_name": "Nguyễn Văn Organizer",
        "email": "organizer@gmail.com",
        "password": "Organizer@123456",
        "role": "ORGANIZER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Trần Quốc Bảo",
        "email": "organizer2@gmail.com",
        "password": "Organizer@123456",
        "role": "ORGANIZER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Lê Thị Hương",
        "email": "organizer3@gmail.com",
        "password": "Organizer@123456",
        "role": "ORGANIZER",
        "status": "ACTIVE",
    },
    {
        "full_name": "Phạm Đức Minh",
        "email": "organizer4@gmail.com",
        "password": "Organizer@123456",
        "role": "ORGANIZER",
        "status": "LOCKED",
    },
    {
        "full_name": "Hoàng Ngọc Lan",
        "email": "organizer5@gmail.com",
        "password": "Organizer@123456",
        "role": "ORGANIZER",
        "status": "ACTIVE",
    },

    # ADMIN
    {
        "full_name": "Nguyễn Văn Admin",
        "email": "admin@gmail.com",
        "password": "Admin@123456",
        "role": "ADMIN",
        "status": "ACTIVE",
    },
    {
        "full_name": "Trần Văn Quản Trị",
        "email": "admin2@gmail.com",
        "password": "Admin@123456",
        "role": "ADMIN",
        "status": "ACTIVE",
    },
]


def _seed_users(db: Session) -> int:
    created = 0

    for data in _USERS:
        existing = (
            db.query(UserModel)
            .filter(UserModel.email == data["email"])
            .first()
        )

        if existing:
            continue

        db.add(
            UserModel(
                full_name=data["full_name"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
                status=data["status"],
            )
        )
        created += 1

    db.commit()
    return created


# ============================================================
# 2. ORGANIZATIONS
# ============================================================

_ORGANIZATIONS = [
    {
        "name": "VolunteerLink Hà Nội",
        "email": "contact@volunteerlink.vn",
        "phone": "0241234567",
        "address": "Hoàn Kiếm, Hà Nội",
        "description": "Tổ chức hoạt động tình nguyện vì cộng đồng tại Hà Nội.",
        "owner_email": "organizer@gmail.com",
        "status": OrganizationStatus.APPROVED,
    },
    {
        "name": "Green Future Việt Nam",
        "email": "greenfuture@example.com",
        "phone": "0901234567",
        "address": "Cầu Giấy, Hà Nội",
        "description": "Tổ chức các hoạt động bảo vệ môi trường và trồng cây xanh.",
        "owner_email": "organizer2@gmail.com",
        "status": OrganizationStatus.APPROVED,
    },
    {
        "name": "Hope Education",
        "email": "hopeedu@example.com",
        "phone": "0912345678",
        "address": "Đống Đa, Hà Nội",
        "description": "Hỗ trợ giáo dục cho trẻ em có hoàn cảnh khó khăn.",
        "owner_email": "organizer3@gmail.com",
        "status": OrganizationStatus.PENDING,
    },
    {
        "name": "Helping Hands",
        "email": "helpinghands@example.com",
        "phone": "0923456789",
        "address": "Thanh Xuân, Hà Nội",
        "description": "Kết nối cộng đồng thông qua các hoạt động thiện nguyện.",
        "owner_email": "organizer4@gmail.com",
        "status": OrganizationStatus.REJECTED,
    },
    {
        "name": "Community Care",
        "email": "communitycare@example.com",
        "phone": "0934567890",
        "address": "Hà Đông, Hà Nội",
        "description": "Hỗ trợ người già và những người có hoàn cảnh khó khăn.",
        "owner_email": "organizer5@gmail.com",
        "status": OrganizationStatus.APPROVED,
    },
]


def _seed_organizations(db: Session) -> int:
    created = 0

    for data in _ORGANIZATIONS:
        owner = (
            db.query(UserModel)
            .filter(
                UserModel.email == data["owner_email"],
                UserModel.role == "ORGANIZER",
            )
            .first()
        )

        if not owner:
            continue

        existing = (
            db.query(OrganizationModel)
            .filter(OrganizationModel.owner_id == owner.id)
            .first()
        )

        if existing:
            continue

        db.add(
            OrganizationModel(
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
                ),
            )
        )

        created += 1

    db.commit()
    return created


# ============================================================
# 3. CAMPAIGNS
# ============================================================

_CAMPAIGNS_DATA = [
    {
        "title": "Dọn vệ sinh Hồ Gươm",
        "category": "ENVIRONMENT",
        "location": "Hoàn Kiếm, Hà Nội",
        "days": 0,
        "status": "OPEN",
        "code": "LIVE26",
    },
    {
        "title": "Trồng cây xanh tại Ba Vì",
        "category": "ENVIRONMENT",
        "location": "Ba Vì, Hà Nội",
        "days": 12,
        "status": "OPEN",
    },
    {
        "title": "Tiếp sức mùa thi",
        "category": "EDUCATION",
        "location": "Cầu Giấy, Hà Nội",
        "days": 20,
        "status": "PENDING",
    },
    {
        "title": "Dạy học cho trẻ em khó khăn",
        "category": "EDUCATION",
        "location": "Long Biên, Hà Nội",
        "days": 15,
        "status": "OPEN",
    },
    {
        "title": "Ngày hội hiến máu nhân đạo",
        "category": "HEALTH",
        "location": "Đống Đa, Hà Nội",
        "days": 9,
        "status": "OPEN",
    },
    {
        "title": "Bữa cơm yêu thương",
        "category": "COMMUNITY",
        "location": "Hai Bà Trưng, Hà Nội",
        "days": 5,
        "status": "OPEN",
    },
    {
        "title": "Làm sạch bãi biển Mỹ Khê",
        "category": "ENVIRONMENT",
        "location": "Sơn Trà, Đà Nẵng",
        "days": 18,
        "status": "OPEN",
    },
    {
        "title": "Ngày hội tái chế rác thải",
        "category": "ENVIRONMENT",
        "location": "Nam Từ Liêm, Hà Nội",
        "days": -10,
        "status": "COMPLETED",
    },
    {
        "title": "Trung thu cho em",
        "category": "COMMUNITY",
        "location": "Hà Đông, Hà Nội",
        "days": -30,
        "status": "COMPLETED",
    },
    {
        "title": "Hỗ trợ thư viện cộng đồng",
        "category": "EDUCATION",
        "location": "Lê Chân, Hải Phòng",
        "days": -5,
        "status": "CLOSED",
    },
    {
        "title": "Chạy bộ gây quỹ từ thiện",
        "category": "HEALTH",
        "location": "Tây Hồ, Hà Nội",
        "days": -15,
        "status": "CLOSED",
    },
]


def _seed_campaigns(db: Session) -> int:
    organizations = (
        db.query(OrganizationModel)
        .filter(
            OrganizationModel.status == OrganizationStatus.APPROVED
        )
        .order_by(OrganizationModel.id)
        .all()
    )

    if not organizations:
        return 0

    now = datetime.now()
    created = 0

    for idx, data in enumerate(_CAMPAIGNS_DATA):
        org = organizations[idx % len(organizations)]

        existing = (
            db.query(CampaignModel)
            .filter(
                CampaignModel.organization_id == org.id,
                CampaignModel.title == data["title"],
            )
            .first()
        )

        if existing:
            continue

        days = data["days"]

        if days == 0:
            start_time = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_time = now.replace(
                hour=23, minute=59, second=59, microsecond=0
            )
            reg_deadline = now - timedelta(hours=2)
        else:
            start_time = (
                now + timedelta(days=days)
            ).replace(
                hour=8, minute=0, second=0, microsecond=0
            )
            end_time = start_time + timedelta(hours=4)
            reg_deadline = start_time - timedelta(days=2)

        code = data.get("code")
        code_expires = (
            now + timedelta(days=1) if code else None
        )

        db.add(
            CampaignModel(
                organization_id=org.id,
                title=data["title"],
                description=(
                    f"Chiến dịch {data['title']} nhằm hỗ trợ cộng đồng, "
                    "lan tỏa tinh thần tình nguyện và tạo ra "
                    "những giá trị tích cực cho xã hội."
                ),
                image_url=None,
                category=data["category"],
                location=data["location"],
                start_time=start_time,
                end_time=end_time,
                registration_deadline=reg_deadline,
                max_participants=20 + idx * 5,
                requirements=(
                    "Có tinh thần trách nhiệm, tham gia đúng giờ "
                    "và tuân thủ hướng dẫn của ban tổ chức."
                ),
                estimated_hours=4.0,
                status=data["status"],
                reason=(
                    "Chiến dịch bị hủy do thay đổi kế hoạch."
                    if data["status"] == "CANCELLED"
                    else None
                ),
                attendance_code=code,
                attendance_code_expires_at=code_expires,
            )
        )

        created += 1

    db.commit()
    return created


# ============================================================
# 4. ATTENDANCES
# ============================================================

def _seed_attendances(db: Session) -> int:
    volunteer = (
        db.query(UserModel)
        .filter(UserModel.email == "user@gmail.com")
        .first()
    )

    organizer = (
        db.query(UserModel)
        .filter(UserModel.email == "organizer@gmail.com")
        .first()
    )

    if not volunteer:
        return 0

    campaigns = db.query(CampaignModel).all()

    if not campaigns:
        return 0

    now = datetime.now().replace(microsecond=0)
    created_att = 0
    MAX_ATT = 5

    for campaign in campaigns:
        if created_att >= MAX_ATT:
            break

        # Tạo đơn đăng ký APPROVED nếu chưa có
        reg = (
            db.query(RegistrationModel)
            .filter(
                RegistrationModel.user_id == volunteer.id,
                RegistrationModel.campaign_id == campaign.id,
            )
            .first()
        )

        if not reg:
            reg_time = (
                (
                    campaign.start_time - timedelta(days=3)
                ).replace(second=0, microsecond=0)
                if campaign.start_time
                else now - timedelta(days=5)
            )

            reg = RegistrationModel(
                user_id=volunteer.id,
                campaign_id=campaign.id,
                status="APPROVED",
                message=f"Đăng ký tham gia chiến dịch {campaign.title}",
                created_at=reg_time,
            )

            db.add(reg)
            db.flush()

        # Chiến dịch hôm nay: để user test check-in
        is_today = bool(
            campaign.start_time
            and campaign.end_time
            and campaign.start_time <= now <= campaign.end_time
        )

        if is_today:
            if not campaign.attendance_code:
                campaign.attendance_code = "LIVE26"
                campaign.attendance_code_expires_at = (
                    now + timedelta(days=1)
                )
            continue

        # Không tạo điểm danh trùng
        existing_att = (
            db.query(AttendanceModel)
            .filter(
                AttendanceModel.registration_id == reg.id
            )
            .first()
        )

        if existing_att:
            continue

        if campaign.start_time and campaign.end_time:
            ci = campaign.start_time.replace(
                second=0, microsecond=0
            )
            co = campaign.end_time.replace(
                second=0, microsecond=0
            )

            if co > now:
                dur_h = max(
                    1.0,
                    (co - ci).total_seconds() / 3600
                )

                ci = (
                    now - timedelta(days=1)
                ).replace(
                    hour=8, minute=0, second=0, microsecond=0
                )

                co = ci + timedelta(hours=dur_h)
        else:
            ci = (
                now - timedelta(days=1)
            ).replace(
                hour=8, minute=0, second=0, microsecond=0
            )

            co = ci + timedelta(hours=4)

        total_mins = max(
            0,
            int(round((co - ci).total_seconds() / 60))
        )

        db.add(
            AttendanceModel(
                registration_id=reg.id,
                check_in_at=ci,
                check_out_at=co,
                total_minutes=total_mins,
                recorded_by=organizer.id if organizer else None,
                status="PRESENT",
                edit_reason=None,
            )
        )

        created_att += 1

    db.commit()
    return created_att


# ============================================================
# 5. RUN SEED
# ============================================================

def run_seed():
    """Tự động thêm dữ liệu mẫu khi server khởi động."""

    db: Session = SessionLocal()

    try:
        u = _seed_users(db)
        o = _seed_organizations(db)
        c = _seed_campaigns(db)
        a = _seed_attendances(db)

        print(
            f"[SEED] Users: +{u} | "
            f"Organizations: +{o} | "
            f"Campaigns: +{c} | "
            f"Attendances: +{a}"
        )

        if not any([u, o, c, a]):
            print("[SEED] Không có dữ liệu mới cần thêm.")

    except Exception as exc:
        db.rollback()
        print(f"[SEED] Lỗi khi seed: {exc}")
        raise

    finally:
        db.close()
