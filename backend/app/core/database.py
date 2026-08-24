import logging
from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.exports_dir.mkdir(parents=True, exist_ok=True)

_using_sqlite_fallback = False


def _mysql_connect_args() -> dict:
    return {"connect_timeout": settings.mysql_connect_timeout}


def ensure_database(url_str: str) -> None:
    url = make_url(url_str)
    if not url.drivername.startswith("mysql") or not url.database:
        return
    dbname = url.database
    admin = url.set(database="")
    admin_engine = create_engine(
        admin,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        connect_args=_mysql_connect_args(),
    )
    try:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        admin_engine.dispose()


def _probe_mysql(url_str: str) -> None:
    probe = create_engine(
        url_str,
        pool_pre_ping=True,
        connect_args=_mysql_connect_args(),
    )
    try:
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        probe.dispose()


def _build_engine() -> Engine:
    global _using_sqlite_fallback
    url = settings.sqlalchemy_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
    try:
        ensure_database(url)
        _probe_mysql(url)
        logger.info("Using MySQL %s", make_url(url).render_as_string(hide_password=True))
        return create_engine(url, pool_pre_ping=True, connect_args=_mysql_connect_args(), pool_recycle=3600)
    except Exception as exc:
        if not settings.mysql_fallback_sqlite:
            raise
        _using_sqlite_fallback = True
        sqlite_url = f"sqlite:///{settings.db_path}"
        logger.warning(
            "MySQL unreachable (%s). Falling back to SQLite %s. "
            "Check VPN / 3306 firewall / bind-address on the MySQL host.",
            exc.__class__.__name__,
            settings.db_path,
        )
        return create_engine(sqlite_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def db_info() -> dict:
    return {
        "url": engine.url.render_as_string(hide_password=True),
        "fallback_sqlite": _using_sqlite_fallback,
    }


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_schema() -> None:
    extras = {
        "personas": {
            "zone": "VARCHAR(64) DEFAULT ''",
            "content_style": "VARCHAR(200) DEFAULT ''",
            "update_freq": "VARCHAR(64) DEFAULT ''",
            "comment_style": "TEXT",
            "skill_prompt": "TEXT",
            "skill_brief_json": "TEXT",
            "skill_generated_at": "DATETIME NULL",
        },
        "calendar_events": {
            "source": "VARCHAR(32) DEFAULT 'extract'",
        },
        "topics": {
            "priority": "VARCHAR(16) DEFAULT 'mid'",
            "tags": "TEXT",
        },
        "user_settings": {
            "llm_api_key": "TEXT",
        },
    }
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in extras.items():
            if table not in tables:
                continue
            existing = {col["name"] for col in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
        if "user_settings" in tables:
            conn.execute(
                text(
                    "UPDATE user_settings SET llm_model = :model "
                    "WHERE llm_model IN ('deepseek-chat', 'DeepSeek-V4-Flash-0731', '')"
                ),
                {"model": settings.default_llm_model},
            )
            conn.execute(
                text(
                    "UPDATE user_settings SET llm_base_url = :url "
                    "WHERE llm_base_url IN ('https://api.deepseek.com', 'https://api.deepseek.com/', '')"
                ),
                {"url": settings.default_llm_base_url},
            )
