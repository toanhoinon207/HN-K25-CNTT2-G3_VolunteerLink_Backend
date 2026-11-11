from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
from app.dependencies.auth import require_role
from app.schemas.attendance_codes import (
    AttendanceCodeCreate,
    AttendanceCodeResponse,
    AttendanceCheckRequest
)
from app.schemas.attendances import AttendanceResponse
from app.services.attendances import (
    create_attendance_code,
    check_in,
    check_out
)


router = APIRouter(
    prefix="/attendances",
    tags=["Attendances"]
)


@router.post(
    "/code",
    response_model=AttendanceCodeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_code(
    data: AttendanceCodeCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER"))
):
    return create_attendance_code(db, data, current_user)


@router.post("/check-in", response_model=AttendanceResponse)
def attendance_check_in(
    data: AttendanceCheckRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER"))
):
    return check_in(db, data, current_user)


@router.post("/check-out", response_model=AttendanceResponse)
def attendance_check_out(
    data: AttendanceCheckRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER"))
):
    return check_out(db, data, current_user) 