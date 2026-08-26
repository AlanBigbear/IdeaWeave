from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    CalendarCaptureOut,
    CalendarEventIn,
    CalendarEventOut,
    CalendarEventUpdate,
    CalendarExtractIn,
)
from app.services import calendar as calendar_service
from app.services.streaming import sse_stream

router = APIRouter(prefix="/calendar", tags=["calendar"])

_EXTRACT_STATUSES = [
    "编导娘探出头去读这段热点…",
    "抠出事件、日期和地点…",
    "按你的人设想想怎么拍…",
]

_CAPTURE_STATUSES = [
    "编导娘探出头去蹲未来 30 天热点…",
    "翻遍日历格子，按人设筛出能拍的…",
    "把热点一条条排进日历…",
]


@router.post("/extract", response_model=CalendarEventOut)
def extract(
    payload: CalendarExtractIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calendar_service.extract(db, user, payload)


@router.post("/extract/stream")
def extract_stream(
    payload: CalendarExtractIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def run(session: Session) -> CalendarEventOut:
        owner = session.get(User, user.id)
        return calendar_service.extract(session, owner, payload)

    return StreamingResponse(
        sse_stream(
            run,
            serialize=lambda r: r.model_dump_json(),
            statuses=_EXTRACT_STATUSES,
        ),
        media_type="text/event-stream",
    )


@router.post("/capture", response_model=CalendarCaptureOut)
def capture(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return calendar_service.capture(db, user)


@router.post("/capture/stream")
def capture_stream(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    def run(session: Session) -> CalendarCaptureOut:
        owner = session.get(User, user.id)
        return calendar_service.capture(session, owner)

    return StreamingResponse(
        sse_stream(
            run,
            serialize=lambda r: r.model_dump_json(),
            statuses=_CAPTURE_STATUSES,
        ),
        media_type="text/event-stream",
    )


@router.get("", response_model=list[CalendarEventOut])
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return calendar_service.list_events(db, user)


@router.post("", response_model=CalendarEventOut)
def create_event(
    payload: CalendarEventIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calendar_service.create_event(db, user, payload)


@router.patch("/{event_id}", response_model=CalendarEventOut)
def update_event(
    event_id: int,
    payload: CalendarEventUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calendar_service.update_event(db, user, event_id, payload)


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    calendar_service.delete_event(db, user, event_id)
    return {"ok": True}
