from fastapi import HTTPException
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
from app.prompts.personas import persona_system_prompt, persona_skill_fact_sheet


def _chain(llm: ChatOpenAI, persona, schema, human: str):
    parser = PydanticOutputParser(pydantic_object=schema)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system}\n请严格按以下 JSON Schema 输出，不要 Markdown。\n{format_instructions}"),
            ("human", human),
        ]
    ).partial(system=persona_system_prompt(persona), format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


def extract_topic_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        ExtractedTopic,
        "从 UP 主提供的爆款摘要或抓取的网页正文中提取一个可入库选题。"
        "若是网页正文，先判断它为什么火、爆点在哪，再归纳成选题。"
        "feasibility 只能是 quick 或 deferred。\n来源备注：{source_note}\n内容：\n{raw_text}",
    )


def diverge_ideas_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        IdeaBundle,
        "这是编导面试考核：根据一个模糊想法，给出恰好 3 个差异化创意。"
        "三个方案必须在角度、受众、拍摄成本上明显不同，且都能拍成 B 站中长视频。\n"
        "关联选题：{topic_hint}\n模糊想法：\n{vague_idea}",
    )


def expand_script_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        ScriptBundle,
        "把大纲扩写成 B 站体验派长视频脚本。"
        "必须包含：0-15 秒钩子、分镜（镜头/动作/台词）、弹幕或三连互动。"
        "结合评论里的真实问题改脚本，不要无视评论。\n"
        "同时给出 6 套中文封面生图 Prompt（只出提示词，不生图），"
        "以及脚本审核风险预警（夸大、未核实体验、广告未披露、引战等）。\n"
        "关联创意：{idea_hint}\n大纲：\n{outline}\n拍摄清单：\n{shot_list}\n评论要点：\n{comments}",
    )


def extract_calendar_chain(llm: ChatOpenAI, persona):
    return _chain(
        llm,
        persona,
        CalendarExtract,
        "从热点/展会文本中抽取日历字段。日期尽量规范成 YYYY-MM-DD。"
        "vlog_fit 说明为什么适合做线下体验 Vlog；commercial 说明商业化机会。\n文本：\n{raw_text}",
    )


def capture_calendar_chain(llm: ChatOpenAI, persona):
    parser = PydanticOutputParser(pydantic_object=CalendarCaptureBundle)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system}\n请严格按以下 JSON Schema 输出，不要 Markdown。\n{format_instructions}"),
            (
                "human",
                "请只捕捉「未来 90 天」且「与该 UP 主人设强相关」的热点。\n"
                "今天：{today}\n窗口截止（含）：{until}\n"
                "人设档案：\n{persona_brief}\n\n"
                "硬规则：\n"
                "1. 每条都必须是这个分区/风格/受众会拍的选题；换一个人设就不该出现。\n"
                "2. vlog_fit 必须写清「为什么适合 TA」，禁止空泛套话。\n"
                "3. 禁止堆无关通用节日。只有能落到该人设具体拍法时才能用节日节点。\n"
                "4. start_date、end_date 必须是 YYYY-MM-DD，事件必须落在 {today} 至 {until} 内。\n"
                "5. 标题要具体（展会名、赛事、平台活动、分区风口），不要只写「开学季」。\n"
                "6. 不要重复已有标题：{existing}\n"
                "7. 可参考的季节节点（按人设筛过，仅作提示，不要原样照抄）：{seasonal}\n"
                "输出 6-10 条。",
            ),
        ]
    ).partial(system=persona_system_prompt(persona), format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


def generate_persona_skill_chain(llm: ChatOpenAI, persona):
    parser = PydanticOutputParser(pydantic_object=PersonaSkill)
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
                "要求：\n"
                "1. positioning：一句话频道定位，说清拍什么、给谁看、凭什么被记住；\n"
                "2. hook_formula：3 个专属开头钩子公式，具体到句式结构，禁止「提出问题引发思考」这类通用模板；\n"
                "3. tone_rules：3-6 条语言风格规则（词汇、句长、情绪浓度、禁用表达）；\n"
                "4. topic_preferences：该追什么选题、什么选题不要碰；结合更新节奏说明短平快与高成本选题怎么取舍；\n"
                "5. script_structure：专属脚本结构模板，按其视频形态给开头/中段/结尾的时间轴骨架；\n"
                "6. interaction_style：口播里怎么预埋互动、评论区怎么运营，符合其评论互动习惯；\n"
                "7. red_lines：内容红线清单，结合其禁忌与 B 站社区审核特点；\n"
                "8. system_prompt：把以上全部融会贯通，写成 300-500 字第二人称指令"
                "（「你是为 UP 主『xx』工作的虚拟编导…」），可直接作为 system prompt 使用，"
                "不要出现「以上」「如下」这类指代词。\n\n"
                f"人设信息：\n{persona_skill_fact_sheet(persona)}\n\n"
                "请严格按以下 JSON Schema 输出，不要 Markdown。\n{format_instructions}",
            ),
        ]
    ).partial(format_instructions=parser.get_format_instructions())
    return prompt | llm | parser


def invoke_or_502(chain, payload):
    try:
        return chain.invoke(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}") from exc
