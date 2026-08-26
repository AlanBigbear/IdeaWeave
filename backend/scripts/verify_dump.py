"""Verify deploy/ideaweave_full.sql round-trips correctly.

把 dump 导入源 MySQL 上一个临时库 ideaweave_verify_tmp，逐表对比行数 + 内容 MD5。
全部 MATCH 才说明 dump 无误。用完自动删临时库。

用法:
    cd backend && .venv/bin/python3 scripts/verify_dump.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pymysql
from sqlalchemy.engine.url import make_url

BACKEND = Path(__file__).resolve().parents[1]
PROJECT = BACKEND.parent
FULL = PROJECT / "deploy" / "ideaweave_full.sql"
ENV = BACKEND / ".env"
DEFAULT_URL = "mysql+pymysql://root:123456@10.23.36.149:3306/ideaweave?charset=utf8mb4"

TABLES = [
    "users",
    "personas",
    "user_settings",
    "inspirations",
    "topics",
    "idea_sessions",
    "scripts",
    "calendar_events",
]

TMP_DB = "ideaweave_verify_tmp"
CHARSET = "utf8mb4"


def load_url() -> str:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val
    return DEFAULT_URL


def connect(url, database=None):
    return pymysql.connect(
        host=url.host,
        port=url.port or 3306,
        user=url.username,
        password=url.password or "",
        database=database,
        charset=CHARSET,
        connect_timeout=8,
    )


def table_hash(cur, table: str) -> tuple[int, str]:
    cur.execute(f"SELECT * FROM `{table}` ORDER BY id")
    rows = cur.fetchall()
    h = hashlib.md5()
    h.update(str(len(rows)).encode())
    for row in rows:
        for v in row:
            if v is None:
                h.update(b"\x00N")
            elif isinstance(v, (bytes, bytearray)):
                h.update(b"\x00b" + bytes(v))
            else:
                h.update(b"\x00s" + str(v).encode())
    return len(rows), h.hexdigest()


def split_statements(text: str) -> list[str]:
    """按行累积，行尾以 ; 结尾即一条语句。dump 中换行已转义为 \\n，故多行只出现在 CREATE TABLE。"""
    stmts: list[str] = []
    buf: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        buf.append(line)
        if s.endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    if buf:
        stmts.append("\n".join(buf))
    return stmts


def main() -> int:
    url = make_url(load_url())
    src = connect(url, url.database)
    admin = connect(url)  # 无默认库，用于建/删临时库

    # 源库各表 (行数, 哈希)
    expected: dict[str, tuple[int, str]] = {}
    with src.cursor() as cur:
        for t in TABLES:
            expected[t] = table_hash(cur, t)

    dst = None
    try:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{TMP_DB}`")
            cur.execute(
                f"CREATE DATABASE `{TMP_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        admin.commit()

        dst = connect(url, TMP_DB)
        stmts = split_statements(FULL.read_text(encoding="utf-8"))
        with dst.cursor() as cur:
            for stmt in stmts:
                cur.execute(stmt)
        dst.commit()

        print(f"{'table':18} {'dump':>5} {'source':>6}  {'content':>7}")
        print("-" * 45)
        all_ok = True
        with dst.cursor() as cur:
            for t in TABLES:
                n, h = table_hash(cur, t)
                en, eh = expected[t]
                ok = n == en and h == eh
                all_ok = all_ok and ok
                print(f"{t:18} {n:5} {en:6}  {'MATCH' if ok else 'DIFF ✗'}")
        print("-" * 45)
        print("结论:", "全部一致，dump 无误 ✅" if all_ok else "存在差异，需排查 ✗")
        return 0 if all_ok else 1
    finally:
        if dst is not None:
            dst.close()
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{TMP_DB}`")
        admin.commit()
        admin.close()
        src.close()


if __name__ == "__main__":
    sys.exit(main())
