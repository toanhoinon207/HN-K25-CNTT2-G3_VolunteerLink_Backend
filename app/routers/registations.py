from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.schemas.registration import RegistrationCreate, RegistrationResponse
from app.services.registrations import create_registration, cancel_registration, get_campaign_registrations, reject_registration
from app.services.registrations import approve_registration
from app.schemas.registration import RejectRegistrationRequest

router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"]
)


@router.post("/", response_model=RegistrationResponse)
def register_campaign(
    data: RegistrationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
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
    current_user=Depends(get_current_user)
):
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
    current_user=Depends(get_current_user)
):
    return reject_registration(
        db=db,
        registration_id=registration_id,
        campaign_id=campaign_id,
        reason=request.reason
    )