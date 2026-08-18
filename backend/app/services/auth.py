from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserSettings
from app.schemas import LoginIn, RegisterIn


def register_user(db: Session, payload: RegisterIn) -> tuple[User, str]:
    exists = db.query(User).filter(User.username == payload.username).one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(
        UserSettings(
            user_id=user.id,
            llm_base_url=settings.default_llm_base_url,
            llm_model=settings.default_llm_model,
        )
    )
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.username)
    return user, token


def login_user(db: Session, payload: LoginIn) -> tuple[User, str]:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return user, create_access_token(user.id, user.username)


def touch_settings(row: UserSettings) -> None:
    row.updated_at = datetime.now(timezone.utc)
