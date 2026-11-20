from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.admin import AdminDashboardService

try:
    from app.core.security import get_current_user
except ImportError:
    from app.dependencies.auth import get_current_user  # type: ignore

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard/stats")
def get_admin_dashboard_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    role_raw = getattr(current_user, "role", "")
    role_val = role_raw.value if hasattr(role_raw, "value") else str(role_raw)

    if role_val.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới có quyền truy cập thống kê này."
        )

    try:
        stats = AdminDashboardService.get_admin_dashboard_stats(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "message": "Thành công",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )