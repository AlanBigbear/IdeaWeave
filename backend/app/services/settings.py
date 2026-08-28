from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.chains.llm import normalize_openai_base_url
from app.core.config import settings
from app.models import User, UserSettings
from app.schemas import SettingsIn, SettingsOut
from app.services.auth import touch_settings
from app.services.secrets_store import get_api_key, get_effective_api_key


def get_settings(db: Session, user: User) -> SettingsOut:
    from app.services.trial import is_trial_user

    row = db.query(UserSettings).filter(UserSettings.user_id == user.id).one_or_none()
    if row is None:
        row = UserSettings(
            user_id=user.id,
            llm_base_url=settings.default_llm_base_url,
            llm_model=settings.default_llm_model,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    if not (row.llm_api_key or "").strip():
        legacy = "" if is_trial_user(user) else get_api_key(user.id)
        if legacy:
            row.llm_api_key = legacy
            db.commit()
    return SettingsOut(
        llm_base_url=row.llm_base_url,
        llm_model=row.llm_model,
        has_api_key=bool(
            settings.default_llm_api_key
            if is_trial_user(user)
            else get_effective_api_key(user.id, row.llm_api_key)
        ),
        default_llm_base_url=settings.default_llm_base_url,
        default_llm_model=settings.default_llm_model,
    )


def update_settings(db: Session, user: User, payload: SettingsIn) -> SettingsOut:
    from app.services.trial import is_trial_user

    if is_trial_user(user):
        raise HTTPException(status_code=403, detail="公共试用空间使用服务端模型配置，不能修改 API Key 或模型地址")
    row = db.query(UserSettings).filter(UserSettings.user_id == user.id).one_or_none()
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
    row.llm_base_url = normalize_openai_base_url(payload.llm_base_url) or settings.default_llm_base_url
    row.llm_model = payload.llm_model.strip() or settings.default_llm_model
    touch_settings(row)
    if payload.llm_api_key is not None:
        row.llm_api_key = payload.llm_api_key.strip()
    db.commit()
    return get_settings(db, user)
