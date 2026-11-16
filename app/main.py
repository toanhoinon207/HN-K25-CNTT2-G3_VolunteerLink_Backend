
"""Điểm khởi động của backend.

Chạy: uvicorn app.main:app --reload
Tài liệu API: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app import models
from app.core.config import settings
from app.db.session import Base, engine

# Import hàm seed dữ liệu
from app.db.seed import run_seed

from app.routers import (
    health,
    auth,
    registations,
    attendance,
    campaigns,
    organizations,
    profile
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

    yield


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

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(registations.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(organizations.admin_router, prefix="/api")
app.include_router(profile.router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"
    }
