
from fastapi import HTTPException
from datetime import timedelta
from uuid import uuid4
from jose import jwt
from app.core.config import settings
from app.models.auth_sessions import AuthSessionModel, now_utc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.users import UserModel
from app.schemas.users import UserCreate
from app.schemas.auth import LoginRequest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token
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

    sid = str(uuid4())
    token_data = {"sub": str(user.id), "sid": sid}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    refresh_payload = decode_refresh_token(refresh_token)

    session = AuthSessionModel(
        id=sid,
        user_id=user.id,
        refresh_token_jti=refresh_payload["jti"],
        expires_at=now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_user_token(db: Session, refresh_token: str):
    try:
        payload = decode_refresh_token(refresh_token)
        user_id = int(payload["sub"])
        sid = payload["sid"]
        jti = payload["jti"]
        if not isinstance(sid, str) or not isinstance(jti, str):
            raise ValueError("TOKEN_INVALID")
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Refresh Token không hợp lệ hoặc đã hết hạn")

    # Khóa dòng để hai yêu cầu refresh đồng thời không cùng dùng được token cũ.
    session = db.query(AuthSessionModel).filter(
        AuthSessionModel.id == sid,
        AuthSessionModel.user_id == user_id
    ).with_for_update().first()

    if session is None or session.revoked_at is not None or session.expires_at <= now_utc():
        db.rollback()
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không còn hiệu lực")

    if session.refresh_token_jti != jti:
        db.rollback()
        raise HTTPException(status_code=401, detail="Refresh Token đã được sử dụng hoặc thu hồi")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None or user.status != "ACTIVE":
        db.rollback()
        raise HTTPException(status_code=401, detail="Tài khoản không còn hoạt động")

    token_data = {"sub": str(user.id), "sid": sid}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    session.refresh_token_jti = decode_refresh_token(new_refresh_token)["jti"]
    session.expires_at = now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


def logout_user(db: Session, access_token: str, current_user: UserModel):
    from app.core.security import decode_access_token
    payload = decode_access_token(access_token)
    sid = payload.get("sid")
    # UPDATE có điều kiện để việc thu hồi phiên là thao tác duy nhất.
    count = db.query(AuthSessionModel).filter(
        AuthSessionModel.id == sid,
        AuthSessionModel.user_id == current_user.id,
        AuthSessionModel.revoked_at.is_(None)
    ).update({AuthSessionModel.revoked_at: now_utc()}, synchronize_session=False)
    db.commit()
    if not count:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không còn hiệu lực")
    return {"message": "Đăng xuất thành công"}
