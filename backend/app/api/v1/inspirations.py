from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import ExtractInspirationIn, FetchPreviewIn, FetchPreviewOut, TopicOut
from app.services import topic as topic_service
from app.services.streaming import sse_token_stream

router = APIRouter(prefix="/inspirations", tags=["inspirations"])


@router.post("/extract", response_model=TopicOut)
def extract(
    payload: ExtractInspirationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topic_service.extract_and_save(db, user, payload)


@router.post("/extract/stream")
def extract_stream(
    payload: ExtractInspirationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def run(session: Session, on_delta) -> TopicOut:
        owner = session.get(User, user.id)
        return topic_service.extract_and_save(session, owner, payload, on_delta)

    return StreamingResponse(
        sse_token_stream(run, serialize=lambda r: r.model_dump_json()),
        media_type="text/event-stream",
    )


@router.post("/fetch", response_model=FetchPreviewOut)
def fetch(
    payload: FetchPreviewIn,
    user: User = Depends(get_current_user),
):
    return topic_service.fetch_preview(payload.url)
