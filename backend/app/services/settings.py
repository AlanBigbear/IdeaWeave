from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserSettings
from app.schemas import SettingsIn, SettingsOut
from app.services.auth import touch_settings
from app.services.secrets_store import get_api_key, set_api_key


def get_settings(db: Session, user: User) -> SettingsOut:
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
    return SettingsOut(
        llm_base_url=row.llm_base_url,
        llm_model=row.llm_model,
        has_api_key=bool(get_api_key(user.id)),
        default_llm_base_url=settings.default_llm_base_url,
        default_llm_model=settings.default_llm_model,
    )


def update_settings(db: Session, user: User, payload: SettingsIn) -> SettingsOut:
    row = db.query(UserSettings).filter(UserSettings.user_id == user.id).one_or_none()
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
    row.llm_base_url = payload.llm_base_url.strip() or settings.default_llm_base_url
    row.llm_model = payload.llm_model.strip() or settings.default_llm_model
    touch_settings(row)
    if payload.llm_api_key is not None:
        set_api_key(user.id, payload.llm_api_key)
    db.commit()
    return get_settings(db, user)
