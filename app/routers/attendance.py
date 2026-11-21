from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
from app.dependencies.auth import require_role, get_current_user
from app.schemas.attendance_codes import (
    AttendanceCodeCreate,
    AttendanceCodeResponse,
    AttendanceCheckRequest
)
from app.schemas.attendances import AttendanceListItem, AttendanceResponse, AttendanceStatusUpdate, AttendanceTimeUpdate, ManualAttendanceCreate
from app.services.attendances import (
    create_attendance_code,
    check_in,
    check_out,
    get_campaign_attendances,
    get_my_attendance_history as get_my_attendance_history_service,
    manual_attendance,
    update_attendance_status,
    update_attendance_time
)



router = APIRouter(
    prefix="/attendances",
    tags=["Attendances"]
)


@router.get("/my-history")
def get_my_attendance_history(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Lấy lịch sử điểm danh mới nhất của người dùng hiện tại từ Database."""
    return get_my_attendance_history_service(db, current_user.id)


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
@router.get(
    "/campaigns/{campaign_id}",
    response_model=list[AttendanceListItem]
)
def get_attendances_by_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER"))
):
    return get_campaign_attendances(
        db,
        campaign_id,
        current_user
    )


@router.post(
    "/campaigns/{campaign_id}/manual",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_manual_attendance(
    campaign_id: int,
    data: ManualAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER"))
):
    return manual_attendance(
        db,
        campaign_id,
        data,
        current_user
    )


@router.patch(
    "/{attendance_id}/status",
    response_model=AttendanceResponse
)
def change_attendance_status(
    attendance_id: int,
    data: AttendanceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER"))
):
    return update_attendance_status(
        db,
        attendance_id,
        data,
        current_user
    )


@router.patch(
    "/{attendance_id}/time",
    response_model=AttendanceResponse
)
def change_attendance_time(
    attendance_id: int,
    data: AttendanceTimeUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER"))
):
    return update_attendance_time(
        db,
        attendance_id,
        data,
        current_user
    )
