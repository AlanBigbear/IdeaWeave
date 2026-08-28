from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut, TrialLoginIn, UserOut
from app.services import auth as auth_service
from app.services import trial as trial_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    _, token = auth_service.register_user(db, payload)
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    _, token = auth_service.login_user(db, payload)
    return TokenOut(access_token=token)


@router.post("/trial", response_model=TokenOut)
def trial(
    request: Request,
    payload: TrialLoginIn | None = None,
    db: Session = Depends(get_db),
):
    trial_service.limit_trial_login(request)
    account = payload.account if payload else "tech"
    _, token = trial_service.trial_login(db, account)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id,
        username=user.username,
        active_persona_id=user.active_persona_id,
        created_at=user.created_at,
        is_trial=trial_service.is_trial_user(user),
    )
