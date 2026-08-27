from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import ExpandScriptIn, ScriptOut
from app.services import script as script_service
from app.services.streaming import sse_token_stream

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("/expand", response_model=ScriptOut)
def expand(
    payload: ExpandScriptIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return script_service.expand(db, user, payload)


@router.post("/expand/stream")
def expand_stream(
    payload: ExpandScriptIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def run(session: Session, on_delta) -> ScriptOut:
        owner = session.get(User, user.id)
        return script_service.expand(session, owner, payload, on_delta)

    return StreamingResponse(
        sse_token_stream(run, serialize=lambda r: r.model_dump_json()),
        media_type="text/event-stream",
    )


@router.get("", response_model=list[ScriptOut])
def list_scripts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return script_service.list_scripts(db, user)


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(
    script_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return script_service.get_script(db, user, script_id)
