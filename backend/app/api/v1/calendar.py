from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import CalendarEventOut, CalendarExtractIn
from app.services import calendar as calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/extract", response_model=CalendarEventOut)
def extract(
    payload: CalendarExtractIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calendar_service.extract(db, user, payload)


@router.get("", response_model=list[CalendarEventOut])
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return calendar_service.list_events(db, user)


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    calendar_service.delete_event(db, user, event_id)
    return {"ok": True}
