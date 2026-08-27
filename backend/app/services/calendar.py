from fastapi import HTTPException
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import capture_calendar_chain, extract_calendar_chain, run_chain
from app.models import CalendarEvent, User
from app.schemas import (
    CalendarCaptureOut,
    CalendarEventIn,
    CalendarEventOut,
    CalendarEventUpdate,
    CalendarExtractIn,
)
from app.services.common import require_persona
from app.services.hotspots import capture_window, overlaps_window, seasonal_hints_for_persona


def _fingerprint(title: str, start_date: str) -> tuple[str, str]:
    return title.strip().lower(), (start_date or "").strip()


def _existing_keys(db: Session, user: User) -> set[tuple[str, str]]:
    rows = (
        db.query(CalendarEvent.title, CalendarEvent.start_date)
        .filter(CalendarEvent.user_id == user.id)
        .all()
    )
    return {_fingerprint(title, start_date) for title, start_date in rows}


def _insert_payload(db: Session, user: User, payload: dict, seen: set[tuple[str, str]]) -> CalendarEvent | None:
    title = (payload.get("title") or "").strip()
    start_date = (payload.get("start_date") or "").strip()
    end_date = (payload.get("end_date") or start_date).strip()
    if not title:
        return None
    if payload.get("source") == "capture":
        if not overlaps_window(start_date, end_date):
            return None
        # 质量闸门：泛称标题 / 没写拍法的低质条目直接丢弃
        if len(title) < 6 or not (payload.get("vlog_fit") or "").strip():
            return None
    key = _fingerprint(title, start_date)
    if key in seen:
        return None
    row = CalendarEvent(
        user_id=user.id,
        title=title[:200],
        start_date=start_date,
        end_date=end_date,
        location=(payload.get("location") or "").strip(),
        vlog_fit=(payload.get("vlog_fit") or "").strip(),
        commercial=(payload.get("commercial") or "").strip(),
        raw_text=(payload.get("raw_text") or "").strip(),
        source=(payload.get("source") or "manual").strip() or "manual",
    )
    db.add(row)
    seen.add(key)
    return row


def extract(db: Session, user: User, payload: CalendarExtractIn) -> CalendarEventOut:
    persona = require_persona(db, user)
    llm = build_llm(db, user, temperature=0.2, max_tokens=500, fast=True)
    raw, parser = extract_calendar_chain(llm, persona)
    result = run_chain(
        raw,
        parser,
        {"raw_text": payload.raw_text[:10000], "today": date.today().isoformat()},
    )
    seen = _existing_keys(db, user)
    row = _insert_payload(
        db,
        user,
        {
            "title": result.title,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "location": result.location,
            "vlog_fit": result.vlog_fit,
            "commercial": result.commercial,
            "raw_text": payload.raw_text,
            "source": "extract",
        },
        seen,
    )
    if row is None:
        raise HTTPException(status_code=409, detail="这条热点已在日历里")
    db.commit()
    db.refresh(row)
    return CalendarEventOut.model_validate(row)


def capture(db: Session, user: User) -> CalendarCaptureOut:
    persona = require_persona(db, user)
    today, until = capture_window()
    hints = seasonal_hints_for_persona(persona, today)
    seen = _existing_keys(db, user)
    llm = build_llm(db, user, temperature=0.5, max_tokens=3000, fast=True)
    # 去重提示只保留窗口附近的事件标题，避免列表无限增长
    window_from = (today - timedelta(days=7)).isoformat()
    window_until = until.isoformat()
    existing_titles = sorted(
        {
            title
            for title, start in seen
            if window_from <= (start or "") <= window_until
        }
    )
    raw, parser = capture_calendar_chain(llm, persona)
    bundle = run_chain(
        raw,
        parser,
        {
            "today": today.isoformat(),
            "until": window_until,
            "existing": "、".join(existing_titles[:40]) or "无",
            "seasonal": "；".join(
                f"{item['title']}({item['start_date']}，{item['angle']})" for item in hints
            )
            or "无匹配季节节点，请完全按人设生成",
        },
    )
    created_rows: list[CalendarEvent] = []
    skipped = 0
    for item in bundle.events:
        row = _insert_payload(
            db,
            user,
            {
                "title": item.title,
                "start_date": item.start_date,
                "end_date": item.end_date or item.start_date,
                "location": item.location,
                "vlog_fit": item.vlog_fit,
                "commercial": item.commercial,
                "raw_text": "AI 按人设捕捉（未来30天）",
                "source": "capture",
            },
            seen,
        )
        if row is None:
            skipped += 1
        else:
            created_rows.append(row)
    db.commit()
    for row in created_rows:
        db.refresh(row)
    return CalendarCaptureOut(
        created=len(created_rows),
        skipped=skipped,
        warning="" if created_rows else "未来 30 天内没蹲到足够具体又符合人设的热点，可以稍后再试或手动添加",
        events=[CalendarEventOut.model_validate(row) for row in created_rows],
    )


def create_event(db: Session, user: User, payload: CalendarEventIn) -> CalendarEventOut:
    require_persona(db, user)
    seen = _existing_keys(db, user)
    row = _insert_payload(
        db,
        user,
        {**payload.model_dump(), "source": payload.source or "manual"},
        seen,
    )
    if row is None:
        raise HTTPException(status_code=409, detail="同名同日期的热点已存在")
    db.commit()
    db.refresh(row)
    return CalendarEventOut.model_validate(row)


def update_event(db: Session, user: User, event_id: int, payload: CalendarEventUpdate) -> CalendarEventOut:
    row = _get_owned(db, user, event_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(row)
    return CalendarEventOut.model_validate(row)


def list_events(db: Session, user: User) -> list[CalendarEvent]:
    return (
        db.query(CalendarEvent)
        .filter(CalendarEvent.user_id == user.id)
        .order_by(CalendarEvent.start_date.asc(), CalendarEvent.id.asc())
        .all()
    )


def delete_event(db: Session, user: User, event_id: int) -> None:
    row = _get_owned(db, user, event_id)
    db.delete(row)
    db.commit()


def _get_owned(db: Session, user: User, event_id: int) -> CalendarEvent:
    row = db.get(CalendarEvent, event_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="日历项不存在")
    return row
