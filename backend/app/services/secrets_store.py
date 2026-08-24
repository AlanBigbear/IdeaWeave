import json
from pathlib import Path

from app.core.config import settings


def _load() -> dict:
    path = settings.secrets_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    path: Path = settings.secrets_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_api_key(user_id: int) -> str:
    return _load().get(str(user_id), "")


def get_effective_api_key(user_id: int, stored: str = "") -> str:
    return (stored or "").strip() or get_api_key(user_id) or settings.default_llm_api_key


def set_api_key(user_id: int, api_key: str) -> None:
    data = _load()
    if api_key.strip():
        data[str(user_id)] = api_key.strip()
    elif str(user_id) in data:
        del data[str(user_id)]
    _save(data)
