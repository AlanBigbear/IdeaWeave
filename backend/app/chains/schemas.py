from pydantic import BaseModel, Field


class PersonaSkill(BaseModel):
    positioning: str = Field(description="一句话频道定位：拍什么、给谁看、凭什么被记住，不超过 40 字")
    hook_formula: list[str] = Field(
        min_length=3, max_length=3,
        description="3 个专属开头钩子公式，具体到句式，每个不超过 40 字",
    )
    tone_rules: list[str] = Field(min_length=3, max_length=4, description="3-4 条语言风格规则，每条不超过 25 字")
    topic_preferences: list[str] = Field(
        min_length=2, max_length=4, description="2-4 条选题取舍，每条不超过 35 字",
    )
    script_structure: str = Field(description="开头/中段/结尾的时间轴骨架，分号分隔要点，不超过 120 字")
    interaction_style: str = Field(description="口播互动预埋与评论区运营方式，不超过 80 字")
    red_lines: list[str] = Field(min_length=3, max_length=5, description="3-5 条内容红线，每条不超过 20 字")
    system_prompt: str = Field(
        description="把以上融会贯通写成的第二人称 system prompt，250-350 字，可直接驱动创作任务",
    )


class ExtractedTopic(BaseModel):
    title: str = Field(description="选题标题，动词开头，≤24字")
    highlights: list[str] = Field(min_length=3, max_length=5, description="3-5 个爆点，每条 ≤25字")
    feasibility: str = Field(description="quick 表示短平快可执行，deferred 表示高成本暂缓")
    cost_note: str = Field(description="成本/门槛说明，≤40字")
    why: str = Field(description="为什么值得做或不值得立刻做，≤60字")


class CreativeIdea(BaseModel):
    title: str = Field(description="方案标题，≤16字")
    angle: str = Field(description="切入角度，≤50字")
    audience: str = Field(description="目标受众，≤50字")
    cost: str = Field(description="拍摄成本，≤50字")
    hook: str = Field(description="开头钩子，套用专属钩子公式，≤50字")
    why_different: str = Field(description="差异点，≤50字")


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
    shots: list[Shot] = Field(min_length=6, max_length=14)
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
    location: str = ""
    vlog_fit: str = ""
    commercial: str = ""


class CalendarCaptureBundle(BaseModel):
    events: list[CalendarExtract] = Field(min_length=1, max_length=10)
