"""Auto-seed dữ liệu mẫu VolunteerLink khi server khởi động.

Đọc và thực thi bộ seed SQL duy nhất tại `sql/seed_all.sql` nếu bảng `users` chưa có dữ liệu.
"""
from pathlib import Path
from sqlalchemy import text

from app.db.session import SessionLocal


SEED_SQL_PATH = Path(__file__).resolve().parents[2] / "sql" / "seed_all.sql"


def _split_sql_statements(sql_content: str) -> list[str]:
    """Tách nội dung SQL thành từng câu lệnh thực thi, bỏ qua comment và lệnh điều khiển database."""
    lines = []
    for raw_line in sql_content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        lines.append(raw_line)

    cleaned = "\n".join(lines)
    statements: list[str] = []
    for chunk in cleaned.split(";"):
        stmt = chunk.strip()
        if not stmt:
            continue
        upper = stmt.upper()
        if upper.startswith("USE ") or upper in ("START TRANSACTION", "COMMIT"):
            continue
        statements.append(stmt)
    return statements


def run_seed():
    if not SEED_SQL_PATH.exists():
        print(f"[SEED] Không tìm thấy {SEED_SQL_PATH}, bỏ qua nạp dữ liệu mẫu.")
        return

    db = SessionLocal()
    try:
        existing_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        if existing_users > 0:
            print("[SEED] Database đã có dữ liệu users, bỏ qua auto-seed.")
            return

        sql_content = SEED_SQL_PATH.read_text(encoding="utf-8")
        statements = _split_sql_statements(sql_content)
        for stmt in statements:
            db.execute(text(stmt))
        db.commit()
        print("[SEED] Đã nạp dữ liệu mẫu từ sql/seed_all.sql thành công.")
    except Exception as e:
        db.rollback()
        print(f"[SEED] Lỗi khi auto-seed từ sql/seed_all.sql: {e}")
        raise
    finally:
        db.close()
