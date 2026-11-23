
from datetime import datetime
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, case

from app.models.campaigns import CampaignModel, now_vietnam
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.models.waitlist_entry import WaitlistEntryModel
from app.schemas.campaigns import (
    CampaignCancelRequest,
    CampaignCreate,
    CampaignReviewRequest,
    CampaignUpdate,
)
from app.services.notifications import create_notification, notify_active_admins


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


def get_organizer_campaigns(
    db: Session,
    current_user: UserModel,
):
    organization = get_approved_organization(db, current_user.id)

    campaigns = (
        db.query(CampaignModel)
        .filter(CampaignModel.organization_id == organization.id)
        .order_by(CampaignModel.created_at.desc(), CampaignModel.id.desc())
        .all()
    )
    if not campaigns:
        return []

    campaign_ids = [c.id for c in campaigns]
    counts_rows = (
        db.query(
            RegistrationModel.campaign_id,
            func.count(RegistrationModel.id),
        )
        .filter(
            RegistrationModel.campaign_id.in_(campaign_ids),
            RegistrationModel.status == "APPROVED",
        )
        .group_by(RegistrationModel.campaign_id)
        .all()
    )
    counts_map = {camp_id: count for camp_id, count in counts_rows}

    for camp in campaigns:
        setattr(camp, "registered_count", counts_map.get(camp.id, 0))

    return campaigns


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

    for dt_field in ("start_time", "end_time", "registration_deadline"):
        if dt_field in payload and payload[dt_field] is not None:
            payload[dt_field] = to_naive_vn(payload[dt_field])

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

    for dt_field in ("start_time", "end_time", "registration_deadline"):
        if dt_field in updates and updates[dt_field] is not None:
            updates[dt_field] = to_naive_vn(updates[dt_field])

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
    if to_naive_vn(campaign.registration_deadline) <= now_vietnam():
        raise HTTPException(
            status_code=422,
            detail="Hạn chót đăng ký phải nằm ở thời điểm tương lai khi gửi duyệt",
        )

    campaign.status = "PENDING"
    campaign.reason = None
    notify_active_admins(
        db, "Chiến dịch chờ kiểm duyệt",
        f'Chiến dịch "{campaign.title}" vừa được gửi duyệt.',
        "admin-dashboard.html?tab=campaigns",
    )

    db.commit()
    db.refresh(campaign)

    return campaign


def complete_expired_checkout_campaigns(db: Session) -> int:
    """Đánh dấu COMPLETED khi chiến dịch kết thúc hoặc mã CHECK_OUT hết hạn.

    Giữ quy tắc hiện có: mã CHECK_OUT cuối cùng hết hạn sẽ kết thúc
    chiến dịch. Bổ sung dự phòng theo end_time để các chiến dịch không
    từng cấp mã CHECK_OUT cũng không bị kẹt ở CLOSED vô thời hạn.
    Mã CHECK_IN cũ không thể tự kích hoạt việc hoàn thành.
    """
    now = now_vietnam()
    updated = (
        db.query(CampaignModel)
        .filter(
            CampaignModel.status.in_(["OPEN", "CLOSED"]),
            or_(
                CampaignModel.end_time <= now,
                and_(
                    CampaignModel.attendance_code_type == "CHECK_OUT",
                    CampaignModel.attendance_code_expires_at.isnot(None),
                    CampaignModel.attendance_code_expires_at <= now,
                ),
            ),
        )
        .update(
            {CampaignModel.status: "COMPLETED", CampaignModel.updated_at: now},
            synchronize_session=False,
        )
    )
    if updated:
        db.commit()
    return updated


def close_expired_campaigns(db: Session) -> int:
    """Đóng nhận đăng ký, KHÔNG kết thúc hoạt động/khóa điểm danh.

    OPEN -> CLOSED từ registration_deadline; CLOSED vẫn được điểm danh
    trong [start_time, end_time] theo validate_campaign_time().
    """
    now = now_vietnam()
    updated = (
        db.query(CampaignModel)
        .filter(
            CampaignModel.status == "OPEN",
            CampaignModel.registration_deadline <= now,
            CampaignModel.end_time > now,
        )
        .update(
            {
                CampaignModel.status: "CLOSED",
                CampaignModel.updated_at: now,
            },
            synchronize_session=False,
        )
    )
    if updated:
        db.commit()
    return updated


def sync_campaign_lifecycle(db: Session) -> tuple[int, int]:
    """Cập nhật vòng đời trong một lượt; không ghi đè COMPLETED/CANCELLED."""
    closed = close_expired_campaigns(db)
    completed = complete_expired_checkout_campaigns(db)
    return closed, completed


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
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                CampaignModel.title.ilike(pattern),
                CampaignModel.location.ilike(pattern),
            )
        )

    return query


def filter_campaigns(query, category: str | None, status: str | None = None):
    if category and category.strip():
        query = query.filter(
            CampaignModel.category == category.strip()
        )
    if status and status.strip():
        query = query.filter(
            CampaignModel.status == status.strip().upper()
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
    status: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 6
):
    close_expired_campaigns(db)
    query = get_public_campaign_query(db)
    query = search_campaigns(query, keyword)
    query = filter_campaigns(query, category, status)
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
    close_expired_campaigns(db)
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


ALLOWED_CAMPAIGN_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_CAMPAIGN_IMAGE_BYTES = 2 * 1024 * 1024
CAMPAIGN_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "campaigns"


def upload_campaign_image(file: UploadFile) -> dict:
    ext = ALLOWED_CAMPAIGN_IMAGE_TYPES.get((file.content_type or "").lower())
    if not ext:
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ định dạng ảnh JPG, PNG hoặc WEBP."
        )
    content = file.file.read(MAX_CAMPAIGN_IMAGE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="File ảnh rỗng.")
    if len(content) > MAX_CAMPAIGN_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Kích thước ảnh tối đa là 2MB.")
    is_valid_image = (
        (ext == ".jpg" and content.startswith(b"\xff\xd8\xff"))
        or (ext == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (ext == ".webp" and len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP")
    )
    if not is_valid_image:
        raise HTTPException(
            status_code=400,
            detail="Nội dung file không khớp định dạng ảnh JPG, PNG hoặc WEBP."
        )
    CAMPAIGN_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"campaign_{uuid.uuid4().hex}{ext}"
    (CAMPAIGN_UPLOAD_DIR / filename).write_bytes(content)
    return {"image_url": f"/uploads/campaigns/{filename}"}


def get_admin_campaign_detail(db: Session, campaign_id: int):
    campaign = (
        db.query(CampaignModel)
        .options(joinedload(CampaignModel.organization))
        .filter(CampaignModel.id == campaign_id)
        .first()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")
    approved_count = (
        db.query(func.count(RegistrationModel.id))
        .filter(
            RegistrationModel.campaign_id == campaign_id,
            RegistrationModel.status == "APPROVED",
        )
        .scalar()
    ) or 0
    campaign.approved_count = approved_count
    campaign.remaining_slots = max(campaign.max_participants - approved_count, 0)
    return campaign


def get_featured_campaigns(db: Session, limit: int = 3):
    close_expired_campaigns(db)
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


def get_pending_campaigns(db: Session):
    return (
        db.query(CampaignModel)
        .options(joinedload(CampaignModel.organization))
        .filter(CampaignModel.status == "PENDING")
        .order_by(CampaignModel.updated_at.asc(), CampaignModel.id.asc())
        .all()
    )


def review_campaign(
    db: Session,
    campaign_id: int,
    data: CampaignReviewRequest,
):
    campaign = (
        db.query(CampaignModel)
        .options(joinedload(CampaignModel.organization))
        .filter(CampaignModel.id == campaign_id)
        .with_for_update()
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

    if campaign.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Chỉ có thể kiểm duyệt chiến dịch đang ở trạng thái PENDING",
        )

    if data.action == "APPROVE":
        if campaign.registration_deadline <= now_vietnam():
            raise HTTPException(
                status_code=409,
                detail="Không thể duyệt chiến dịch đã quá hạn đăng ký",
            )
        campaign.status = "OPEN"
        campaign.reason = None
        if campaign.organization:
            create_notification(
                db=db,
                user_id=campaign.organization.owner_id,
                title="Chiến dịch đã được phê duyệt",
                content=f"Chiến dịch '{campaign.title}' đã được phê duyệt và mở đăng ký.",
                link=f"campaign_detail.html?id={campaign.id}",
            )
    else:
        reason = (data.reason or "").strip()
        if not reason:
            raise HTTPException(
                status_code=422,
                detail="Vui lòng nhập lý do từ chối chiến dịch",
            )
        campaign.status = "DRAFT"
        campaign.reason = reason
        if campaign.organization:
            create_notification(
                db=db,
                user_id=campaign.organization.owner_id,
                title="Chiến dịch bị từ chối",
                content=f"Chiến dịch '{campaign.title}' bị từ chối. Lý do: {reason}",
                link=f"campaign_detail.html?id={campaign.id}",
            )

    db.commit()
    db.refresh(campaign)
    return campaign


def cancel_campaign(
    db: Session,
    campaign_id: int,
    data: CampaignCancelRequest,
    current_user: UserModel,
):
    organization = get_approved_organization(db, current_user.id)

    campaign = (
        db.query(CampaignModel)
        .filter(CampaignModel.id == campaign_id)
        .with_for_update()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

    if campaign.organization_id != organization.id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền hủy chiến dịch này",
        )

    if campaign.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(
            status_code=409,
            detail="Không thể hủy chiến dịch đã hoàn thành hoặc đã bị hủy",
        )

    reason = data.reason.strip()
    if not reason:
        raise HTTPException(
            status_code=422,
            detail="Vui lòng nhập lý do hủy chiến dịch",
        )

    campaign.status = "CANCELLED"
    campaign.reason = reason

    active_registrations = (
        db.query(RegistrationModel)
        .filter(
            RegistrationModel.campaign_id == campaign.id,
            RegistrationModel.status.in_(["PENDING", "APPROVED", "WAITLISTED"]),
        )
        .all()
    )

    for registration in active_registrations:
        registration.status = "CANCELLED"
        create_notification(
            db=db,
            user_id=registration.user_id,
            title="Chiến dịch đã bị hủy",
            content=f"Chiến dịch '{campaign.title}' đã bị hủy. Lý do: {reason}",
            link=f"campaign_detail.html?id={campaign.id}",
        )

    db.query(WaitlistEntryModel).filter(
        WaitlistEntryModel.campaign_id == campaign.id,
        WaitlistEntryModel.status.in_(["WAITING", "INVITED"]),
    ).update({WaitlistEntryModel.status: "EXPIRED"}, synchronize_session=False)

    db.commit()
    db.refresh(campaign)
    return campaign


def complete_campaign_by_organizer(
    db: Session,
    campaign_id: int,
    current_user: UserModel,
):
    organization = get_approved_organization(db, current_user.id)
    campaign = (
        db.query(CampaignModel)
        .filter(CampaignModel.id == campaign_id)
        .with_for_update()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")
    if campaign.organization_id != organization.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hoàn thành chiến dịch này")
    if campaign.status not in ("OPEN", "CLOSED"):
        raise HTTPException(
            status_code=409,
            detail="Chỉ có thể hoàn thành chiến dịch đang ở trạng thái OPEN hoặc CLOSED",
        )
    now = now_vietnam()
    if campaign.start_time and now < campaign.start_time:
        raise HTTPException(
            status_code=409,
            detail="Không thể hoàn thành chiến dịch chưa bắt đầu diễn ra",
        )
    campaign.status = "COMPLETED"
    campaign.updated_at = now
    db.commit()
    db.refresh(campaign)
    return campaign


def derive_display_status(status, start_time, end_time, registration_deadline, now=None):
    """Presentation-only status; do not use for authorization."""
    now = now or now_vietnam()
    if status in ("DRAFT", "PENDING", "CANCELLED", "COMPLETED"):
        return status
    if now >= end_time:
        return "COMPLETED"
    if now >= start_time:
        return "IN_PROGRESS"
    if now >= registration_deadline or status == "CLOSED":
        return "REGISTRATION_CLOSED"
    return "REGISTRATION_OPEN"
