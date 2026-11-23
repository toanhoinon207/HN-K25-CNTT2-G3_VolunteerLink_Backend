
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.users import UserModel
from app.schemas.users import UserCreate, UserResponse
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services.auth import (
    login_user,
    logout_user,
    refresh_user_token,
    register_user,
    request_password_reset,
    reset_password_with_token,
)
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
    data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, data)


@router.post("/login", response_model = TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, data)


@router.get("/me", response_model = UserResponse)
def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_user_token(db, data.refresh_token)


@router.post("/logout")
def logout(
    current_user: UserModel = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    return logout_user(db, credentials.credentials, current_user)


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return request_password_reset(db, str(data.email))


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return reset_password_with_token(db, data.token, data.new_password)
