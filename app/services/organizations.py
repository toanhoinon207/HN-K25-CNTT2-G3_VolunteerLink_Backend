
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
from datetime import date

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
        ).first()

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
            org.status = OrganizationStatus.APPROVED

            if user_owner:
                user_owner.role = "ORGANIZER"

        elif action == "REJECT":
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bắt buộc phải nhập lý do khi từ chối hồ sơ."
                )

            org.status = OrganizationStatus.REJECTED
            org.rejection_reason = reason.strip()

        db.commit()
        db.refresh(org)

        if user_owner:
            db.refresh(user_owner)

        return org

class OrganizerDashboardService:
    
    @staticmethod
    def get_organizer_dashboard_stats(
        db: Session,
        organizer_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
      
        campaign_query = db.query(CampaignModel).filter(CampaignModel.organizer_id == organizer_id)
        
       
        if start_date:
            campaign_query = campaign_query.filter(CampaignModel.created_at >= start_date)
        if end_date:
            campaign_query = campaign_query.filter(CampaignModel.created_at <= end_date)
            
        campaigns = campaign_query.all()
        campaign_ids = [c.id for c in campaigns]

       
        status_counts = {}
        for c in campaigns:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1

        if not campaign_ids:
            return {
                "total_campaigns": 0,
                "campaigns_by_status": {},
                "total_registrations": 0,
                "attendance_rate": 0.0,
                "total_verified_hours": 0.0,
                "top_volunteers": []
            }

       
        total_registrations = db.query(RegistrationModel).filter(
            RegistrationModel.campaign_id.in_(campaign_ids)
        ).count()

       
        total_attendances = db.query(AttendanceModel).filter(
            AttendanceModel.campaign_id.in_(campaign_ids)
        ).count()
        
        attendance_rate = (total_attendances / total_registrations * 100) if total_registrations > 0 else 0.0

       
        total_verified_hours = db.query(func.sum(AttendanceModel.hours)).filter(
            AttendanceModel.campaign_id.in_(campaign_ids),
            AttendanceModel.is_verified == True
        ).scalar() or 0.0

       
        top_volunteers_query = db.query(
            UserModel.id,
            UserModel.full_name,
            UserModel.email,
            func.sum(AttendanceModel.hours).label("total_hours"),
            func.count(AttendanceModel.id).label("total_sessions")
        ).join(AttendanceModel, AttendanceModel.user_id == UserModel.id)\
         .filter(AttendanceModel.campaign_id.in_(campaign_ids))\
         .group_by(UserModel.id, UserModel.full_name, UserModel.email)\
         .order_by(func.sum(AttendanceModel.hours).desc())\
         .limit(10).all()

        top_volunteers = [
            {
                "user_id": v.id,
                "full_name": v.full_name,
                "email": v.email,
                "total_hours": v.total_hours or 0.0,
                "total_sessions": v.total_sessions
            }
            for v in top_volunteers_query
        ]

        return {
            "total_campaigns": len(campaigns),
            "campaigns_by_status": status_counts,
            "total_registrations": total_registrations,
            "attendance_rate": round(attendance_rate, 2),
            "total_verified_hours": round(total_verified_hours, 2),
            "top_volunteers": top_volunteers
        }