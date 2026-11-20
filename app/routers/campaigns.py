
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.users import UserModel

from app.schemas.campaigns import (
    CampaignCancelRequest,
    CampaignCreate,
    CampaignDetailResponse,
    CampaignListItemResponse,
    CampaignListResponse,
    CampaignPendingItemResponse,
    CampaignResponse,
    CampaignReviewRequest,
    CampaignUpdate,
    OrganizerCampaignResponse,
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


@router.patch(
    "/{campaign_id}/cancel",
    response_model=CampaignResponse
)
def cancel_campaign(
    campaign_id: int,
    data: CampaignCancelRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):
    return campaign_service.cancel_campaign(
        db, campaign_id, data, current_user
    )


@router.get(
    "",
    response_model=CampaignListResponse
)
def list_public_campaigns(
    keyword: str | None = None,
    category: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=6, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return campaign_service.get_public_campaigns(
        db=db,
        keyword=keyword,
        category=category,
        sort=sort,
        page=page,
        page_size=page_size
    )

@router.get(
    "/mine",
    response_model=list[OrganizerCampaignResponse]
)
def list_my_campaigns(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):
    return campaign_service.get_organizer_campaigns(db, current_user)


@router.get(
    "/featured",
    response_model=list[CampaignListItemResponse]
)
def list_featured_campaigns(
    limit: int = Query(default=6, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return campaign_service.get_featured_campaigns(
        db=db,
        limit=limit
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


admin_router = APIRouter(
    prefix="/admin/campaigns",
    tags=["Admin Campaigns"]
)


@admin_router.get(
    "/pending",
    response_model=list[CampaignPendingItemResponse]
)
def list_pending_campaigns(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    return campaign_service.get_pending_campaigns(db)


@admin_router.patch(
    "/{campaign_id}/review",
    response_model=CampaignResponse
)
def review_campaign(
    campaign_id: int,
    data: CampaignReviewRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    return campaign_service.review_campaign(db, campaign_id, data)


