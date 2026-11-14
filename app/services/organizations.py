
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.users import UserModel
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

    if payload.email and payload.email != org.email:
        email_exist = get_organization_by_email(db, payload.email)

        if email_exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email của tổ chức này đã được sử dụng."
            )

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    update_data.pop("status", None)
    update_data.pop("rejection_reason", None)

    for key, value in update_data.items():
        setattr(org, key, value)

    if org.status == OrganizationStatus.REJECTED:
        org.status = OrganizationStatus.PENDING
        org.rejection_reason = None

    db.commit()
    db.refresh(org)

    return org


class OrganizationService:

    @staticmethod
    def get_pending_organizations(db: Session):
        """Lấy danh sách hồ sơ đang chờ duyệt."""

        return db.query(OrganizationModel).filter(
            OrganizationModel.status == OrganizationStatus.PENDING
        ).all()

    @staticmethod
    def review_organization(
        db: Session,
        org_id: int,
        action: str,
        reason: str | None = None
    ):
        

        org = db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).first()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin tổ chức."
            )

        if org.status != OrganizationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hồ sơ này đã được xử lý trước đó với trạng thái: {org.status}"
            )

        action = action.strip().upper()

        if action not in ["APPROVE", "REJECT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hành động không hợp lệ. Chỉ chấp nhận APPROVE hoặc REJECT."
            )

        user_owner = db.query(UserModel).filter(
            UserModel.id == org.owner_id
        ).first()

        if action == "APPROVE":
            org.status = OrganizationStatus.APPROVED

            if user_owner:
                user_owner.role = "ORGANIZER"

        elif action == "REJECT":
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bắt buộc phải nhập lý do khi từ chối hồ sơ."
                )

            org.status = OrganizationStatus.REJECTED
            org.rejection_reason = reason.strip()

        db.commit()
        db.refresh(org)

        if user_owner:
            db.refresh(user_owner)

        return org
