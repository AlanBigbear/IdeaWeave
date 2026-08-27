import logging
from typing import get_args, get_origin

from fastapi import HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.chains.schemas import (
    CalendarCaptureBundle,
    CalendarExtract,
    ExtractedTopic,
    IdeaBundle,
    PersonaSkill,
    ScriptBundle,
)
from app.prompts.personas import persona_skill_fact_sheet, persona_system_prompt


class TolerantPydanticOutputParser(PydanticOutputParser):
    """容错版 PydanticOutputParser。

    模型偶发会把「只有一个 list 字段」的 JSON 对象直接输出成裸数组，
    例如 IdeaBundle{ideas:[...]} 被输出成 [{...}, ...]。这里自动包回该字段再校验，
    其余情况原样抛错，不掩盖真正的格式问题。
    """

    def _parse_obj(self, obj):
        if isinstance(obj, list):
            wrapped = self._wrap_bare_list(obj)
            if wrapped is not None:
                obj = wrapped
        return super()._parse_obj(obj)

    def _wrap_bare_list(self, data):
        list_fields = [
            name
            for name, field in self.pydantic_object.model_fields.items()
            if get_origin(field.annotation) is list
        ]
        if len(list_fields) == 1:
            return {list_fields[0]: data}
        return None


def _field_spec(ftype) -> str:
    origin = get_origin(ftype)
    if origin is list:
        args = get_args(ftype)
        inner = args[0] if args else str
        if isinstance(inner, type) and issubclass(inner, BaseModel):
            return "对象数组，每项[" + _model_spec(inner) + "]"
        return "字符串数组"
    if isinstance(ftype, type) and issubclass(ftype, BaseModel):
        return "对象{" + _model_spec(ftype) + "}"
    if ftype is int:
        return "整数"
    return "字符串"


def _model_spec(model: type[BaseModel]) -> str:
    parts = []
    for name, field in model.model_fields.items():
        spec = _field_spec(field.annotation)
        desc = (field.description or "").strip()
        if desc:
            desc = desc.split("。")[0][:30]
            spec += f"（{desc}）"
        parts.append(f"{name}:{spec}")
    return "；".join(parts)


def compact_format_instructions(schema: type[BaseModel]) -> str:
    """替代 PydanticOutputParser.get_format_instructions() 的紧凑中文版，省 60-80% token。"""
    return (
        "严格输出一个 JSON 对象（禁止 Markdown 代码块、注释或多余文字），字段：\n"
        + _model_spec(schema)
    )


def _chain(llm: ChatOpenAI, persona, schema, human: str):
    parser = TolerantPydanticOutputParser(pydantic_object=schema)
    prompt = ChatPromptTemplate.from_messages(
        [
            # format_spec 用 partial 注入：partial 值不参与模板解析，说明文字里的花括号安全
            ("system", "{system}\n{format_spec}"),
            ("human", human),
        ]
    ).partial(system=persona_system_prompt(persona), format_spec=compact_format_instructions(schema))
    return (prompt | llm), parser


def extract_topic_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        ExtractedTopic,
        "从 UP 主提供的爆款摘要或抓取的网页正文中，精准提炼一个可入库选题。\n"
        "做「忠实的信息抽取 + 适配人设的判断」，不要脑补原文没有的事实。\n\n"
        "质量规则：\n"
        "1. highlights 必须逐条能在原文找到依据——尽量保留原文的具体事实、数字、金句或冲突点，"
        "压缩成 ≤25 字，禁止编造或写「放哪篇都行」的空话；\n"
        "2. 标题要抓住原文最核心、最具体的一点（关键数字/结论/反差），动词开头、≤24 字；\n"
        "3. feasibility 只按「拍摄成本与门槛」判断：明显要跨城/授权/长周期/高投入才给 deferred，"
        "否则 quick；若原文与该 UP 主人设不匹配，在 why 说明冲突点并给 deferred；\n"
        "4. cost_note ≤40 字写清主要成本/门槛；why ≤60 字写「为什么值得做 / 为什么不值得立刻做」；\n"
        "5. 若原文是广告、公告或信息量过低，在 why 里说明并给 deferred。\n"
        "feasibility 只能是 quick 或 deferred。\n"
        "来源备注：{source_note}\n{truncated_note}内容：\n{raw_text}",
    )


def diverge_ideas_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        IdeaBundle,
        "这是编导面试考核：根据一个模糊想法，给出恰好 3 个差异化创意。\n"
        "要求：\n"
        "1. 三个方案必须在角度、受众、拍摄成本上明显不同，且都能拍成 B 站中长视频；\n"
        "2. 每个方案必须贴着该 UP 主的人设展开：角度落在其分区内、受众对齐其粉丝画像、"
        "成本符合其更新节奏（见系统指令的人设信息）；\n"
        "3. 每个方案的 hook 必须套用专属 Skill 里的钩子公式之一；\n"
        "4. 每个字段 ≤50 字，title ≤16 字，说人话不写套话。\n"
        "关联选题：{topic_hint}\n模糊想法：\n{vague_idea}",
    )


def expand_script_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        ScriptBundle,
        "把大纲扩写成符合该 UP 主视频形态（见系统指令）的完整拍摄脚本。\n"
        "要求：\n"
        "1. 全篇必须贴着该 UP 主的人设写：选题角度落在其分区、语言遵守 Skill 的"
        "语言风格规则、台词浓度按其受众调整——换一个 UP 主这套稿子就不该能用；\n"
        "2. 必须包含：0-15 秒钩子（套用专属钩子公式之一）、8-14 个分镜（镜头/动作/台词）、"
        "弹幕或三连互动（按 Skill 的互动方式写）；\n"
        "3. 每条台词 ≤80 字，interaction 没有可埋的点就留空，不要硬凑；\n"
        "4. 结合评论里的真实问题改脚本，不要无视评论；\n"
        "5. 同时给出 6 套中文封面生图 Prompt（只出提示词，不生图，每条 ≤60 字），"
        "以及 2-4 条审核风险预警（夸大、未核实体验、广告未披露、引战等）。\n"
        "关联创意：{idea_hint}\n大纲：\n{outline}\n拍摄清单：\n{shot_list}\n评论要点：\n{comments}",
    )


def extract_calendar_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        CalendarExtract,
        "从热点/展会文本中抽取日历字段。\n"
        f"今天：{{today}}\n"
        "规则：相对日期（如「下周六」）按今天换算成 YYYY-MM-DD；"
        "未知日期留空，禁止猜测；标题用事件全名（含城市/主办方），≤40字；"
        "vlog_fit 写清为什么适合该 UP 主 + 具体拍法，≤60字；commercial 只写确有机会的一条，≤30字，没有留空。\n"
        "文本：\n{raw_text}",
    )


def capture_calendar_chain(llm: ChatOpenAI, persona):
    parser = TolerantPydanticOutputParser(pydantic_object=CalendarCaptureBundle)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system}\n{format_spec}"),
            (
                "human",
                "请为这个 UP 主捕捉「未来 30 天」能拍、且「有意思」的热点，尽量多给。\n"
                "今天：{today}\n窗口截止（含）：{until}\n\n"
                "两类都要挖：\n"
                "1. 有时效的正式活动：展会/赛事/演唱会/漫展/新品发布/平台大促等；\n"
                "2. 话题型热点：网络热梗、平台挑战、影视综新番新游、社会情绪话题、节日新玩法等"
                "——这类没有精确日期也没关系，落到窗口内一个合理日子即可。\n\n"
                "硬规则：\n"
                "1. 优先挑有「冲突 / 反差 / 情绪点」的，能做「值不值得」「避坑」「第一视角体验」"
                "「省钱爽点」这类选题，别给平淡的信息播报；\n"
                "2. 每条都贴合这个人设的分区/风格/受众；vlog_fit 写清「有意思的点 + 具体拍法」，≤60 字；"
                "commercial 只写确有机会的一条，≤30 字，没有就留空；\n"
                "3. 正式活动尽量用你确定存在或有把握的（拿不准具体日期就写近似值或留空），"
                "话题型热点不要求精确日期；\n"
                "4. start_date、end_date 用 YYYY-MM-DD，都要落在 {today} 至 {until} 内；\n"
                "5. 不要重复已有标题：{existing}\n"
                "6. 季节节点仅作提示，可参考也可跳过，不要原样照抄：{seasonal}\n\n"
                "输出 6-10 条；别为了凑数硬编一个不存在的具体活动。",
            ),
        ]
    ).partial(
        system=persona_system_prompt(persona),
        format_spec=compact_format_instructions(CalendarCaptureBundle),
    )
    return (prompt | llm), parser


def generate_persona_skill_chain(llm: ChatOpenAI, persona):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一位资深 B 站内容编导架构师，擅长把创作者的零散人设信息"
                "编译成一份可直接驱动 AI 编导的「专属 Skill」。输出必须具体、可执行、有辨识度，禁止空话套话。默认中文。",
            ),
            (
                "human",
                "请基于下面的 UP 主人设信息，编译一份专属编导 Skill。"
                "这份 Skill 之后会作为 system prompt 驱动该 UP 主的全部创作任务"
                "（爆点提取、创意发散、脚本扩写、热点规划），所以每一条都要带上这个人设的具体特征，"
                "换一个分区或风格的 UP 主来就不该适用。\n\n"
                "要求（严格控制篇幅，超字数视为不合格）：\n"
                "1. positioning：一句话频道定位，拍什么、给谁看、凭什么被记住，≤40字；\n"
                "2. hook_formula：3 个专属钩子公式，具体到句式结构，每个 ≤40字，禁止「提出问题引发思考」这类通用模板；\n"
                "3. tone_rules：3-4 条语言风格规则（词汇、句长、情绪、禁用表达），每条 ≤25字；\n"
                "4. topic_preferences：2-4 条选题取舍（追什么、不碰什么、短平快/高成本怎么分），每条 ≤35字；\n"
                "5. script_structure：开头/中段/结尾的时间轴骨架，分号分隔要点，≤120字；\n"
                "6. interaction_style：口播互动预埋 + 评论区运营，≤80字；\n"
                "7. red_lines：3-5 条内容红线，每条 ≤20字；\n"
                "8. system_prompt：把以上融会贯通写成 250-350 字第二人称指令"
                "（「你是为 UP 主『xx』工作的虚拟编导…」），可直接作为 system prompt 使用，"
                "不要出现「以上」「如下」这类指代词。\n\n"
                f"人设信息：\n{persona_skill_fact_sheet(persona)}\n\n"
                "{format_spec}",
            ),
        ]
    ).partial(format_spec=compact_format_instructions(PersonaSkill))
    return (prompt | llm), TolerantPydanticOutputParser(pydantic_object=PersonaSkill)


def invoke_or_502(chain, payload):
    try:
        return chain.invoke(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logging.getLogger(__name__).exception("LLM 调用失败")
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}") from exc


def _chunk_reasoning(chunk) -> str:
    """DeepSeek 推理模型会把思考过程放在 reasoning_content，普通模型则没有。"""
    for meta in (chunk.additional_kwargs, chunk.response_metadata):
        if isinstance(meta, dict) and meta.get("reasoning_content"):
            return str(meta["reasoning_content"])
    return ""


def run_chain(raw, parser, payload, on_delta=None):
    """跑一条 prompt|llm 链。传入 on_delta 时走流式，把思考/正文增量逐段回调出去。

    on_delta(kind, text)：kind 为 "thinking"（推理模型的思考过程）或 "content"（正文/JSON）。
    返回解析好的 Pydantic 对象。
    """
    if on_delta is None:
        return invoke_or_502(raw | parser, payload)

    parts: list[str] = []
    try:
        for chunk in raw.stream(payload):
            reasoning = _chunk_reasoning(chunk)
            content = chunk.content or ""
            if reasoning:
                on_delta("thinking", reasoning)
            if content:
                on_delta("content", content)
                parts.append(content)
        return parser.parse("".join(parts))
    except HTTPException:
        raise
    except Exception as exc:
        logging.getLogger(__name__).exception("LLM 流式调用失败")
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}") from exc
