"""Auto-seed dữ liệu mẫu VolunteerLink khi server khởi động.

Ủy quyền trực tiếp cho `seed_all.run_all_seeds(db)` để dùng chung bộ seed từng file
(với mật khẩu chung 12345678 và hash bcrypt riêng cho từng tài khoản).
"""
from app.db.session import SessionLocal


def run_seed():
    try:
        from seed_all import run_all_seeds
    except ModuleNotFoundError as exc:
        if exc.name != "seed_all":
            raise
        print("[SEED] Không có seed_all.py, bỏ qua nạp dữ liệu mẫu.")
        return
    db = SessionLocal()
    try:
        run_all_seeds(db)
    except Exception as e:
        db.rollback()
        print(f"[SEED] Lỗi khi auto-seed: {e}")
        raise
    finally:
        db.close()
