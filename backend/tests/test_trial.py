import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import CalendarEvent, IdeaSession, Inspiration, Persona, Script, Topic, User, UserSettings
from app.services import trial
from app.services.trial import is_reserved_trial_username

ACCOUNTS = ["tech", "anime", "pet"]


@pytest.fixture()
def trial_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'trial.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(trial, "SessionLocal", factory)
    monkeypatch.setattr(trial, "engine", engine)
    monkeypatch.setattr(trial.settings, "trial_enabled", True)
    monkeypatch.setattr(trial.settings, "trial_username", "demo")
    monkeypatch.setattr(trial.settings, "trial_anime_username", "demo-anime")
    monkeypatch.setattr(trial.settings, "trial_pet_username", "demo-pet")
    yield factory
    engine.dispose()


def _counts(db, user_id: int) -> dict[str, int]:
    return {
        "settings": db.query(UserSettings).filter_by(user_id=user_id).count(),
        "personas": db.query(Persona).filter_by(user_id=user_id).count(),
        "inspirations": db.query(Inspiration).filter_by(user_id=user_id).count(),
        "topics": db.query(Topic).filter_by(user_id=user_id).count(),
        "ideas": db.query(IdeaSession).filter_by(user_id=user_id).count(),
        "scripts": db.query(Script).filter_by(user_id=user_id).count(),
        "calendar": db.query(CalendarEvent).filter_by(user_id=user_id).count(),
    }


@pytest.mark.parametrize("key", ACCOUNTS)
def test_reset_provisions_complete_idempotent_baseline(trial_db, key):
    first = trial.reset_trial_account(key)
    assert first is not None
    first_id = first.id
    spec = trial.get_trial_account(key)
    assert spec.username == first.username

    with trial_db() as db:
        user = db.get(User, first_id)
        assert user.active_persona_id is not None
        persona = db.get(Persona, user.active_persona_id)
        assert persona.user_id == user.id
        assert persona.name == spec.persona["name"]
        assert persona.zone == spec.persona["zone"]
        assert persona.skill_prompt
        assert persona.skill_brief_json
        settings_row = db.query(UserSettings).filter_by(user_id=user.id).one()
        assert settings_row.llm_api_key == ""
        assert _counts(db, user.id) == {
            "settings": 1,
            "personas": 1,
            "inspirations": 1,
            "topics": 3,
            "ideas": 1,
            "scripts": 1,
            "calendar": 3,
        }
        topics = db.query(Topic).filter_by(user_id=user.id).order_by(Topic.id).all()
        assert [t.status for t in topics] == ["ready", "inbox", "paused"]
        assert [t.priority for t in topics] == ["high", "mid", "low"]
        assert topics[0].inspiration_id is not None
        assert topics[2].inspiration_id is None
        script = db.query(Script).filter_by(user_id=user.id).one()
        body = json.loads(script.script_json)
        assert 6 <= len(body["shots"]) <= 14
        assert len(json.loads(script.cover_prompts_json)) == 6
        assert len(json.loads(script.risks_json)) == 3
        events = db.query(CalendarEvent).filter_by(user_id=user.id).all()
        assert len(events) == 3
        assert all(e.start_date >= date.today().isoformat() for e in events)
        db.add(Topic(user_id=user.id, title="访客临时选题"))
        db.commit()

    second = trial.reset_trial_account(key)
    assert second.id == first_id
    with trial_db() as db:
        assert _counts(db, first_id)["topics"] == 3
        assert db.query(Topic).filter_by(user_id=first_id, title="访客临时选题").count() == 0


def test_reset_is_isolated_between_accounts_and_normal_users(trial_db):
    with trial_db() as db:
        normal = User(username="normal-user", password_hash="normal-hash")
        db.add(normal)
        db.flush()
        normal_id = normal.id
        db.add(Topic(user_id=normal_id, title="普通用户选题"))
        db.commit()

    users = {}
    for key in ACCOUNTS:
        u = trial.reset_trial_account(key)
        users[key] = u.id
        with trial_db() as db:
            db.add(Topic(user_id=u.id, title=f"{key}临时选题"))
            db.commit()

    trial.reset_trial_account("anime")
    with trial_db() as db:
        assert db.get(User, normal_id).username == "normal-user"
        assert db.query(Topic).filter_by(user_id=normal_id, title="普通用户选题").one()
        assert db.query(Topic).filter_by(user_id=users["tech"], title="tech临时选题").one()
        assert db.query(Topic).filter_by(user_id=users["pet"], title="pet临时选题").one()
        assert db.query(Topic).filter_by(user_id=users["anime"], title="anime临时选题").count() == 0


def test_reset_all_provisions_three_accounts(trial_db):
    results = trial.reset_all_trial_accounts()
    assert set(results) == set(ACCOUNTS)
    with trial_db() as db:
        for key in ACCOUNTS:
            u = db.query(User).filter_by(username=trial.get_trial_account(key).username).one()
            assert u.active_persona_id is not None


def test_reserved_username_detection_case_insensitive():
    assert is_reserved_trial_username("demo")
    assert is_reserved_trial_username(" DEMO ")
    assert is_reserved_trial_username("Demo")
    assert is_reserved_trial_username("demo-anime")
    assert is_reserved_trial_username("DEMO-ANIME")
    assert is_reserved_trial_username("demo-pet")
    assert is_reserved_trial_username("  Demo-Pet  ")
    assert not is_reserved_trial_username("demo2")
    assert not is_reserved_trial_username("正常用户")


def test_trial_login_defaults_tech_and_supports_keys(trial_db):
    with trial_db() as db:
        user, token = trial.trial_login(db)
        assert user.username == "demo"
        assert token
        assert user.active_persona_id is not None
    for key in ("anime", "pet"):
        with trial_db() as db:
            user, token = trial.trial_login(db, key)
            assert user.username == trial.get_trial_account(key).username
            assert token


def test_unknown_account_rejected():
    with pytest.raises(ValueError):
        trial.get_trial_account("hacker")
