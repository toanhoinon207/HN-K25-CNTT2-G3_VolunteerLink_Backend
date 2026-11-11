from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.schemas.registration import RegistrationCreate
from app.services.registrations import create_registration
from app.models.users import UserModel
from app.services.registrations import cancel_registration
router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"]
)


@router.post("/")
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

@router.patch("/{registration_id}/cancel")
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
