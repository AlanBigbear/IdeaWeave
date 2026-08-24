from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    ActivatePersonaIn,
    PersonaIn,
    PersonaOptionsOut,
    PersonaOut,
    PersonaSkillUpdateIn,
    PersonaTemplateOut,
)
from app.services import persona as persona_service

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/options", response_model=PersonaOptionsOut)
def options():
    return persona_service.options()


@router.get("/templates", response_model=list[PersonaTemplateOut])
def templates():
    return persona_service.templates()


@router.get("", response_model=list[PersonaOut])
def list_personas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return persona_service.list_user_personas(db, user)


@router.post("", response_model=PersonaOut)
def create_persona(
    payload: PersonaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.create_persona(db, user, payload)


@router.post("/setup", response_model=PersonaOut)
def setup_persona(
    payload: PersonaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.setup_persona(db, user, payload)


@router.post("/activate", response_model=PersonaOut)
def activate(
    payload: ActivatePersonaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.persona_id:
        return persona_service.activate_persona(db, user, payload.persona_id)
    if payload.template_key:
        return persona_service.activate_template(db, user, payload.template_key)
    raise HTTPException(status_code=400, detail="请提供 template_key 或 persona_id")


@router.put("/{persona_id}", response_model=PersonaOut)
def update_persona(
    persona_id: int,
    payload: PersonaIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.update_persona(db, user, persona_id, payload)


@router.post("/{persona_id}/skill", response_model=PersonaOut)
def generate_persona_skill(
    persona_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.generate_skill(db, user, persona_id)


@router.put("/{persona_id}/skill", response_model=PersonaOut)
def update_persona_skill(
    persona_id: int,
    payload: PersonaSkillUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.update_skill(db, user, persona_id, payload.skill_prompt)
