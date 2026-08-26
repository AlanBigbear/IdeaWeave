from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import generate_persona_skill_chain, run_chain
from app.models import Persona, User
from app.prompts.personas import PERSONA_OPTIONS, PERSONA_TEMPLATES, get_template
from app.schemas import PersonaIn
from app.services.skill_presets import build_preset_skill, build_preset_skill_from_template, list_preset_templates


def list_user_personas(db: Session, user: User) -> list[Persona]:
    return db.query(Persona).filter(Persona.user_id == user.id).order_by(Persona.id.desc()).all()


def get_owned_persona(db: Session, user: User, persona_id: int) -> Persona:
    persona = db.get(Persona, persona_id)
    if persona is None or persona.user_id != user.id:
        raise HTTPException(status_code=404, detail="人设不存在")
    return persona


def _apply_preset_skill(persona: Persona) -> None:
    preset = build_preset_skill(persona)
    persona.skill_prompt = preset["system_prompt"]
    persona.skill_brief_json = _dump_brief(preset)
    persona.skill_generated_at = datetime.now(timezone.utc)


def _dump_brief(preset: dict) -> str:
    import json

    return json.dumps(preset, ensure_ascii=False)


def generate_skill(db: Session, user: User, persona_id: int, on_delta=None) -> Persona:
    persona = get_owned_persona(db, user, persona_id)
    llm = build_llm(db, user, temperature=0.7, max_tokens=1200)
    raw, parser = generate_persona_skill_chain(llm, persona)
    skill = run_chain(raw, parser, {}, on_delta)
    persona.skill_prompt = skill.system_prompt.strip()
    persona.skill_brief_json = skill.model_dump_json()
    persona.skill_generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(persona)
    return persona


def update_skill(db: Session, user: User, persona_id: int, skill_prompt: str) -> Persona:
    persona = get_owned_persona(db, user, persona_id)
    persona.skill_prompt = skill_prompt.strip()
    db.commit()
    db.refresh(persona)
    return persona


def _persona_fields(payload: PersonaIn) -> dict:
    return payload.model_dump()


def create_persona(db: Session, user: User, payload: PersonaIn) -> Persona:
    persona = Persona(user_id=user.id, **_persona_fields(payload))
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def setup_persona(db: Session, user: User, payload: PersonaIn) -> Persona:
    persona = Persona(user_id=user.id, **_persona_fields(payload))
    db.add(persona)
    db.flush()
    _apply_preset_skill(persona)
    user.active_persona_id = persona.id
    db.commit()
    db.refresh(persona)
    return persona


def apply_preset_skill(db: Session, user: User, persona_id: int, template_key: str | None = None) -> Persona:
    persona = get_owned_persona(db, user, persona_id)
    preset = (
        build_preset_skill_from_template(persona, template_key)
        if template_key
        else build_preset_skill(persona)
    )
    if preset is None:
        raise HTTPException(status_code=404, detail="Skill 模板不存在")
    persona.skill_prompt = preset["system_prompt"]
    persona.skill_brief_json = _dump_brief(preset)
    persona.skill_generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(persona)
    return persona


def preset_templates() -> list[dict]:
    return list_preset_templates()


def activate_template(db: Session, user: User, template_key: str) -> Persona:
    template = get_template(template_key)
    if template is None:
        raise HTTPException(status_code=404, detail="人设模板不存在")
    existing = (
        db.query(Persona)
        .filter(Persona.user_id == user.id, Persona.template_key == template_key)
        .one_or_none()
    )
    fields = {
        "template_key": template["key"],
        "name": template["name"],
        "style_desc": template["style_desc"],
        "audience": template["audience"],
        "video_format": template["video_format"],
        "taboos": template["taboos"],
        "sample_tone": template["sample_tone"],
        "zone": template.get("zone", ""),
        "content_style": template.get("content_style", ""),
        "update_freq": template.get("update_freq", ""),
        "comment_style": template.get("comment_style", ""),
    }
    if existing is None:
        existing = Persona(user_id=user.id, **fields)
        db.add(existing)
        db.flush()
    else:
        for key, value in fields.items():
            setattr(existing, key, value)
    user.active_persona_id = existing.id
    db.commit()
    db.refresh(existing)
    return existing


def activate_persona(db: Session, user: User, persona_id: int) -> Persona:
    persona = db.get(Persona, persona_id)
    if persona is None or persona.user_id != user.id:
        raise HTTPException(status_code=404, detail="人设不存在")
    user.active_persona_id = persona.id
    db.commit()
    db.refresh(persona)
    return persona


def update_persona(db: Session, user: User, persona_id: int, payload: PersonaIn) -> Persona:
    persona = db.get(Persona, persona_id)
    if persona is None or persona.user_id != user.id:
        raise HTTPException(status_code=404, detail="人设不存在")
    for key, value in payload.model_dump().items():
        setattr(persona, key, value)
    db.commit()
    db.refresh(persona)
    return persona


def templates() -> list[dict]:
    return PERSONA_TEMPLATES


def options() -> dict:
    return PERSONA_OPTIONS
