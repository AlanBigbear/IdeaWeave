from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import DivergeIn, IdeaSessionOut, SelectIdeaIn
from app.services import idea as idea_service

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/diverge", response_model=IdeaSessionOut)
def diverge(
    payload: DivergeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.diverge(db, user, payload)


@router.get("", response_model=list[IdeaSessionOut])
def list_ideas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return idea_service.list_sessions(db, user)


@router.get("/{session_id}", response_model=IdeaSessionOut)
def get_idea(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.session_to_out(idea_service.get_session(db, user, session_id))


@router.post("/{session_id}/select", response_model=IdeaSessionOut)
def select_idea(
    session_id: int,
    payload: SelectIdeaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.select_idea(db, user, session_id, payload.index)
