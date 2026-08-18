from datetime import datetime

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    active_persona_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonaIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    style_desc: str = ""
    audience: str = ""
    video_format: str = ""
    taboos: str = ""
    sample_tone: str = ""
    template_key: str = "custom"
    zone: str = ""
    content_style: str = ""
    update_freq: str = ""
    comment_style: str = ""


class PersonaOut(BaseModel):
    id: int
    template_key: str
    name: str
    style_desc: str
    audience: str
    video_format: str
    taboos: str
    sample_tone: str
    zone: str = ""
    content_style: str = ""
    update_freq: str = ""
    comment_style: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonaTemplateOut(BaseModel):
    key: str
    name: str
    style_desc: str
    audience: str
    video_format: str
    taboos: str
    sample_tone: str
    zone: str = ""
    content_style: str = ""
    update_freq: str = ""
    comment_style: str = ""


class OptionItem(BaseModel):
    key: str
    label: str
    desc: str = ""
    emoji: str = ""


class PersonaOptionsOut(BaseModel):
    zones: list[OptionItem]
    content_styles: list[str]
    update_freqs: list[OptionItem]
    comment_styles: list[OptionItem]


class ActivatePersonaIn(BaseModel):
    template_key: str | None = None
    persona_id: int | None = None


class SettingsOut(BaseModel):
    llm_base_url: str
    llm_model: str
    has_api_key: bool
    default_llm_base_url: str
    default_llm_model: str


class SettingsIn(BaseModel):
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str | None = None


class ExtractInspirationIn(BaseModel):
    raw_text: str = Field(min_length=8)
    source_note: str = ""


class InspirationOut(BaseModel):
    id: int
    raw_text: str
    source_note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TopicOut(BaseModel):
    id: int
    inspiration_id: int | None
    title: str
    highlights: list[str]
    feasibility: str
    cost_note: str
    why: str
    source: str
    status: str
    created_at: datetime


class TopicCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    highlights: list[str] = Field(default_factory=list)
    feasibility: str = "quick"
    cost_note: str = ""
    why: str = ""


class TopicPatchIn(BaseModel):
    title: str | None = None
    highlights: list[str] | None = None
    feasibility: str | None = None
    cost_note: str | None = None
    why: str | None = None
    status: str | None = None


class IdeaItem(BaseModel):
    title: str
    angle: str
    audience: str
    cost: str
    hook: str
    why_different: str


class DivergeIn(BaseModel):
    vague_idea: str = Field(min_length=4)
    topic_id: int | None = None


class IdeaSessionOut(BaseModel):
    id: int
    topic_id: int | None
    vague_idea: str
    ideas: list[IdeaItem]
    selected_index: int | None
    created_at: datetime


class SelectIdeaIn(BaseModel):
    index: int = Field(ge=0, le=2)


class ShotOut(BaseModel):
    time_range: str
    camera: str
    action: str
    line: str
    interaction: str = ""


class ScriptBodyOut(BaseModel):
    title: str
    hook: str
    duration_hint: str
    shots: list[ShotOut]
    cta: str


class CoverPromptOut(BaseModel):
    style: str
    prompt: str


class RiskItemOut(BaseModel):
    level: str
    category: str
    detail: str
    suggestion: str


class ExpandScriptIn(BaseModel):
    outline: str = Field(min_length=8)
    shot_list: str = ""
    comments_text: str = ""
    use_mock_comments: bool = True
    topic_id: int | None = None
    idea_session_id: int | None = None


class ScriptOut(BaseModel):
    id: int
    topic_id: int | None
    idea_session_id: int | None
    outline: str
    shot_list: str
    comments_text: str
    script: ScriptBodyOut
    cover_prompts: list[CoverPromptOut]
    risks: list[RiskItemOut]
    created_at: datetime


class CalendarExtractIn(BaseModel):
    raw_text: str = Field(min_length=8)


class CalendarEventOut(BaseModel):
    id: int
    title: str
    start_date: str
    end_date: str
    location: str
    vlog_fit: str
    commercial: str
    raw_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentBundleOut(BaseModel):
    source: str
    comments: list[str]
