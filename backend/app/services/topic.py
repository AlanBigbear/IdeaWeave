from fastapi import HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import extract_topic_chain, invoke_or_502
from app.models import Inspiration, Topic, User
from app.providers.fetcher import FetchError, FetchResult, fetch_webpage
from app.schemas import (
    TOPIC_PRIORITIES,
    TOPIC_STATUSES,
    ExtractInspirationIn,
    FetchPreviewOut,
    TopicCreateIn,
    TopicOut,
    TopicPatchIn,
)
from app.services.common import dumps, loads, require_persona

TOPIC_STATUS_LABELS = {"inbox": "待定", "ready": "可用", "paused": "暂缓", "dropped": "弃用"}
TOPIC_PRIORITY_LABELS = {"high": "高", "mid": "中", "low": "低"}
_PRIORITY_ORDER = case(
    (Topic.priority == "high", 0), (Topic.priority == "mid", 1), else_=2
)


def _fetch_or_400(url: str) -> FetchResult:
    try:
        return fetch_webpage(url)
    except FetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def fetch_preview(url: str) -> FetchPreviewOut:
    result = _fetch_or_400(url)
    return FetchPreviewOut(**result.__dict__)


def topic_to_out(topic: Topic) -> TopicOut:
    return TopicOut(
        id=topic.id,
        inspiration_id=topic.inspiration_id,
        title=topic.title,
        highlights=loads(topic.highlights, []),
        feasibility=topic.feasibility,
        cost_note=topic.cost_note,
        why=topic.why,
        source=topic.source,
        status=topic.status,
        priority=topic.priority,
        tags=loads(topic.tags, []),
        created_at=topic.created_at,
    )


def extract_and_save(db: Session, user: User, payload: ExtractInspirationIn) -> TopicOut:
    persona = require_persona(db, user)
    if payload.url.strip() and not payload.raw_text.strip():
        fetched = _fetch_or_400(payload.url)
        raw_text = f"《{fetched.title}》（来源：{fetched.site_name}）\n{fetched.text}"
        source_note = payload.source_note.strip() or f"链接抓取：{fetched.url}"
    else:
        raw_text = payload.raw_text
        source_note = payload.source_note
    llm = build_llm(db, user)
    chain = extract_topic_chain(llm, persona)
    result = invoke_or_502(chain, {"raw_text": raw_text, "source_note": source_note})
    feasibility = result.feasibility if result.feasibility in {"quick", "deferred"} else "quick"
    inspiration = Inspiration(
        user_id=user.id, raw_text=raw_text, source_note=source_note
    )
    db.add(inspiration)
    db.flush()
    topic = Topic(
        user_id=user.id,
        inspiration_id=inspiration.id,
        title=result.title,
        highlights=dumps(result.highlights),
        feasibility=feasibility,
        cost_note=result.cost_note,
        why=result.why,
        source="extract",
        status="inbox",
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic_to_out(topic)


def list_topics(
    db: Session,
    user: User,
    feasibility: str | None = None,
    q: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
):
    query = db.query(Topic).filter(Topic.user_id == user.id)
    if feasibility in {"quick", "deferred"}:
        query = query.filter(Topic.feasibility == feasibility)
    if status in TOPIC_STATUSES:
        query = query.filter(Topic.status == status)
    if priority in TOPIC_PRIORITIES:
        query = query.filter(Topic.priority == priority)
    if tag:
        query = query.filter(Topic.tags.like(f'%"{tag}"%'))
    if q:
        like = f"%{q}%"
        query = query.filter(Topic.title.like(like))
    rows = query.order_by(_PRIORITY_ORDER, Topic.id.desc()).all()
    return [topic_to_out(row) for row in rows]


def create_manual_topic(db: Session, user: User, payload: TopicCreateIn) -> TopicOut:
    require_persona(db, user)
    feasibility = payload.feasibility if payload.feasibility in {"quick", "deferred"} else "quick"
    status = payload.status if payload.status in TOPIC_STATUSES else "inbox"
    priority = payload.priority if payload.priority in TOPIC_PRIORITIES else "mid"
    topic = Topic(
        user_id=user.id,
        title=payload.title,
        highlights=dumps(payload.highlights),
        feasibility=feasibility,
        cost_note=payload.cost_note,
        why=payload.why,
        source="manual",
        status=status,
        priority=priority,
        tags=dumps(payload.tags),
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic_to_out(topic)


def patch_topic(db: Session, user: User, topic_id: int, payload: TopicPatchIn) -> TopicOut:
    topic = db.get(Topic, topic_id)
    if topic is None or topic.user_id != user.id:
        raise HTTPException(status_code=404, detail="选题不存在")
    data = payload.model_dump(exclude_unset=True)
    for json_field in ("highlights", "tags"):
        if json_field in data and data[json_field] is not None:
            topic.__setattr__(json_field, dumps(data.pop(json_field)))
    if data.get("status") and data["status"] not in TOPIC_STATUSES:
        data.pop("status")
    if data.get("priority") and data["priority"] not in TOPIC_PRIORITIES:
        data.pop("priority")
    for key, value in data.items():
        setattr(topic, key, value)
    db.commit()
    db.refresh(topic)
    return topic_to_out(topic)


def delete_topic(db: Session, user: User, topic_id: int) -> None:
    topic = db.get(Topic, topic_id)
    if topic is None or topic.user_id != user.id:
        raise HTTPException(status_code=404, detail="选题不存在")
    db.delete(topic)
    db.commit()


def export_markdown(
    db: Session,
    user: User,
    feasibility: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
) -> str:
    topics = list_topics(
        db, user, feasibility=feasibility, status=status, priority=priority, tag=tag
    )
    lines = ["# B-Star 选题库", ""]
    for topic in topics:
        tag_label = "短平快可执行" if topic.feasibility == "quick" else "高成本暂缓"
        status_label = TOPIC_STATUS_LABELS.get(topic.status, topic.status)
        priority_label = TOPIC_PRIORITY_LABELS.get(topic.priority, topic.priority)
        lines.extend(
            [
                f"## {topic.title}",
                f"- 可行性：{tag_label}",
                f"- 状态：{status_label}｜优先级：{priority_label}",
                f"- 标签：{'、'.join(topic.tags) if topic.tags else '—'}",
                f"- 来源：{'AI 提取' if topic.source == 'extract' else '零碎灵感'}",
                f"- 成本：{topic.cost_note or '—'}",
                f"- 理由：{topic.why or '—'}",
                "- 爆点：",
            ]
        )
        for item in topic.highlights:
            lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)
