
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.users import UserModel
from app.schemas.users import UserCreate
from app.schemas.auth import LoginRequest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)


def register_user(db: Session, data: UserCreate):
    email = str(data.email).strip().lower()

    existing = db.query(UserModel).filter(
        UserModel.email == email
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email đã tồn tại"
        )

    user = UserModel(
        email=email,
        full_name=data.full_name.strip(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="USER",
        status="ACTIVE"
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email đã tồn tại"
        )

    db.refresh(user)
    return user


def login_user(db: Session, data: LoginRequest):
    email = str(data.email).strip().lower()

    user = db.query(UserModel).filter(
        UserModel.email == email
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Tài khoản đã bị khóa hoặc vô hiệu hóa"
        )

    token_data = {
        "sub": str(user.id)
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer"
    }
