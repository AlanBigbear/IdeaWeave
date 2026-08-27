from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import diverge_ideas_chain, run_chain
from app.models import IdeaSession, Topic, User
from app.schemas import DivergeIn, IdeaCardOut, IdeaItem, IdeaSessionOut
from app.services.common import dumps, loads, require_persona


def session_to_out(row: IdeaSession) -> IdeaSessionOut:
    raw = loads(row.ideas_json, [])
    ideas = [IdeaItem.model_validate(item) for item in raw]
    saved = [i for i in loads(row.saved_json, []) if isinstance(i, int) and 0 <= i < len(ideas)]
    return IdeaSessionOut(
        id=row.id,
        topic_id=row.topic_id,
        vague_idea=row.vague_idea,
        ideas=ideas,
        selected_index=row.selected_index,
        saved_indexes=saved,
        created_at=row.created_at,
    )


def diverge(db: Session, user: User, payload: DivergeIn, on_delta=None) -> IdeaSessionOut:
    persona = require_persona(db, user)
    topic_hint = "无"
    if payload.topic_id:
        topic = db.get(Topic, payload.topic_id)
        if topic is None or topic.user_id != user.id:
            raise HTTPException(status_code=404, detail="选题不存在")
        topic_hint = f"{topic.title} | {topic.why}"
    llm = build_llm(db, user, temperature=0.5, max_tokens=1600, fast=True)
    raw, parser = diverge_ideas_chain(llm, persona)
    bundle = run_chain(
        raw,
        parser,
        {"vague_idea": payload.vague_idea[:2000], "topic_hint": topic_hint[:600]},
        on_delta,
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


def save_idea(db: Session, user: User, session_id: int, index: int, saved: bool) -> IdeaSessionOut:
    row = get_session(db, user, session_id)
    ideas = loads(row.ideas_json, [])
    if index < 0 or index >= len(ideas):
        raise HTTPException(status_code=400, detail="请选择 1/2/3 号创意")
    saved_indexes = [i for i in loads(row.saved_json, []) if isinstance(i, int)]
    if saved and index not in saved_indexes:
        saved_indexes.append(index)
    elif not saved and index in saved_indexes:
        saved_indexes.remove(index)
    row.saved_json = dumps(sorted(saved_indexes))
    db.commit()
    db.refresh(row)
    return session_to_out(row)


def _card_out(row: IdeaSession, index: int, idea: IdeaItem) -> IdeaCardOut:
    return IdeaCardOut(
        session_id=row.id,
        index=index,
        created_at=row.created_at,
        **idea.model_dump(),
    )


def list_cards(db: Session, user: User) -> list[IdeaCardOut]:
    rows = (
        db.query(IdeaSession)
        .filter(IdeaSession.user_id == user.id)
        .order_by(IdeaSession.id.desc())
        .all()
    )
    cards: list[IdeaCardOut] = []
    for row in rows:
        raw = loads(row.ideas_json, [])
        for index, item in enumerate(raw):
            cards.append(_card_out(row, index, IdeaItem.model_validate(item)))
    return cards


def update_card(db: Session, user: User, session_id: int, index: int, payload: IdeaItem) -> IdeaCardOut:
    row = get_session(db, user, session_id)
    ideas = loads(row.ideas_json, [])
    if index < 0 or index >= len(ideas):
        raise HTTPException(status_code=400, detail="创意卡不存在")
    ideas[index] = payload.model_dump()
    row.ideas_json = dumps(ideas)
    db.commit()
    db.refresh(row)
    return _card_out(row, index, payload)


def delete_card(db: Session, user: User, session_id: int, index: int) -> None:
    row = get_session(db, user, session_id)
    ideas = loads(row.ideas_json, [])
    if index < 0 or index >= len(ideas):
        raise HTTPException(status_code=400, detail="创意卡不存在")
    ideas.pop(index)
    row.ideas_json = dumps(ideas)
    if row.selected_index is not None:
        if row.selected_index == index:
            row.selected_index = None
        elif row.selected_index > index:
            row.selected_index -= 1
    saved: list[int] = []
    for i in loads(row.saved_json, []):
        if not isinstance(i, int) or i == index:
            continue
        saved.append(i - 1 if i > index else i)
    row.saved_json = dumps(sorted(saved))
    db.commit()
    db.refresh(row)
