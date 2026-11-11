
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.schemas.campaigns import CampaignCreate, CampaignUpdate


def get_approved_organization(db: Session, user_id: int):
    organization = db.query(OrganizationModel).filter(
        OrganizationModel.owner_id == user_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=403,
            detail="Bạn chưa sở hữu tổ chức nào"
        )

    if organization.status != OrganizationStatus.APPROVED:
        raise HTTPException(
            status_code=403,
            detail="Tổ chức chưa được phê duyệt"
        )

    return organization


def validate_campaign(data: dict):
    start = data["start_time"]
    end = data["end_time"]
    deadline = data["registration_deadline"]

    if end <= start:
        raise HTTPException(
            status_code=422,
            detail="Thời gian kết thúc phải sau thời gian bắt đầu"
        )

    if deadline >= start:
        raise HTTPException(
            status_code=422,
            detail="Hạn đăng ký phải trước thời gian bắt đầu"
        )

    if data["max_participants"] <= 0:
        raise HTTPException(
            status_code=422,
            detail="Số lượng tối đa phải lớn hơn 0"
        )


def get_owned_draft(
    db: Session,
    campaign_id: int,
    organization_id: int
):
    campaign = db.query(CampaignModel).filter(
        CampaignModel.id == campaign_id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy chiến dịch"
        )

    if campaign.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền quản lý chiến dịch này"
        )

    if campaign.status != "DRAFT":
        raise HTTPException(
            status_code=409,
            detail="Chỉ được thao tác với chiến dịch DRAFT"
        )

    return campaign


def create_campaign(
    db: Session,
    data: CampaignCreate,
    current_user: UserModel
):
    organization = get_approved_organization(
        db, current_user.id
    )

    payload = data.model_dump(
        exclude={"organization_id"}
    )

    validate_campaign(payload)

    campaign = CampaignModel(
        **payload,
        organization_id=organization.id,
        status="DRAFT"
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return campaign


def update_campaign(
    db: Session,
    campaign_id: int,
    data: CampaignUpdate,
    current_user: UserModel
):
    organization = get_approved_organization(
        db, current_user.id
    )

    campaign = get_owned_draft(
        db, campaign_id, organization.id
    )

    updates = data.model_dump(exclude_unset=True)

    merged = {
        column.name: getattr(campaign, column.name)
        for column in CampaignModel.__table__.columns
    }
    merged.update(updates)

    validate_campaign(merged)

    approved_count = db.query(
        func.count(RegistrationModel.id)
    ).filter(
        RegistrationModel.campaign_id == campaign_id,
        RegistrationModel.status == "APPROVED"
    ).scalar()

    if merged["max_participants"] < approved_count:
        raise HTTPException(
            status_code=409,
            detail=(
                "Số lượng tối đa không được nhỏ hơn "
                "số tình nguyện viên đã duyệt"
            )
        )

    for field, value in updates.items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)

    return campaign


def submit_campaign(
    db: Session,
    campaign_id: int,
    current_user: UserModel
):
    organization = get_approved_organization(
        db, current_user.id
    )

    campaign = get_owned_draft(
        db, campaign_id, organization.id
    )

    data = {
        column.name: getattr(campaign, column.name)
        for column in CampaignModel.__table__.columns
    }

    validate_campaign(data)

    campaign.status = "PENDING"
    campaign.reason = None

    db.commit()
    db.refresh(campaign)

    return campaign
