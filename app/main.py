
"""Điểm khởi động của backend.

Chạy: uvicorn app.main:app --reload
Tài liệu API: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app import models
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.services.waitlist import process_expired_invites
from app.services.campaigns import complete_expired_checkout_campaigns

# Import hàm seed dữ liệu
from app.db.seed import run_seed
from app.routers import health, items, auth, registations, attendance, campaigns, organizations, admin

from app.routers import (
    health,
    auth,
    admin,
    registations,
    attendance,
    campaigns,
    organizations,
    profile,
    notification,
    certificates,
    waitlist,
    hour_claims,
    attendance_appeals,
    admin_users,
    hour_claims
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 1. Tạo các bảng còn thiếu
        Base.metadata.create_all(bind=engine)

        print(
            f"[DB] Đã kết nối MySQL "
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        # 2. Tự động seed dữ liệu mẫu
        print("[SEED] Bắt đầu thêm dữ liệu mẫu...")
        run_seed()

    except OperationalError as error:
        print("[DB] KHÔNG kết nối được MySQL!")
        print("[DB] Kiểm tra MySQL và file .env")

        if "Unknown database" in str(error.orig):
            print("[DB] Chưa có database -> chạy sql/init.sql")

        print(f"[DB] Chi tiết: {error.orig}")
        raise

    # Kiểm tra định kỳ lời mời đã quá 24 giờ để mời người kế tiếp.
    async def expire_waitlist_invites():
        while True:
            await asyncio.sleep(30)
            def process_with_session():
                db = SessionLocal()
                try:
                    complete_expired_checkout_campaigns(db)
                    process_expired_invites(db)
                finally:
                    db.close()
            try:
                await asyncio.to_thread(process_with_session)
            except Exception:
                logging.exception("Lỗi tác vụ cập nhật campaign/waitlist")

    # Sau khi server khởi động lại, bắt kịp các mã CHECK-OUT đã hết hạn.
    with SessionLocal() as db:
        complete_expired_checkout_campaigns(db)
    expiry_task = asyncio.create_task(expire_waitlist_invites())
    try:
        yield
    finally:
        expiry_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
(UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(registations.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(campaigns.admin_router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(organizations.admin_router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(notification.router, prefix="/api")
app.include_router(certificates.router, prefix="/api")
app.include_router(waitlist.router, prefix="/api")
app.include_router(hour_claims.router, prefix="/api")
app.include_router(attendance_appeals.router, prefix="/api") 

@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"}
