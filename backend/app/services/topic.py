from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import extract_topic_chain, invoke_or_502
from app.models import Inspiration, Topic, User
from app.schemas import ExtractInspirationIn, TopicCreateIn, TopicOut, TopicPatchIn
from app.services.common import dumps, loads, require_persona


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
        created_at=topic.created_at,
    )


def extract_and_save(db: Session, user: User, payload: ExtractInspirationIn) -> TopicOut:
    persona = require_persona(db, user)
    llm = build_llm(db, user)
    chain = extract_topic_chain(llm, persona)
    result = invoke_or_502(chain, {"raw_text": payload.raw_text, "source_note": payload.source_note})
    feasibility = result.feasibility if result.feasibility in {"quick", "deferred"} else "quick"
    inspiration = Inspiration(
        user_id=user.id, raw_text=payload.raw_text, source_note=payload.source_note
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


def list_topics(db: Session, user: User, feasibility: str | None = None, q: str | None = None):
    query = db.query(Topic).filter(Topic.user_id == user.id)
    if feasibility in {"quick", "deferred"}:
        query = query.filter(Topic.feasibility == feasibility)
    if q:
        like = f"%{q}%"
        query = query.filter(Topic.title.like(like))
    rows = query.order_by(Topic.id.desc()).all()
    return [topic_to_out(row) for row in rows]


def create_manual_topic(db: Session, user: User, payload: TopicCreateIn) -> TopicOut:
    require_persona(db, user)
    feasibility = payload.feasibility if payload.feasibility in {"quick", "deferred"} else "quick"
    topic = Topic(
        user_id=user.id,
        title=payload.title,
        highlights=dumps(payload.highlights),
        feasibility=feasibility,
        cost_note=payload.cost_note,
        why=payload.why,
        source="manual",
        status="inbox",
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
    if "highlights" in data and data["highlights"] is not None:
        topic.highlights = dumps(data.pop("highlights"))
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


def export_markdown(db: Session, user: User, feasibility: str | None = None) -> str:
    topics = list_topics(db, user, feasibility=feasibility)
    lines = ["# B-Star 选题库", ""]
    for topic in topics:
        tag = "短平快可执行" if topic.feasibility == "quick" else "高成本暂缓"
        lines.extend(
            [
                f"## {topic.title}",
                f"- 可行性：{tag}",
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
