
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel

from app.services.organizations import OrganizationService, OrganizerDashboardService
from datetime import date
from typing import Optional

from app.models.organizations import OrganizationModel
from app.services.organizations import OrganizationService

from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.dependencies.auth import get_current_user, require_role

from app.services.organizations import (
    create_organization_service,
    get_my_organization_service,
    update_my_organization_service
)


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED
)
def register_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER"))
):
    return create_organization_service(
        db=db,
        payload=payload,
        owner_id=current_user.id
    )


@router.get(
    "/me",
    response_model=OrganizationResponse
)
def get_my_organization(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return get_my_organization_service(
        db=db,
        owner_id=current_user.id
    )


@router.put(
    "/me",
    response_model=OrganizationResponse
)
def update_my_organization(
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return update_my_organization_service(
        db=db,
        payload=payload,
        owner_id=current_user.id
    )


admin_router = APIRouter(prefix="/admin/organizations", tags=["Admin Organizations"])

@admin_router.get("")
def list_organizations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    return db.query(OrganizationModel).order_by(OrganizationModel.id.desc()).all()


@admin_router.get("/pending")
def list_pending_orgs(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):

    

    return OrganizationService.get_pending_organizations(db)

@admin_router.patch("/{org_id}/review")
def review_org(
    org_id: int,
    action: str, 
    reason: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    updated_org = OrganizationService.review_organization(db, org_id, action, reason)
    return {
        "message": f"Đã xử lý hồ sơ thành công.",
        "organization_id": updated_org.id,
        "status": updated_org.status
    }
    
@router.get("/stats")
def get_organizer_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    
    if current_user.role not in ["ORGANIZER", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập trang quản trị của Organizer."
        )

    
    stats = OrganizerDashboardService.get_organizer_dashboard_stats(
        db=db,
        organizer_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "message": "Lấy dữ liệu thống kê dashboard thành công",
        "data": stats
    }