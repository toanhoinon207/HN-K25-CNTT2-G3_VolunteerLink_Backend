
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
from app.schemas.users import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import register_user, login_user
from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    return register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(db, data)


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: UserModel = Depends(get_current_user)
):
    return current_user
