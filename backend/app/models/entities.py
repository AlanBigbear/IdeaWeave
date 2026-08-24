from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active_persona_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    personas: Mapped[list["Persona"]] = relationship(back_populates="user")
    settings: Mapped["UserSettings | None"] = relationship(back_populates="user")


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_key: Mapped[str] = mapped_column(String(64), default="custom")
    name: Mapped[str] = mapped_column(String(80))
    style_desc: Mapped[str] = mapped_column(Text, default="")
    audience: Mapped[str] = mapped_column(Text, default="")
    video_format: Mapped[str] = mapped_column(String(120), default="")
    taboos: Mapped[str] = mapped_column(Text, default="")
    sample_tone: Mapped[str] = mapped_column(Text, default="")
    zone: Mapped[str] = mapped_column(String(64), default="")
    content_style: Mapped[str] = mapped_column(String(200), default="")
    update_freq: Mapped[str] = mapped_column(String(64), default="")
    comment_style: Mapped[str] = mapped_column(Text, default="")
    skill_prompt: Mapped[str] = mapped_column(Text, default="")
    skill_brief_json: Mapped[str] = mapped_column(Text, default="{}")
    skill_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="personas")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    llm_base_url: Mapped[str] = mapped_column(String(255), default="")
    llm_model: Mapped[str] = mapped_column(String(120), default="")
    llm_api_key: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="settings")


class Inspiration(Base):
    __tablename__ = "inspirations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    source_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    inspiration_id: Mapped[int | None] = mapped_column(ForeignKey("inspirations.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    feasibility: Mapped[str] = mapped_column(String(32), default="quick")  # quick | deferred
    cost_note: Mapped[str] = mapped_column(Text, default="")
    why: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="extract")  # extract | manual
    status: Mapped[str] = mapped_column(String(32), default="inbox")  # inbox | ready | paused | dropped
    priority: Mapped[str] = mapped_column(String(16), default="mid")  # high | mid | low
    tags: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class IdeaSession(Base):
    __tablename__ = "idea_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    vague_idea: Mapped[str] = mapped_column(Text)
    ideas_json: Mapped[str] = mapped_column(Text, default="[]")
    selected_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    idea_session_id: Mapped[int | None] = mapped_column(ForeignKey("idea_sessions.id"), nullable=True)
    outline: Mapped[str] = mapped_column(Text, default="")
    shot_list: Mapped[str] = mapped_column(Text, default="")
    comments_text: Mapped[str] = mapped_column(Text, default="")
    script_json: Mapped[str] = mapped_column(Text, default="{}")
    cover_prompts_json: Mapped[str] = mapped_column(Text, default="[]")
    risks_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[str] = mapped_column(String(32), default="")
    end_date: Mapped[str] = mapped_column(String(32), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    vlog_fit: Mapped[str] = mapped_column(Text, default="")
    commercial: Mapped[str] = mapped_column(Text, default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="extract")  # capture | extract | manual
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
