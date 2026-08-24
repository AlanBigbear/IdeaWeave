"""Copy local SQLite (backend/data/bstar.db) into MySQL ideaweave. Prints counts only."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url

BACKEND = Path(__file__).resolve().parents[1]
SQLITE_PATH = BACKEND / "data" / "bstar.db"
SECRETS_PATH = BACKEND / "data" / "secrets.json"
MYSQL_URL = "mysql+pymysql://root:123456@10.23.36.149:3306/ideaweave?charset=utf8mb4"

INSERT_ORDER = [
    "users",
    "personas",
    "user_settings",
    "inspirations",
    "topics",
    "idea_sessions",
    "scripts",
    "calendar_events",
]


def load_env_url() -> str:
    env = BACKEND / ".env"
    if not env.exists():
        return MYSQL_URL
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL=") and "mysql" in line:
            return line.split("=", 1)[1].strip()
    return MYSQL_URL


def sqlite_rows(conn: sqlite3.Connection, table: str) -> tuple[list[str], list[dict]]:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    rows = []
    for row in conn.execute(f"SELECT * FROM {table}").fetchall():
        rows.append({cols[i]: row[i] for i in range(len(cols))})
    return cols, rows


def mysql_columns(engine, table: str) -> set[str]:
    return {c["name"] for c in inspect(engine).get_columns(table)}


def main() -> int:
    if not SQLITE_PATH.exists():
        print(f"missing sqlite {SQLITE_PATH}")
        return 1
    url = load_env_url()
    print("target", make_url(url).render_as_string(hide_password=True))

    src = sqlite3.connect(SQLITE_PATH)
    src.row_factory = sqlite3.Row
    dst = create_engine(url, connect_args={"connect_timeout": 8}, pool_pre_ping=True)

    import app.models.entities  # noqa: F401
    from app.core.database import Base

    Base.metadata.create_all(bind=dst)

    secrets: dict[str, str] = {}
    if SECRETS_PATH.exists():
        secrets = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))

    with dst.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        existing = set(inspect(dst).get_table_names())
        for table in reversed(INSERT_ORDER):
            if table in existing:
                conn.execute(text(f"DELETE FROM `{table}`"))
        copied: dict[str, int] = {}
        for table in INSERT_ORDER:
            if table not in existing and table not in {t.name for t in Base.metadata.sorted_tables}:
                continue
            src_cols, rows = sqlite_rows(src, table)
            dest_cols = mysql_columns(dst, table)
            use_cols = [c for c in src_cols if c in dest_cols]
            n = 0
            for row in rows:
                payload = {k: row[k] for k in use_cols}
                for key, value in list(payload.items()):
                    if value is None and key not in {
                        "active_persona_id",
                        "inspiration_id",
                        "topic_id",
                        "idea_session_id",
                        "selected_index",
                        "skill_generated_at",
                    }:
                        payload[key] = ""
                if table == "user_settings" and "llm_api_key" in dest_cols:
                    uid = str(payload.get("user_id", ""))
                    if uid in secrets and not (payload.get("llm_api_key") or "").strip():
                        payload["llm_api_key"] = secrets[uid]
                    payload.setdefault("llm_api_key", "")
                if table == "topics":
                    payload.setdefault("priority", "mid")
                    payload.setdefault("tags", "[]")
                colnames = ", ".join(f"`{k}`" for k in payload)
                params = ", ".join(f":{k}" for k in payload)
                conn.execute(text(f"INSERT INTO `{table}` ({colnames}) VALUES ({params})"), payload)
                n += 1
            copied[table] = n
            if n and "id" in dest_cols:
                max_id = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM `{table}`")).scalar()
                conn.execute(text(f"ALTER TABLE `{table}` AUTO_INCREMENT = {int(max_id) + 1}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print("copied", copied)
    src.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
