import threading
import time

from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserSettings


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


# 复用 ChatOpenAI 实例（含底层 HTTP 连接池），省去每次请求的 TCP+TLS 握手
_client_cache: dict[tuple, tuple] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300


def _cached_client(key: tuple, factory) -> ChatOpenAI:
    now = time.monotonic()
    with _cache_lock:
        hit = _client_cache.get(key)
        if hit and now - hit[0] < _CACHE_TTL:
            return hit[1]
    client = factory()
    with _cache_lock:
        if len(_client_cache) > 64:
            _client_cache.clear()
        _client_cache[key] = (now, client)
    return client


def build_llm(
    db: Session,
    user: User,
    temperature: float = 0.6,
    max_tokens: int | None = None,
) -> ChatOpenAI:
    from app.services.secrets_store import get_effective_api_key

    cfg = get_user_settings(db, user)
    api_key = get_effective_api_key(user.id, cfg.llm_api_key)
    base_url = normalize_openai_base_url(cfg.llm_base_url or settings.default_llm_base_url)
    model = (cfg.llm_model or settings.default_llm_model).strip()
    if not base_url or not model or not api_key:
        raise LLMNotConfigured()

    def factory() -> ChatOpenAI:
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            timeout=300,
            max_retries=2,
            max_tokens=max_tokens,
        )

    return _cached_client((user.id, base_url, model, api_key, temperature, max_tokens), factory)
