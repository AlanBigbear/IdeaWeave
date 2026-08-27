from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
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
from app.services import jobs as jobs_service
from app.services import persona as persona_service
from app.services.streaming import sse_token_stream

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


@router.post("/{persona_id}/skill/stream")
def generate_persona_skill_stream(
    persona_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    def run(session: Session, on_delta) -> PersonaOut:
        owner = session.get(User, user.id)
        persona = persona_service.generate_skill(session, owner, persona_id, on_delta)
        return PersonaOut.model_validate(persona)

    return StreamingResponse(
        sse_token_stream(run, serialize=lambda r: r.model_dump_json()),
        media_type="text/event-stream",
    )


@router.post("/{persona_id}/skill/async")
def generate_persona_skill_async(
    persona_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    persona_service.get_owned_persona(db, user, persona_id)

    def task() -> dict:
        session = SessionLocal()
        try:
            owner = session.get(User, user.id)
            persona = persona_service.generate_skill(session, owner, persona_id)
            return {"persona": PersonaOut.model_validate(persona).model_dump()}
        finally:
            session.close()

    job_id = jobs_service.submit(f"skill:{user.id}:{persona_id}", task)
    return {"job_id": job_id}


@router.get("/skill-jobs/{job_id}")
def skill_job_status(job_id: str, user: User = Depends(get_current_user)):
    job = jobs_service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    payload: dict = {"status": job.status, "error": job.error, "persona": None}
    if job.status == "done":
        payload["persona"] = job.result.get("persona")
    return payload


@router.put("/{persona_id}/skill", response_model=PersonaOut)
def update_persona_skill(
    persona_id: int,
    payload: PersonaSkillUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return persona_service.update_skill(db, user, persona_id, payload.skill_prompt)


@router.get("/skill-templates")
def skill_templates(user: User = Depends(get_current_user)):
    return persona_service.preset_templates()


@router.post("/{persona_id}/skill/preset", response_model=PersonaOut)
def apply_preset_persona_skill(
    persona_id: int,
    payload: dict | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template_key = (payload or {}).get("template_key")
    return persona_service.apply_preset_skill(db, user, persona_id, template_key)
