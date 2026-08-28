from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import DivergeIn, IdeaCardOut, IdeaItem, IdeaSessionOut, SaveIdeaIn, SelectIdeaIn
from app.services import idea as idea_service
from app.services.streaming import sse_token_stream
from app.services.trial import trial_generation_slot

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/diverge", response_model=IdeaSessionOut, dependencies=[Depends(trial_generation_slot)])
def diverge(
    payload: DivergeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.diverge(db, user, payload)


@router.post("/diverge/stream", dependencies=[Depends(trial_generation_slot)])
def diverge_stream(
    payload: DivergeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def run(session: Session, on_delta) -> IdeaSessionOut:
        owner = session.get(User, user.id)
        return idea_service.diverge(session, owner, payload, on_delta)

    return StreamingResponse(
        sse_token_stream(run, serialize=lambda r: r.model_dump_json()),
        media_type="text/event-stream",
    )


@router.get("", response_model=list[IdeaSessionOut])
def list_ideas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return idea_service.list_sessions(db, user)


@router.get("/cards", response_model=list[IdeaCardOut])
def list_cards(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return idea_service.list_cards(db, user)


@router.patch("/{session_id}/cards/{index}", response_model=IdeaCardOut)
def update_card(
    session_id: int,
    index: int,
    payload: IdeaItem,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.update_card(db, user, session_id, index, payload)


@router.delete("/{session_id}/cards/{index}")
def delete_card(
    session_id: int,
    index: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idea_service.delete_card(db, user, session_id, index)
    return {"ok": True}


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


@router.post("/{session_id}/save", response_model=IdeaSessionOut)
def save_idea(
    session_id: int,
    payload: SaveIdeaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return idea_service.save_idea(db, user, session_id, payload.index, payload.saved)
