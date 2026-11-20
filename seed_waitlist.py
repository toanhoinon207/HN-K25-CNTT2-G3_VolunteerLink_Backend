"""Script seed dữ liệu mẫu cho waitlist_entries.

Chạy: python seed_waitlist.py
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.registration import RegistrationModel
from app.models.waitlist_entry import WaitlistEntryModel


def seed_waitlist(db: Session):
    waitlisted_regs = (
        db.query(RegistrationModel)
        .filter(RegistrationModel.status == "WAITLISTED")
        .order_by(RegistrationModel.campaign_id, RegistrationModel.id)
        .all()
    )

    if not waitlisted_regs:
        print("[!] Không có registration nào ở trạng thái WAITLISTED. Chạy `python seed_registration.py` trước.")
        return

    now = datetime.now().replace(microsecond=0)
    created = 0
    skipped = 0
    position_counter: dict[int, int] = {}

    for reg in waitlisted_regs:
        existing = db.query(WaitlistEntryModel).filter(
            WaitlistEntryModel.user_id == reg.user_id,
            WaitlistEntryModel.campaign_id == reg.campaign_id,
        ).first()
        if existing:
            skipped += 1
            continue

        pos = position_counter.get(reg.campaign_id, 0) + 1
        position_counter[reg.campaign_id] = pos

        # Vị trí #1 đặt trạng thái INVITED để test luồng phản hồi lời mời, các vị trí sau WAITING
        if pos == 1:
            entry = WaitlistEntryModel(
                user_id=reg.user_id,
                campaign_id=reg.campaign_id,
                position=pos,
                status="INVITED",
                invited_at=now - timedelta(hours=2),
                response_deadline=now + timedelta(hours=22),
                responded_at=None,
            )
        else:
            entry = WaitlistEntryModel(
                user_id=reg.user_id,
                campaign_id=reg.campaign_id,
                position=pos,
                status="WAITING",
            )

        db.add(entry)
        created += 1
        print(f"  [+] Waitlist campaign_id={reg.campaign_id}, user_id={reg.user_id}, pos={pos}, status={entry.status}")

    db.commit()
    print("\n========== SEED WAITLIST ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_waitlist(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
