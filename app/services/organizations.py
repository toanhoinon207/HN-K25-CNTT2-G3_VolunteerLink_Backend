
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organizations import OrganizationModel, OrganizationStatus
from app.schemas.organizations import OrganizationCreate, OrganizationUpdate


def get_organization_by_owner(db: Session, owner_id: int):
    return db.query(OrganizationModel).filter(
        OrganizationModel.owner_id == owner_id
    ).first()


def get_organization_by_email(db: Session, email: str):
    return db.query(OrganizationModel).filter(
        OrganizationModel.email == email
    ).first()


def create_organization_service(
    db: Session,
    payload: OrganizationCreate,
    owner_id: int
):
    existing_org = get_organization_by_owner(db, owner_id)

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi tài khoản chỉ được phép đăng ký tối đa một tổ chức."
        )

    email_exist = get_organization_by_email(db, payload.email)

    if email_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email của tổ chức này đã được sử dụng."
        )

    db_org = OrganizationModel(
        name=payload.name,
        description=payload.description,
        logo_url=payload.logo_url,
        address=payload.address,
        email=payload.email,
        phone=payload.phone,
        document_url=payload.document_url,
        status=OrganizationStatus.PENDING,
        owner_id=owner_id
    )

    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    return db_org


def get_my_organization_service(
    db: Session,
    owner_id: int
):
    org = get_organization_by_owner(db, owner_id)

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
    org = get_organization_by_owner(db, owner_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tổ chức của bạn."
        )

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(org, key, value)

    if org.status == OrganizationStatus.REJECTED:
        org.status = OrganizationStatus.PENDING
        org.rejection_reason = None

    db.commit()
    db.refresh(org)

    return org
