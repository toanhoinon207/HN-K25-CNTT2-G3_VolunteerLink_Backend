
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.users import UserModel
from app.schemas.organizations import OrganizationCreate, OrganizationUpdate

from typing import Optional
from app.models.attendances import AttendanceModel
from app.models.registration import RegistrationModel
from app.models.campaigns import CampaignModel
from sqlalchemy import func
from datetime import date, datetime

from app.services.notifications import create_notification



def get_organization_by_owner(db: Session, owner_id: int):
    return db.query(OrganizationModel).filter(
        OrganizationModel.owner_id == owner_id
    ).first()


def get_organization_by_email(db: Session, email: str):
    return db.query(OrganizationModel).filter(
        OrganizationModel.email == email
    ).first()


def create_organization_service(
    db: Session,
    payload: OrganizationCreate,
    owner_id: int
):
    existing_org = get_organization_by_owner(db, owner_id)

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi tài khoản chỉ được phép đăng ký tối đa một tổ chức."
        )

    email_exist = get_organization_by_email(db, payload.email)

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email của tổ chức này đã được sử dụng."
        )

    db_org = OrganizationModel(
        name=payload.name,
        description=payload.description,
        logo_url=payload.logo_url,
        address=payload.address,
        email=payload.email,
        phone=payload.phone,
        document_url=payload.document_url,
        status=OrganizationStatus.PENDING,
        owner_id=owner_id
    )

    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    return db_org


def get_my_organization_service(
    db: Session,
    owner_id: int
):
    org = get_organization_by_owner(db, owner_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bạn chưa đăng ký hồ sơ tổ chức nào."
        )

    return org


def update_my_organization_service(
    db: Session,
    payload: OrganizationUpdate,
    owner_id: int
):
    org = get_organization_by_owner(db, owner_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tổ chức của bạn."
        )

    if payload.email and payload.email != org.email:
        email_exist = get_organization_by_email(db, payload.email)

        if email_exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email của tổ chức này đã được sử dụng."
            )

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    update_data.pop("status", None)
    update_data.pop("rejection_reason", None)

    for key, value in update_data.items():
        setattr(org, key, value)

    if org.status == OrganizationStatus.REJECTED:
        org.status = OrganizationStatus.PENDING
        org.rejection_reason = None

    db.commit()
    db.refresh(org)

    return org


class OrganizationService:

    @staticmethod
    def get_pending_organizations(db: Session):
        """Lấy danh sách hồ sơ đang chờ duyệt."""

        return db.query(OrganizationModel).filter(
            OrganizationModel.status == OrganizationStatus.PENDING
        ).all()

    @staticmethod
    def review_organization(
        db: Session,
        org_id: int,
        action: str,
        reason: str | None = None
    ):
        

        org = db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).with_for_update().first()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin tổ chức."
            )

        if org.status != OrganizationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hồ sơ này đã được xử lý trước đó với trạng thái: {org.status}"
            )

        action = action.strip().upper()

        if action not in ["APPROVE", "REJECT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hành động không hợp lệ. Chỉ chấp nhận APPROVE hoặc REJECT."
            )

        user_owner = db.query(UserModel).filter(
            UserModel.id == org.owner_id
        ).first()

        if action == "APPROVE":
            if user_owner is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Không thể duyệt: tài khoản quản lý tổ chức không tồn tại."
                )
            if user_owner.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Không thể duyệt: tài khoản quản lý tổ chức không hoạt động."
                )
            if user_owner.role != "USER":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Không thể duyệt: tài khoản không còn vai trò USER."
                )
            org.status = OrganizationStatus.APPROVED
            user_owner.role = "ORGANIZER"
            create_notification(
                db=db,
                user_id=user_owner.id,
                title="Hồ sơ tổ chức đã được duyệt",
                content=f'Hồ sơ của tổ chức "{org.name}" đã được phê duyệt.',
                link="organizer-dashboard.html?tab=profile",
            )

        elif action == "REJECT":
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bắt buộc phải nhập lý do khi từ chối hồ sơ."
                )

            org.status = OrganizationStatus.REJECTED
            org.rejection_reason = reason.strip()
            if user_owner is not None:
                create_notification(
                    db=db,
                    user_id=user_owner.id,
                    title="Hồ sơ tổ chức bị từ chối",
                    content=f'Hồ sơ của tổ chức "{org.name}" bị từ chối. Lý do: {org.rejection_reason}',
                    link="user-dashboard.html?tab=upgrade",
                )

        db.commit()
        db.refresh(org)

        if user_owner:
            db.refresh(user_owner)

        return org

class OrganizerDashboardService:
    
    @staticmethod
    def get_organizer_dashboard_stats(
        db: Session,
        current_user,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        # 1. Truy vấn các chiến dịch
        campaign_query = db.query(CampaignModel)
        
        if current_user.role.lower() != "admin":
            campaign_query = campaign_query.filter(CampaignModel.organization_id == current_user.id)
        
        # Lọc theo khoảng thời gian start_time của chiến dịch
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            campaign_query = campaign_query.filter(CampaignModel.start_time >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            campaign_query = campaign_query.filter(CampaignModel.start_time <= end_datetime)
            
        campaigns = campaign_query.all()
        campaign_ids = [c.id for c in campaigns]

        # 2. Thống kê số chiến dịch theo trạng thái và chuẩn bị danh sách chiến dịch chi tiết
        status_counts = {}
        campaign_list = []
        for c in campaigns:
            status_str = c.status.value if hasattr(c.status, "value") else str(c.status)
            status_counts[status_str] = status_counts.get(status_str, 0) + 1
            
            # Lấy tên chiến dịch (thử thuộc tính title hoặc name)
            campaign_title = getattr(c, "title", getattr(c, "name", f"Chiến dịch #{c.id}"))
            
            campaign_list.append({
                "id": c.id,
                "title": campaign_title,
                "status": status_str,
                "start_time": str(c.start_time) if c.start_time else None,
                "end_time": str(c.end_time) if hasattr(c, "end_time") and c.end_time else None
            })

        if not campaign_ids:
            return {
                "total_campaigns": 0,
                "campaigns_by_status": {},
                "campaigns": [],
                "total_registrations": 0,
                "attendance_rate": 0.0,
                "total_verified_hours": 0.0,
                "top_volunteers": []
            }

        # 3. Tổng lượt đăng ký
        total_registrations = db.query(RegistrationModel).filter(
            RegistrationModel.campaign_id.in_(campaign_ids)
        ).count()

        # 4. Tỉ lệ có mặt
        total_attendances = db.query(AttendanceModel).join(
            RegistrationModel, AttendanceModel.registration_id == RegistrationModel.id
        ).filter(
            RegistrationModel.campaign_id.in_(campaign_ids),
            AttendanceModel.check_in_at.isnot(None)
        ).count()
        
        attendance_rate = (total_attendances / total_registrations * 100) if total_registrations > 0 else 0.0

        # 5. Tổng số giờ đóng góp đã xác minh
        total_minutes_sum = db.query(func.sum(AttendanceModel.total_minutes)).join(
            RegistrationModel, AttendanceModel.registration_id == RegistrationModel.id
        ).filter(
            RegistrationModel.campaign_id.in_(campaign_ids)
        ).scalar() or 0
        
        total_verified_hours = round(total_minutes_sum / 60.0, 2)

        # 6. Top 10 tình nguyện viên
        top_volunteers_query = db.query(
            UserModel.id,
            UserModel.full_name,
            UserModel.email,
            func.sum(AttendanceModel.total_minutes).label("total_minutes"),
            func.count(AttendanceModel.id).label("total_sessions")
        ).join(RegistrationModel, RegistrationModel.user_id == UserModel.id)\
         .join(AttendanceModel, AttendanceModel.registration_id == RegistrationModel.id)\
         .filter(RegistrationModel.campaign_id.in_(campaign_ids))\
         .group_by(UserModel.id, UserModel.full_name, UserModel.email)\
         .order_by(func.sum(AttendanceModel.total_minutes).desc())\
         .limit(10).all()

        top_volunteers = [
            {
                "user_id": v.id,
                "full_name": v.full_name,
                "email": v.email,
                "total_hours": round((v.total_minutes or 0) / 60.0, 2),
                "total_sessions": v.total_sessions
            }
            for v in top_volunteers_query
        ]

        return {
            "total_campaigns": len(campaigns),
            "campaigns_by_status": status_counts,
            "campaigns": campaign_list,  # <--- Danh sách chi tiết các chiến dịch
            "total_registrations": total_registrations,
            "attendance_rate": round(attendance_rate, 2),
            "total_verified_hours": total_verified_hours,
            "top_volunteers": top_volunteers
        }
        
