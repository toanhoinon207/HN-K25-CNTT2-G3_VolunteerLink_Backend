from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.waitlist_entry import WaitlistEntryModel
from app.services.notifications import create_notification


def now_vietnam():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)


def approved_count(db: Session, campaign_id: int) -> int:
    return db.query(RegistrationModel).filter(
        RegistrationModel.campaign_id == campaign_id,
        RegistrationModel.status == "APPROVED",
    ).count()


def active_invite_count(db: Session, campaign_id: int) -> int:
    # Lời mời đang chờ cũng giữ chỗ để đơn khác không chiếm mất chỗ đó.
    return db.query(WaitlistEntryModel).filter(
        WaitlistEntryModel.campaign_id == campaign_id,
        WaitlistEntryModel.status == "INVITED",
        WaitlistEntryModel.response_deadline > now_vietnam(),
    ).count()


def _invite_next(db: Session, campaign: CampaignModel):
    """Mời đúng người đầu hàng khi chiến dịch còn chỗ."""
    now = now_vietnam()
    if campaign.status != "OPEN" or campaign.registration_deadline <= now:
        return None
    if approved_count(db, campaign.id) + active_invite_count(db, campaign.id) >= campaign.max_participants:
        return None

    entry = db.query(WaitlistEntryModel).filter(
        WaitlistEntryModel.campaign_id == campaign.id,
        WaitlistEntryModel.status == "WAITING",
    ).order_by(WaitlistEntryModel.position, WaitlistEntryModel.id).with_for_update().first()
    if entry is None:
        return None

    entry.status = "INVITED"
    entry.invited_at = now
    entry.response_deadline = now + timedelta(hours=24)
    entry.updated_at = now
    create_notification(
        db=db,
        user_id=entry.user_id,
        title="Bạn được mời từ danh sách chờ",
        content=f'Chiến dịch "{campaign.title}" đã có chỗ. Vui lòng phản hồi lời mời trong vòng 24 giờ.',
        link=f"/campaigns/{campaign.id}",
    )
    return entry


def add_to_waitlist(db: Session, user_id: int, campaign_id: int):
    """Thêm người đăng ký sau cùng vào hàng chờ FIFO."""
    campaign = db.query(CampaignModel).filter_by(id=campaign_id).with_for_update().first()
    if campaign is None:
        raise HTTPException(404, "Không tìm thấy chiến dịch")

    existing = db.query(WaitlistEntryModel).filter_by(
        user_id=user_id, campaign_id=campaign_id
    ).first()
    if existing and existing.status in ("WAITING", "INVITED"):
        return existing

    last_position = db.query(WaitlistEntryModel.position).filter_by(
        campaign_id=campaign_id
    ).order_by(WaitlistEntryModel.position.desc()).first()
    position = (last_position[0] if last_position else 0) + 1

    if existing:
        existing.position = position
        existing.status = "WAITING"
        existing.invited_at = None
        existing.response_deadline = None
        existing.responded_at = None
        entry = existing
    else:
        entry = WaitlistEntryModel(
            user_id=user_id, campaign_id=campaign_id, position=position, status="WAITING"
        )
        db.add(entry)
    db.flush()
    return entry


def list_campaign_waitlist(db: Session, campaign_id: int):
    return db.query(WaitlistEntryModel).filter_by(campaign_id=campaign_id).order_by(
        WaitlistEntryModel.position, WaitlistEntryModel.id
    ).all()


def respond_to_invite(db: Session, waitlist_id: int, user_id: int, response: str):
    entry = db.query(WaitlistEntryModel).filter_by(id=waitlist_id).first()
    if entry is None:
        raise HTTPException(404, "Không tìm thấy lời mời")

    campaign = db.query(CampaignModel).filter_by(
        id=entry.campaign_id
    ).with_for_update().first()
    entry = db.query(WaitlistEntryModel).filter_by(id=waitlist_id).with_for_update().first()
    if entry.user_id != user_id:
        raise HTTPException(403, "Bạn không có quyền phản hồi lời mời này")
    if entry.status != "INVITED":
        raise HTTPException(400, "Lời mời không còn chờ phản hồi")

    now = now_vietnam()
    if entry.response_deadline is None or entry.response_deadline <= now:
        entry.status = "EXPIRED"
        entry.responded_at = now
        entry.updated_at = now
        _invite_next(db, campaign)
        db.commit()
        raise HTTPException(400, "Lời mời đã hết hạn; người tiếp theo đã được mời nếu còn chỗ")

    if response == "DECLINED":
        entry.status = "DECLINED"
        entry.responded_at = now
        entry.updated_at = now
        _invite_next(db, campaign)
    else:
        if approved_count(db, campaign.id) >= campaign.max_participants:
            raise HTTPException(409, "Chiến dịch đã đủ số lượng")
        registration = db.query(RegistrationModel).filter_by(
            user_id=user_id, campaign_id=campaign.id
        ).with_for_update().first()
        if registration is None:
            registration = RegistrationModel(
                user_id=user_id, campaign_id=campaign.id, status="APPROVED"
            )
            db.add(registration)
        else:
            registration.status = "APPROVED"
            registration.rejection_reason = None
        entry.status = "ACCEPTED"
        entry.responded_at = now
        entry.updated_at = now
        create_notification(
            db, user_id, "Đăng ký chiến dịch được duyệt",
            f'Đăng ký tham gia chiến dịch "{campaign.title}" đã được duyệt.',
            f"/campaigns/{campaign.id}",
        )

    db.commit()
    db.refresh(entry)
    return entry


def process_expired_invites(db: Session):
    """Chạy định kỳ để hết hạn lời mời và chuyển lượt mời tiếp theo."""
    now = now_vietnam()
    campaign_ids = db.query(WaitlistEntryModel.campaign_id).filter(
        WaitlistEntryModel.status == "INVITED",
        WaitlistEntryModel.response_deadline <= now,
    ).distinct().all()
    processed = 0
    for (campaign_id,) in campaign_ids:
        campaign = db.query(CampaignModel).filter_by(id=campaign_id).with_for_update().first()
        if campaign is None:
            continue
        entry = db.query(WaitlistEntryModel).filter(
            WaitlistEntryModel.campaign_id == campaign_id,
            WaitlistEntryModel.status == "INVITED",
            WaitlistEntryModel.response_deadline <= now,
        ).order_by(WaitlistEntryModel.position).with_for_update().first()
        if entry is None:
            db.rollback()
            continue
        entry.status = "EXPIRED"
        entry.responded_at = now
        entry.updated_at = now
        _invite_next(db, campaign)
        db.commit()
        processed += 1
    return {"processed": processed}


def promote_after_vacancy(db: Session, campaign_id: int):
    """Gọi khi có chỗ trống; caller quản lý commit giao dịch."""
    db.flush()
    campaign = db.query(CampaignModel).filter_by(id=campaign_id).with_for_update().first()
    if campaign is None:
        return None
    return _invite_next(db, campaign)
