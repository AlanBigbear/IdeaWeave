from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import extract_calendar_chain, invoke_or_502
from app.models import CalendarEvent, User
from app.schemas import CalendarExtractIn, CalendarEventOut
from app.services.common import require_persona


def extract(db: Session, user: User, payload: CalendarExtractIn) -> CalendarEventOut:
    persona = require_persona(db, user)
    llm = build_llm(db, user, temperature=0.2)
    result = invoke_or_502(extract_calendar_chain(llm, persona), {"raw_text": payload.raw_text})
    row = CalendarEvent(
        user_id=user.id,
        title=result.title,
        start_date=result.start_date,
        end_date=result.end_date,
        location=result.location,
        vlog_fit=result.vlog_fit,
        commercial=result.commercial,
        raw_text=payload.raw_text,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CalendarEventOut.model_validate(row)


def list_events(db: Session, user: User) -> list[CalendarEvent]:
    return (
        db.query(CalendarEvent)
        .filter(CalendarEvent.user_id == user.id)
        .order_by(CalendarEvent.start_date.desc(), CalendarEvent.id.desc())
        .all()
    )


def delete_event(db: Session, user: User, event_id: int) -> None:
    row = db.get(CalendarEvent, event_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="日历项不存在")
    db.delete(row)
    db.commit()
