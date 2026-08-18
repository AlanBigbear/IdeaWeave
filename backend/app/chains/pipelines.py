from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.chains.schemas import CalendarExtract, ExtractedTopic, IdeaBundle, ScriptBundle
from app.prompts.personas import persona_system_prompt


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
        "从 UP 主粘贴的爆款摘要中提取一个可入库选题。"
        "feasibility 只能是 quick 或 deferred。\n来源备注：{source_note}\n摘要：\n{raw_text}",
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


def invoke_or_502(chain, payload):
    try:
        return chain.invoke(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}") from exc
