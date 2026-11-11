
from sqlalchemy.orm import Session

from app.models import OrganizationModel, OrganizationStatus
from app.schemas.organizations import OrganizationCreate, OrganizationUpdate


def get_organization_by_owner(db: Session, owner_id: int):
    return db.query(OrganizationModel).filter(
        OrganizationModel.owner_id == owner_id
    ).first()


def get_organization_by_email(db: Session, email: str):
    return db.query(OrganizationModel).filter(
        OrganizationModel.email == email
    ).first()


def create_organization(
    db: Session,
    payload: OrganizationCreate,
    owner_id: int
):
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


def update_organization(
    db: Session,
    db_org: OrganizationModel,
    payload: OrganizationUpdate
):
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_org, key, value)

    if db_org.status == OrganizationStatus.REJECTED:
        db_org.status = OrganizationStatus.PENDING
        db_org.rejection_reason = None

    db.commit()
    db.refresh(db_org)

    return db_org
