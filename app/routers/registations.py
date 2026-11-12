from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.schemas.registration import RegistrationCreate, RegistrationResponse
from app.services.registrations import create_registration, cancel_registration

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
