from pydantic import BaseModel, Field


class PersonaSkill(BaseModel):
    positioning: str = Field(description="一句话频道定位：拍什么、给谁看、凭什么被记住")
    hook_formula: list[str] = Field(
        min_length=3, max_length=3,
        description="3 个专属开头钩子公式，具体到句式，不用通用模板",
    )
    tone_rules: list[str] = Field(min_length=3, max_length=6, description="3-6 条语言风格规则")
    topic_preferences: list[str] = Field(
        min_length=2, max_length=6, description="该追什么选题、什么选题不碰，短平快/高成本怎么取舍",
    )
    script_structure: str = Field(description="专属脚本结构模板，开头/中段/结尾的时间轴骨架")
    interaction_style: str = Field(description="口播互动预埋与评论区运营方式")
    red_lines: list[str] = Field(min_length=2, max_length=8, description="内容红线清单")
    system_prompt: str = Field(
        description="把以上融会贯通写成的第二人称 system prompt，300-500 字，可直接驱动创作任务",
    )


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
    location: str = ""
    vlog_fit: str = ""
    commercial: str = ""


class CalendarCaptureBundle(BaseModel):
    events: list[CalendarExtract] = Field(min_length=4, max_length=12)
