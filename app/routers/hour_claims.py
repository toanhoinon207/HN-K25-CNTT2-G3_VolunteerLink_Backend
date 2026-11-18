from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel

from app.dependencies.auth import require_role, get_current_user

from app.schemas.hourclaims import (
    HourClaimCreate,
    HourClaimReview,
    HourClaimAppealCreate,
    HourClaimAppealReview,
    HourClaimResponse
)

from app.services.hour_claim_service import (
    create_hour_claim,
    get_hour_claims,
    get_hour_claim_detail,
    review_hour_claim,
    create_hour_claim_appeal,
    review_hour_claim_appeal
)


router = APIRouter(
    prefix="/hour-claims",
    tags=["Hour Claims"]
)


# =====================================================
# 1. TNV: TẠO YÊU CẦU
# POST /hour-claims
# =====================================================

@router.post(
    "",
    response_model=HourClaimResponse,
    status_code=status.HTTP_201_CREATED
)
def create_claim(
    data: HourClaimCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER"))
):

    return create_hour_claim(
        db,
        data,
        current_user
    )


# =====================================================
# 2. LẤY DANH SÁCH YÊU CẦU
# GET /hour-claims
# =====================================================

@router.get(
    "",
    response_model=list[HourClaimResponse]
)
def list_claims(
    claim_status: Optional[str] = None,
    appeal_status: Optional[str] = None,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    return get_hour_claims(
        db,
        current_user,
        claim_status,
        appeal_status
    )


# =====================================================
# 3. LẤY CHI TIẾT YÊU CẦU
# GET /hour-claims/{claim_id}
# =====================================================

@router.get(
    "/{claim_id}",
    response_model=HourClaimResponse
)
def get_claim_detail(
    claim_id: int,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    return get_hour_claim_detail(
        db,
        claim_id,
        current_user
    )


# =====================================================
# 4. ORGANIZER: DUYỆT / TỪ CHỐI
# PATCH /hour-claims/{claim_id}/review
# =====================================================

@router.patch(
    "/{claim_id}/review",
    response_model=HourClaimResponse
)
def review_claim(
    claim_id: int,
    data: HourClaimReview,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ORGANIZER")
    )
):

    return review_hour_claim(
        db,
        claim_id,
        data,
        current_user
    )


# =====================================================
# 5. TNV: GỬI KHIẾU NẠI
# POST /hour-claims/{claim_id}/appeals
# =====================================================

@router.post(
    "/{claim_id}/appeals",
    response_model=HourClaimResponse,
    status_code=status.HTTP_201_CREATED
)
def create_appeal(
    claim_id: int,
    data: HourClaimAppealCreate,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("USER")
    )
):

    return create_hour_claim_appeal(
        db,
        claim_id,
        data,
        current_user
    )


# =====================================================
# 6. ADMIN: XỬ LÝ KHIẾU NẠI
# PATCH /hour-claims/{claim_id}/appeal-review
# =====================================================

@router.patch(
    "/{claim_id}/appeal-review",
    response_model=HourClaimResponse
)
def review_appeal(
    claim_id: int,
    data: HourClaimAppealReview,

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role("ADMIN")
    )
):

    return review_hour_claim_appeal(
        db,
        claim_id,
        data,
        current_user
    ) 