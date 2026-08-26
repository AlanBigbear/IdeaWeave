import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Persona, User


def require_persona(db: Session, user: User) -> Persona:
    if user.active_persona_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先选择 UP 主人设",
        )
    persona = db.get(Persona, user.active_persona_id)
    if persona is None or persona.user_id != user.id:
        raise HTTPException(status_code=400, detail="当前人设无效，请重新选择")
    return persona


def dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads(text: str, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
