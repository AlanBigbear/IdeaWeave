from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import TopicCreateIn, TopicOut, TopicPatchIn
from app.services import topic as topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(
    feasibility: str | None = Query(default=None),
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topic_service.list_topics(
        db, user, feasibility=feasibility, q=q, status=status, priority=priority, tag=tag
    )


@router.post("", response_model=TopicOut)
def create_topic(
    payload: TopicCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topic_service.create_manual_topic(db, user, payload)


@router.patch("/{topic_id}", response_model=TopicOut)
def patch_topic(
    topic_id: int,
    payload: TopicPatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return topic_service.patch_topic(db, user, topic_id, payload)


@router.delete("/{topic_id}")
def delete_topic(
    topic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic_service.delete_topic(db, user, topic_id)
    return {"ok": True}


@router.get("/export.md")
def export_md(
    feasibility: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = topic_service.export_markdown(
        db, user, feasibility=feasibility, status=status, priority=priority, tag=tag
    )
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
