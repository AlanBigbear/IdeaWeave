from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/extract", response_model=CalendarEventOut)
def extract(
    payload: CalendarExtractIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calendar_service.extract(db, user, payload)


@router.post("/capture", response_model=CalendarCaptureOut)
def capture(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return calendar_service.capture(db, user)


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
