"""Script seed dữ liệu mẫu cho certificates (ACTIVE và REVOKED).

Chạy: python seed_certificate.py
"""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.models.organizations import OrganizationModel  # noqa: F401
from app.db.session import SessionLocal
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.models.certificate import CertificateModel


def seed_certificates(db: Session):
    eligible_rows = (
        db.query(RegistrationModel, AttendanceModel, CampaignModel)
        .join(AttendanceModel, AttendanceModel.registration_id == RegistrationModel.id)
        .join(CampaignModel, RegistrationModel.campaign_id == CampaignModel.id)
        .filter(
            RegistrationModel.status == "APPROVED",
            CampaignModel.status == "COMPLETED",
            AttendanceModel.status == "PRESENT",
        )
        .order_by(RegistrationModel.id)
        .all()
    )

    if not eligible_rows:
        print("[!] Không có dữ liệu đủ điều kiện (APPROVED + COMPLETED + PRESENT). Chạy `seed_attendance.py` trước.")
        return

    now = datetime.now().replace(microsecond=0)
    created = 0
    skipped = 0

    for idx, (reg, att, campaign) in enumerate(eligible_rows):
        existing = db.query(CertificateModel).filter(
            CertificateModel.user_id == reg.user_id,
            CertificateModel.campaign_id == campaign.id,
        ).first()
        if existing:
            skipped += 1
            continue

        cert_code = f"VL-{now.year}-{campaign.id:03d}-{reg.user_id:04d}"
        total_hours = Decimal(str(round(att.total_minutes / 60.0, 2)))

        # Tạo 1 chứng chỉ REVOKED ở phần tử cuối (nếu có >= 3 bản ghi) để test trạng thái thu hồi
        is_revoked = (idx == len(eligible_rows) - 1 and len(eligible_rows) >= 3)

        cert = CertificateModel(
            certificate_code=cert_code,
            user_id=reg.user_id,
            campaign_id=campaign.id,
            total_hours=total_hours,
            issued_at=now - timedelta(days=2),
            status="REVOKED" if is_revoked else "ACTIVE",
            revoked_reason="Thu hồi do phát hiện sai lệch thông tin điểm danh." if is_revoked else None,
        )
        db.add(cert)
        created += 1
        print(f"  [+] Certificate {cert_code} | user_id={reg.user_id} | status={cert.status}")

    db.commit()
    print("\n========== SEED CERTIFICATES ==========")
    print(f"Đã tạo: {created} | Bỏ qua: {skipped}")


def main():
    db = SessionLocal()
    try:
        seed_certificates(db)
    except Exception as e:
        db.rollback()
        print(f"Seed thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
