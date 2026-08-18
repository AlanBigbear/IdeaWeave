from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import expand_script_chain, invoke_or_502
from app.models import IdeaSession, Script, User
from app.providers.comments import resolve_comments
from app.schemas import ExpandScriptIn, ScriptOut
from app.services.common import dumps, loads, require_persona


def script_to_out(row: Script) -> ScriptOut:
    return ScriptOut(
        id=row.id,
        topic_id=row.topic_id,
        idea_session_id=row.idea_session_id,
        outline=row.outline,
        shot_list=row.shot_list,
        comments_text=row.comments_text,
        script=loads(row.script_json, {}),
        cover_prompts=loads(row.cover_prompts_json, []),
        risks=loads(row.risks_json, []),
        created_at=row.created_at,
    )


def expand(db: Session, user: User, payload: ExpandScriptIn) -> ScriptOut:
    persona = require_persona(db, user)
    idea_hint = "无"
    if payload.idea_session_id:
        session = db.get(IdeaSession, payload.idea_session_id)
        if session is None or session.user_id != user.id:
            raise HTTPException(status_code=404, detail="创意会话不存在")
        ideas = loads(session.ideas_json, [])
        if session.selected_index is not None and session.selected_index < len(ideas):
            idea_hint = dumps(ideas[session.selected_index])
        else:
            idea_hint = dumps(ideas)
    _, comments = resolve_comments(payload.use_mock_comments, payload.comments_text)
    comments_blob = "\n".join(f"- {item}" for item in comments) or "（无评论）"
    llm = build_llm(db, user, temperature=0.55)
    bundle = invoke_or_502(
        expand_script_chain(llm, persona),
        {
            "outline": payload.outline,
            "shot_list": payload.shot_list or "未提供，请按体验派长视频自行补全拍摄要点",
            "comments": comments_blob,
            "idea_hint": idea_hint,
        },
    )
    row = Script(
        user_id=user.id,
        topic_id=payload.topic_id,
        idea_session_id=payload.idea_session_id,
        outline=payload.outline,
        shot_list=payload.shot_list,
        comments_text=comments_blob,
        script_json=dumps(bundle.script.model_dump()),
        cover_prompts_json=dumps([item.model_dump() for item in bundle.cover_prompts]),
        risks_json=dumps([item.model_dump() for item in bundle.risks]),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return script_to_out(row)


def list_scripts(db: Session, user: User) -> list[ScriptOut]:
    rows = db.query(Script).filter(Script.user_id == user.id).order_by(Script.id.desc()).all()
    return [script_to_out(row) for row in rows]


def get_script(db: Session, user: User, script_id: int) -> ScriptOut:
    row = db.get(Script, script_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return script_to_out(row)
