from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import diverge_ideas_chain, invoke_or_502
from app.models import IdeaSession, Topic, User
from app.schemas import DivergeIn, IdeaItem, IdeaSessionOut
from app.services.common import dumps, loads, require_persona


def session_to_out(row: IdeaSession) -> IdeaSessionOut:
    raw = loads(row.ideas_json, [])
    ideas = [IdeaItem.model_validate(item) for item in raw]
    return IdeaSessionOut(
        id=row.id,
        topic_id=row.topic_id,
        vague_idea=row.vague_idea,
        ideas=ideas,
        selected_index=row.selected_index,
        created_at=row.created_at,
    )


def diverge(db: Session, user: User, payload: DivergeIn) -> IdeaSessionOut:
    persona = require_persona(db, user)
    topic_hint = "无"
    if payload.topic_id:
        topic = db.get(Topic, payload.topic_id)
        if topic is None or topic.user_id != user.id:
            raise HTTPException(status_code=404, detail="选题不存在")
        topic_hint = f"{topic.title} | {topic.why}"
    llm = build_llm(db, user, temperature=0.8)
    bundle = invoke_or_502(
        diverge_ideas_chain(llm, persona),
        {"vague_idea": payload.vague_idea, "topic_hint": topic_hint},
    )
    row = IdeaSession(
        user_id=user.id,
        topic_id=payload.topic_id,
        vague_idea=payload.vague_idea,
        ideas_json=dumps([item.model_dump() for item in bundle.ideas]),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return session_to_out(row)


def list_sessions(db: Session, user: User) -> list[IdeaSessionOut]:
    rows = (
        db.query(IdeaSession)
        .filter(IdeaSession.user_id == user.id)
        .order_by(IdeaSession.id.desc())
        .all()
    )
    return [session_to_out(row) for row in rows]


def get_session(db: Session, user: User, session_id: int) -> IdeaSession:
    row = db.get(IdeaSession, session_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="创意会话不存在")
    return row


def select_idea(db: Session, user: User, session_id: int, index: int) -> IdeaSessionOut:
    row = get_session(db, user, session_id)
    ideas = loads(row.ideas_json, [])
    if index < 0 or index >= len(ideas):
        raise HTTPException(status_code=400, detail="请选择 1/2/3 号创意")
    row.selected_index = index
    db.commit()
    db.refresh(row)
    return session_to_out(row)
