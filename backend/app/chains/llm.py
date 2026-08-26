import threading
import time

from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserSettings


class ChatOpenAIWithReasoning(ChatOpenAI):
    """捕获推理模型（如 deepseek-reasoner）流式输出里的 reasoning_content（思考过程）。

    langchain-openai 的 ChatOpenAI 在流式转换时会丢弃 delta 里的 reasoning_content，
    导致推理模型的「思考」看不到。这里把它写进 additional_kwargs，供
    run_chain 的 on_delta("thinking", …) 逐段转发给前端。
    """

    def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info):
        gen = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if gen is None or gen.message is None:
            return gen
        choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
        if not choices:
            return gen
        delta = choices[0].get("delta") or {}
        reasoning = delta.get("reasoning_content")
        if reasoning:
            msg = gen.message
            if not isinstance(msg.additional_kwargs, dict):
                msg.additional_kwargs = {}
            msg.additional_kwargs["reasoning_content"] = reasoning
        return gen


def _is_reasoner(model: str) -> bool:
    """判断是否为推理模型（deepseek-reasoner / 各类 R1）。推理模型不支持 temperature。"""
    m = (model or "").lower()
    return "reasoner" in m or "-r1" in m or m.startswith("r1")


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
    fast: bool = False,
) -> ChatOpenAI:
    from app.services.secrets_store import get_effective_api_key

    cfg = get_user_settings(db, user)
    api_key = get_effective_api_key(user.id, cfg.llm_api_key)
    base_url = normalize_openai_base_url(cfg.llm_base_url or settings.default_llm_base_url)
    if fast:
        # 轻任务走快速模型（非推理），压低首字/整体延迟
        model = (settings.default_llm_fast_model or settings.default_llm_model).strip()
    else:
        model = (cfg.llm_model or settings.default_llm_model).strip()
    if not base_url or not model or not api_key:
        raise LLMNotConfigured()

    # 推理模型（deepseek-reasoner 等）不支持 temperature，置 None 让其不参与请求体
    effective_temperature = None if _is_reasoner(model) else temperature

    def factory() -> ChatOpenAI:
        return ChatOpenAIWithReasoning(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=effective_temperature,
            timeout=300,
            max_retries=2,
            max_tokens=max_tokens,
        )

    return _cached_client(
        (user.id, base_url, model, api_key, effective_temperature, max_tokens), factory
    )
