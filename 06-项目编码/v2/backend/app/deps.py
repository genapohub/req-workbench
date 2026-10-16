from __future__ import annotations
import hashlib
import secrets
import time

from fastapi import Request, HTTPException

from app.config import COOKIE
from app.database import db, row, put


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.scrypt(password=pw.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return f"scrypt${salt}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
        computed = hashlib.scrypt(password=pw.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
        return secrets.compare_digest(computed.hex(), dk)
    except Exception:
        return False


def create_session(conn, user_id: str):
    sid = secrets.token_hex(24)
    expires = int(time.time()) + 60 * 60 * 24 * 7
    put(conn, "sessions", {"id": sid, "user_id": user_id, "expires": expires})
    return sid, expires


def get_session_user(request: Request):
    sid = request.cookies.get(COOKIE)
    if not sid:
        return None
    with db() as conn:
        s = row(conn, "sessions", sid)
        if not s or s.get("expires", 0) < int(time.time()):
            return None
        return row(conn, "users", s["user_id"])


def current_user(request: Request) -> dict:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")
    return user


def role_permissions(conn, user: dict) -> set:
    perms: set[str] = set()
    for rid in user.get("role_ids", []):
        role = row(conn, "roles", rid)
        if role:
            perms.update(role.get("permissions", []))
    return perms


def require_perm(perm: str):
    def dep(request: Request) -> dict:
        user = current_user(request)
        with db() as conn:
            perms = role_permissions(conn, user)
        if perm not in perms:
            raise HTTPException(status_code=403, detail="无权限：缺少 " + perm)
        return user

    return dep


def public_user(u: dict) -> dict:
    return {k: v for k, v in u.items() if k != "password"}
