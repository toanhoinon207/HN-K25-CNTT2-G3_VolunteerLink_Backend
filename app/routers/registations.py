from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.schemas.registration import RegistrationCreate, RegistrationResponse
from app.services.registrations import create_registration, cancel_registration, get_campaign_registrations, reject_registration
from app.services.registrations import approve_registration
from app.schemas.registration import RejectRegistrationRequest

def verify_campaign_owner(db: Session, campaign_id: int, user_id: int):
    campaign = db.query(CampaignModel).join(
        OrganizationModel, CampaignModel.organization_id == OrganizationModel.id
    ).filter(
        CampaignModel.id == campaign_id,
        OrganizationModel.owner_id == user_id
    ).first()
    if campaign is None:
        raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý đăng ký của chiến dịch này")
    return campaign


router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"]
)


@router.get("/me")
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Lấy danh sách đơn đăng ký của chính người dùng hiện tại từ Database."""
    regs = db.query(RegistrationModel).join(
        CampaignModel, RegistrationModel.campaign_id == CampaignModel.id
    ).filter(
        RegistrationModel.user_id == current_user.id
    ).order_by(
        RegistrationModel.id.desc()
    ).all()

    return [
        {
            "id": r.id,
            "campaign_id": r.campaign_id,
            "campaign_title": r.campaign.title if r.campaign else f"Chiến dịch #{r.campaign_id}",
            "status": r.status,
            "message": r.message,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at
        }
        for r in regs
    ]


@router.post("/", response_model=RegistrationResponse)
def register_campaign(
    data: RegistrationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("USER"))
):
    return create_registration(
        db,
        current_user.id,
        data.campaign_id,
        data.message
    )

@router.patch("/{registration_id}/cancel", response_model=RegistrationResponse)
def cancel_registration_api(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return cancel_registration(
        db=db,
        registration_id=registration_id,
        user_id=current_user.id
    )

@router.get("/campaign/{campaign_id}")
def list_campaign_registration(
    campaign_id : int,
    status: str = Query(
        None,
        description="PENDING, APPROVED, REJECTED, CANCELLED"
    ),
    db: Session = Depends(get_db),
    current_user = Depends(require_role("ORGANIZER"))
):
    verify_campaign_owner(db, campaign_id, current_user.id)
    return get_campaign_registrations(
        db=db,
        campaign_id= campaign_id,
        status= status
    )

@router.patch("/{registration_id}/approve")
def approve_registration_api(
    registration_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ORGANIZER"))
):
    verify_campaign_owner(db, campaign_id, current_user.id)
    return approve_registration(
        db=db,
        registration_id=registration_id,
        campaign_id=campaign_id
    )

@router.patch("/{registration_id}/reject")
def reject_registration_api(
    registration_id: int,
    campaign_id: int,
    request: RejectRegistrationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ORGANIZER"))
):
    verify_campaign_owner(db, campaign_id, current_user.id)
    return reject_registration(
        db=db,
        registration_id=registration_id,
        campaign_id=campaign_id,
        reason=request.reason
    )