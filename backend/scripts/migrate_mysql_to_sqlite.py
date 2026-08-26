"""Copy MySQL ideaweave -> local SQLite backend/data/bstar.db. Prints counts only.

用法:
    cd backend && .venv/bin/python3 scripts/migrate_mysql_to_sqlite.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url

BACKEND = Path(__file__).resolve().parents[1]
SQLITE_PATH = BACKEND / "data" / "bstar.db"
MYSQL_URL = "mysql+pymysql://root:123456@10.23.36.149:3306/ideaweave?charset=utf8mb4"

# 按外键依赖顺序插入
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

# 允许为 NULL 的列（外键/可选整数），迁移时不要强行填空串
NULLABLE_COLS = {
    "active_persona_id",
    "inspiration_id",
    "topic_id",
    "idea_session_id",
    "selected_index",
    "skill_generated_at",
}


def load_env_url() -> str:
    env = BACKEND / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL=") and "mysql" in line:
                return line.split("=", 1)[1].strip()
    return MYSQL_URL


def norm(v):
    """SQLite 不接受 datetime 对象，转成可解析的字符串。"""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    return v


def main() -> int:
    url = load_env_url()
    print("source", make_url(url).render_as_string(hide_password=True))
    print("target", SQLITE_PATH)

    src = create_engine(url, connect_args={"connect_timeout": 8}, pool_pre_ping=True)

    sys.path.insert(0, str(BACKEND))
    import app.models.entities  # noqa: F401
    from app.core.database import Base

    dst = create_engine(f"sqlite:///{SQLITE_PATH}")
    Base.metadata.create_all(bind=dst)

    src_insp = inspect(src)
    dst_insp = inspect(dst)
    src_tables = set(src_insp.get_table_names())
    dst_tables = {t.name for t in Base.metadata.sorted_tables}

    # 读 MySQL 全部数据到内存
    data: dict[str, list[dict]] = {}
    with src.connect() as conn:
        for table in INSERT_ORDER:
            if table not in src_tables:
                continue
            cols = [c["name"] for c in src_insp.get_columns(table)]
            rows = [
                dict(zip(cols, row))
                for row in conn.execute(text(f"SELECT * FROM `{table}`"))
            ]
            data[table] = rows

    # 写 SQLite（先清空旧数据，再按依赖顺序插入）
    copied: dict[str, int] = {}
    with dst.begin() as conn:
        for table in reversed(INSERT_ORDER):
            if table in data and table in dst_tables:
                conn.execute(text(f"DELETE FROM {table}"))
        for table in INSERT_ORDER:
            if table not in data or table not in dst_tables:
                continue
            dst_cols = {c["name"] for c in dst_insp.get_columns(table)}
            for row in data[table]:
                payload = {k: norm(v) for k, v in row.items() if k in dst_cols}
                for key, value in list(payload.items()):
                    if value is None and key not in NULLABLE_COLS:
                        payload[key] = ""
                colnames = ", ".join(f'"{k}"' for k in payload)
                params = ", ".join(f":{k}" for k in payload)
                conn.execute(text(f"INSERT INTO {table} ({colnames}) VALUES ({params})"), payload)
            copied[table] = len(data[table])
            print(f"  {table}: {len(data[table])} rows")

    print("copied", copied)
    return 0


if __name__ == "__main__":
    sys.exit(main())
