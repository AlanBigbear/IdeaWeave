from pydantic import BaseModel, Field


class ExtractedTopic(BaseModel):
    title: str = Field(description="简洁可执行的选题标题")
    highlights: list[str] = Field(description="3-6 个爆点")
    feasibility: str = Field(description="quick 表示短平快可执行，deferred 表示高成本暂缓")
    cost_note: str = Field(description="成本/门槛说明")
    why: str = Field(description="为什么现在值得做或不值得立刻做")


class CreativeIdea(BaseModel):
    title: str
    angle: str
    audience: str
    cost: str
    hook: str
    why_different: str


class IdeaBundle(BaseModel):
    ideas: list[CreativeIdea] = Field(min_length=3, max_length=3)


class Shot(BaseModel):
    time_range: str
    camera: str
    action: str
    line: str
    interaction: str = ""


class ScriptBody(BaseModel):
    title: str
    hook: str = Field(description="0-15 秒钩子口播")
    duration_hint: str
    shots: list[Shot] = Field(min_length=5)
    cta: str


class CoverPrompt(BaseModel):
    style: str
    prompt: str


class RiskItem(BaseModel):
    level: str = Field(description="high / mid / low")
    category: str
    detail: str
    suggestion: str


class ScriptBundle(BaseModel):
    script: ScriptBody
    cover_prompts: list[CoverPrompt] = Field(min_length=6, max_length=6)
    risks: list[RiskItem]


class CalendarExtract(BaseModel):
    title: str
    start_date: str = Field(description="YYYY-MM-DD，未知则空")
    end_date: str = Field(description="YYYY-MM-DD，未知则空")
    location: str
    vlog_fit: str
    commercial: str
