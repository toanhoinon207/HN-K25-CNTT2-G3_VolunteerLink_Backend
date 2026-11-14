
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.users import UserModel

from app.schemas.campaigns import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignDetailResponse,
    CampaignListItemResponse
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


@router.get(
    "",
    response_model=CampaignListResponse
)
def list_public_campaigns(
    keyword: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=6, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return campaign_service.get_public_campaigns(
        db=db,
        keyword=keyword,
        category=category,
        page=page,
        page_size=page_size
    )

@router.get(
    "/featured",
    response_model=list[CampaignListItemResponse]
)
def list_featured_campaigns(
    db: Session = Depends(get_db)
):
    return campaign_service.get_featured_campaigns(
        db=db,
        limit=3
    )

@router.get(
    "/{campaign_id}",
    response_model=CampaignDetailResponse
)
def public_campaign_detail(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    return campaign_service.get_public_campaign_detail(
        db, campaign_id
    )


