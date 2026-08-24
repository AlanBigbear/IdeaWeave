from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chains.llm import build_llm
from app.chains.pipelines import generate_persona_skill_chain, invoke_or_502
from app.models import Persona, User
from app.prompts.personas import PERSONA_OPTIONS, PERSONA_TEMPLATES, get_template
from app.schemas import PersonaIn


def list_user_personas(db: Session, user: User) -> list[Persona]:
    return db.query(Persona).filter(Persona.user_id == user.id).order_by(Persona.id.desc()).all()


def get_owned_persona(db: Session, user: User, persona_id: int) -> Persona:
    persona = db.get(Persona, persona_id)
    if persona is None or persona.user_id != user.id:
        raise HTTPException(status_code=404, detail="人设不存在")
    return persona


def generate_skill(db: Session, user: User, persona_id: int) -> Persona:
    persona = get_owned_persona(db, user, persona_id)
    llm = build_llm(db, user, temperature=0.7)
    chain = generate_persona_skill_chain(llm, persona)
    skill = invoke_or_502(chain, {})
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
    user.active_persona_id = persona.id
    db.commit()
    db.refresh(persona)
    return persona


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
