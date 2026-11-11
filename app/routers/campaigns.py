
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.users import UserModel

from app.schemas.campaigns import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse
)

from app.services import campaigns as campaign_service


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=201
)
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):
    return campaign_service.create_campaign(
        db, data, current_user
    )


@router.patch(
    "/{campaign_id}",
    response_model=CampaignResponse
)
def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):
    return campaign_service.update_campaign(
        db, campaign_id, data, current_user
    )


@router.post(
    "/{campaign_id}/submit",
    response_model=CampaignResponse
)
def submit_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):
    return campaign_service.submit_campaign(
        db, campaign_id, current_user
    )
