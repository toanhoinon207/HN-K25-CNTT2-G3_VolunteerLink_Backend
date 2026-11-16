
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, case

from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.schemas.campaigns import CampaignCreate, CampaignUpdate


def to_naive_vn(dt: datetime) -> datetime:
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    return dt


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
    start = to_naive_vn(data["start_time"])
    end = to_naive_vn(data["end_time"])
    deadline = to_naive_vn(data["registration_deadline"])

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

    updates = data.model_dump(exclude_unset=True, exclude_none=True)

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


def get_public_campaign_query(db: Session):
    return (
        db.query(CampaignModel)
        .join(CampaignModel.organization)
        .options(joinedload(CampaignModel.organization))
        .filter(
            CampaignModel.status.in_(
                ["OPEN", "CLOSED", "COMPLETED"]
            ),
            OrganizationModel.status
            == OrganizationStatus.APPROVED
        )
    )


def search_campaigns(query, keyword: str | None):
    if keyword and keyword.strip():
        query = query.filter(
            CampaignModel.title.ilike(
                f"%{keyword.strip()}%"
            )
        )

    return query


def filter_campaigns(query, category: str | None):
    if category and category.strip():
        query = query.filter(
            CampaignModel.category == category.strip()
        )

    return query


def sort_campaigns(query, sort: str | None = None):
    if sort == "oldest":
        return query.order_by(
            CampaignModel.updated_at.asc(),
            CampaignModel.id.asc()
        )
    if sort == "start_asc":
        return query.order_by(
            CampaignModel.start_time.asc(),
            CampaignModel.id.asc()
        )
    if sort == "deadline_asc":
        return query.order_by(
            CampaignModel.registration_deadline.asc(),
            CampaignModel.id.asc()
        )
    return query.order_by(
        CampaignModel.updated_at.desc(),
        CampaignModel.id.desc()
    )


def paginate_campaigns(query, page: int, page_size: int):
    offset = (page - 1) * page_size

    return query.offset(offset).limit(page_size)


def get_public_campaigns(
    db: Session,
    keyword: str | None = None,
    category: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 6
):
    query = get_public_campaign_query(db)
    query = search_campaigns(query, keyword)
    query = filter_campaigns(query, category)
    total = query.order_by(None).count()
    query = sort_campaigns(query, sort)
    query = paginate_campaigns(
        query, page, page_size
    )

    campaigns = query.all()

    return {
        "items": campaigns,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size
    }


def get_public_campaign_detail(
    db: Session,
    campaign_id: int
):
    campaign = (
        get_public_campaign_query(db)
        .filter(CampaignModel.id == campaign_id)
        .first()
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy chiến dịch công khai"
        )

    approved_count = (
        db.query(func.count(RegistrationModel.id))
        .filter(
            RegistrationModel.campaign_id == campaign_id,
            RegistrationModel.status == "APPROVED"
        )
        .scalar()
    ) or 0

    campaign.approved_count = approved_count

    campaign.remaining_slots = max(
        campaign.max_participants - approved_count,
        0
    )

    return campaign


def get_featured_campaigns(db: Session, limit: int = 3):
    now = datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)

    # Thống kê số đăng ký của mỗi chiến dịch
    stats = (
        db.query(
            RegistrationModel.campaign_id,
            func.count(RegistrationModel.id).label("total"),
            func.count(
                case(
                    (RegistrationModel.status == "APPROVED",
                     RegistrationModel.id)
                )
            ).label("approved")
        )
        .filter(
            RegistrationModel.status.in_(["PENDING", "APPROVED"])
        )
        .group_by(RegistrationModel.campaign_id)
        .subquery()
    )

    campaigns = (
        db.query(CampaignModel)
        .join(CampaignModel.organization)
        .outerjoin(
            stats,
            CampaignModel.id == stats.c.campaign_id
        )
        .filter(
            OrganizationModel.status == OrganizationStatus.APPROVED,
            CampaignModel.status == "OPEN",
            CampaignModel.registration_deadline > now,
            CampaignModel.start_time > now,
            CampaignModel.max_participants
                > func.coalesce(stats.c.approved, 0)
        )
        .order_by(
            func.coalesce(stats.c.total, 0).desc(),
            CampaignModel.start_time.asc(),
            CampaignModel.id.asc()
        )
        .limit(limit)
        .all()
    )

    return campaigns
