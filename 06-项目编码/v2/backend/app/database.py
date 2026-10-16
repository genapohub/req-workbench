from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DATA, DB

TABLES = ["users", "roles", "projects", "requirements", "sessions"]


@contextmanager
def db():
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        for t in TABLES:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {t}(id TEXT PRIMARY KEY, body TEXT)")


def put(conn, table: str, item: dict):
    conn.execute(
        f"INSERT INTO {table}(id, body) VALUES(?, ?) "
        f"ON CONFLICT(id) DO UPDATE SET body=excluded.body",
        (item["id"], json.dumps(item, ensure_ascii=False)),
    )


def row(conn, table: str, id: str):
    r = conn.execute(f"SELECT body FROM {table} WHERE id=?", (id,)).fetchone()
    return json.loads(r["body"]) if r else None


def rows(conn, table: str):
    return [json.loads(r["body"]) for r in conn.execute(f"SELECT body FROM {table}").fetchall()]


def get(table: str, id: str):
    with db() as conn:
        return row(conn, table, id)


def get_all(table: str):
    with db() as conn:
        return rows(conn, table)


def delete(conn, table: str, id: str):
    conn.execute(f"DELETE FROM {table} WHERE id=?", (id,))
