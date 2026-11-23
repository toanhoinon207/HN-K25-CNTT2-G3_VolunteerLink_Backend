from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.users import UserModel
from app.dependencies.auth import require_role
from app.schemas.attendance_appeals import (
    AttendanceAppealAdminReview,
    AttendanceAppealCreate,
    AttendanceAppealEscalate,
    AttendanceAppealResponse,
    AttendanceAppealReview,
)
from app.services.attendance_appeals import (
    admin_appeals,
    admin_review_appeal,
    create_appeal,
    escalate_appeal,
    my_appeals,
    organizer_appeals,
    review_appeal,
)

router = APIRouter(prefix="/attendance-appeals", tags=["Attendance appeals"])

@router.post("", response_model=AttendanceAppealResponse, status_code=201)
def submit(data: AttendanceAppealCreate, db: Session = Depends(get_db), user: UserModel = Depends(require_role("USER"))):
    return create_appeal(db, data, user)

@router.get("/me", response_model=list[AttendanceAppealResponse])
def mine(db: Session = Depends(get_db), user: UserModel = Depends(require_role("USER"))):
    return my_appeals(db, user)

@router.get("/organizer", response_model=list[AttendanceAppealResponse])
def organizer_list(campaign_id: int | None = Query(default=None), db: Session = Depends(get_db), user: UserModel = Depends(require_role("ORGANIZER"))):
    return organizer_appeals(db, user, campaign_id)

@router.patch("/{appeal_id}/review", response_model=AttendanceAppealResponse)
def review(appeal_id: int, data: AttendanceAppealReview, db: Session = Depends(get_db), user: UserModel = Depends(require_role("ORGANIZER"))):
    return review_appeal(db, appeal_id, data, user)


@router.post("/{appeal_id}/escalate", response_model=AttendanceAppealResponse)
def escalate(appeal_id: int, data: AttendanceAppealEscalate, db: Session = Depends(get_db), user: UserModel = Depends(require_role("USER"))):
    return escalate_appeal(db, appeal_id, data, user)


@router.get("/admin", response_model=list[AttendanceAppealResponse])
def admin_list(status: str | None = Query(default=None), db: Session = Depends(get_db), user: UserModel = Depends(require_role("ADMIN"))):
    return admin_appeals(db, status)


@router.patch("/{appeal_id}/admin-review", response_model=AttendanceAppealResponse)
def admin_review(appeal_id: int, data: AttendanceAppealAdminReview, db: Session = Depends(get_db), user: UserModel = Depends(require_role("ADMIN"))):
    return admin_review_appeal(db, appeal_id, data, user)
