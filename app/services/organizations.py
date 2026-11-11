
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.organizations import OrganizationCreate, OrganizationUpdate
from app.crud.organizations import (
    get_organization_by_email,
    get_organization_by_owner,
    create_organization,
    update_organization
)


def create_organization_service(
    db: Session,
    payload: OrganizationCreate,
    owner_id: int
):
    existing_org = get_organization_by_owner(db, owner_id=owner_id)

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi tài khoản chỉ được phép đăng ký tối đa một tổ chức."
        )

    email_exist = get_organization_by_email(db, email=payload.email)

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email của tổ chức này đã được sử dụng."
        )

    return create_organization(
        db=db,
        payload=payload,
        owner_id=owner_id
    )


def get_my_organization_service(
    db: Session,
    owner_id: int
):
    org = get_organization_by_owner(db, owner_id=owner_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bạn chưa đăng ký hồ sơ tổ chức nào."
        )

    return org


def update_my_organization_service(
    db: Session,
    payload: OrganizationUpdate,
    owner_id: int
):
    org = get_organization_by_owner(db, owner_id=owner_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tổ chức của bạn."
        )

    return update_organization(
        db=db,
        db_org=org,
        payload=payload
    )
