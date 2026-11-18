
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
from app.services.organizations import OrganizationService, OrganizerDashboardService
from datetime import date
from typing import Optional
import traceback
from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.dependencies.auth import get_current_user

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
    current_user: UserModel = Depends(get_current_user)
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


router = APIRouter(prefix="/admin/organizations", tags=["Admin Organizations"])

@router.get("/pending")
def list_pending_orgs(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    
    return OrganizationService.get_pending_organizations(db)

@router.patch("/{org_id}/review")
def review_org(
    org_id: int,
    action: str, 
    reason: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
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
    current_user = Depends(get_current_user)  
):
    if current_user.role.lower() not in ["organizer", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền truy cập."
        )

    try:
        
        stats = OrganizerDashboardService.get_organizer_dashboard_stats(
            db=db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "message": "Thành công",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))