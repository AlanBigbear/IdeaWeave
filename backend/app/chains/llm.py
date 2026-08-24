from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserSettings
from app.services.secrets_store import get_effective_api_key


class LLMNotConfigured(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在设置页配置大模型 Base URL、模型名和 API Key",
        )


def get_user_settings(db: Session, user: User) -> UserSettings:
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
    return row


def normalize_openai_base_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if "api.deepseek.com" in url and not url.endswith("/v1"):
        return f"{url}/v1"
    return url


def build_llm(db: Session, user: User, temperature: float = 0.6) -> ChatOpenAI:
    cfg = get_user_settings(db, user)
    api_key = get_effective_api_key(user.id, cfg.llm_api_key)
    base_url = normalize_openai_base_url(cfg.llm_base_url or settings.default_llm_base_url)
    model = (cfg.llm_model or settings.default_llm_model).strip()
    if not base_url or not model or not api_key:
        raise LLMNotConfigured()
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        timeout=120,
        max_retries=1,
    )
