
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
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
