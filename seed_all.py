"""Script chạy toàn bộ các file seed lẻ theo đúng thứ tự phụ thuộc.

Chạy: python seed_all.py
Hoặc chạy từng file riêng lẻ theo thứ tự:
  1. python seed_user.py
  2. python seed_volunteer_profile.py
  3. python seed.organizer.py
  4. python seed_campaign.py
  5. python seed_registration.py
  6. python seed_waitlist.py
  7. python seed_attendance.py
  8. python seed_hour_claim.py
  9. python seed_certificate.py
 10. python seed_notification.py
"""
import importlib.util
from pathlib import Path

from app.db.session import SessionLocal

SEED_STEPS = [
    ("seed_user.py", "seed_users"),
    ("seed_volunteer_profile.py", "seed_volunteer_profiles"),
    ("seed.organizer.py", "seed_organizations"),
    ("seed_campaign.py", "seed_campaigns"),
    ("seed_registration.py", "seed_registrations"),
    ("seed_waitlist.py", "seed_waitlist"),
    ("seed_attendance.py", "seed_attendance_data"),
    ("seed_hour_claim.py", "seed_hour_claims"),
    ("seed_certificate.py", "seed_certificates"),
    ("seed_notification.py", "seed_notifications"),
]


def _load_module(file_path: Path):
    spec = importlib.util.spec_from_file_location(file_path.stem.replace(".", "_"), file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Không thể load module từ {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_all_seeds(db):
    base_dir = Path(__file__).resolve().parent
    for filename, func_name in SEED_STEPS:
        file_path = base_dir / filename
        print(f"\n>>> Đang chạy {filename} ({func_name})...")
        module = _load_module(file_path)
        seed_fn = getattr(module, func_name)
        seed_fn(db)


def main():
    db = SessionLocal()
    try:
        run_all_seeds(db)
        print("\n==========================================")
        print("HOÀN TẤT TOÀN BỘ SEED DỮ LIỆU!")
        print("==========================================")
    except Exception as e:
        db.rollback()
        print(f"\n[X] Lỗi khi chạy seed_all: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
