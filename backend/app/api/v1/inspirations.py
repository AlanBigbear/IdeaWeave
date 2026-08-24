from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import ExtractInspirationIn, FetchPreviewIn, FetchPreviewOut, TopicOut
from app.services import topic as topic_service

router = APIRouter(prefix="/inspirations", tags=["inspirations"])


@router.post("/extract", response_model=TopicOut)
def extract(
    payload: ExtractInspirationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topic_service.extract_and_save(db, user, payload)


@router.post("/fetch", response_model=FetchPreviewOut)
def fetch(
    payload: FetchPreviewIn,
    user: User = Depends(get_current_user),
):
    return topic_service.fetch_preview(payload.url)
