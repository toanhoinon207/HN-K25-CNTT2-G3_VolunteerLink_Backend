from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.users import UserModel
from app.dependencies.auth import require_role
from app.schemas.attendance_appeals import AttendanceAppealCreate, AttendanceAppealReview, AttendanceAppealResponse
from app.services.attendance_appeals import create_appeal, my_appeals, organizer_appeals, review_appeal

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
