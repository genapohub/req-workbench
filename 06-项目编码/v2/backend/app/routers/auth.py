from __future__ import annotations
import json
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import COOKIE, MENUS
from app.database import db, row, rows, delete, put
from app.deps import verify_password, create_session, get_session_user, role_permissions, public_user
from app.resp import ok, fail
from app.schemas import LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])


def _find_user_by_username(conn, username: str):
    for r in rows(conn, "users"):
        if r.get("username") == username:
            return r
    return None


@router.post("/login")
def login(body: LoginIn):
    with db() as conn:
        user = _find_user_by_username(conn, body.username)
        if not user or not verify_password(body.password, user.get("password", "")):
            return fail(1002, "账号或密码错误", 401)
        if user.get("status") == "disabled":
            return fail(1003, "账号已禁用", 403)
        sid, expires = create_session(conn, user["id"])
    resp = ok({"token": sid, "user": public_user(user)})
    resp.set_cookie(
        COOKIE, sid, httponly=True, samesite="lax",
        max_age=max(0, expires - int(time.time())), path="/",
    )
    return resp


@router.post("/logout")
def logout(request: Request):
    sid = request.cookies.get(COOKIE)
    if sid:
        with db() as conn:
            delete(conn, "sessions", sid)
    resp = ok({})
    resp.delete_cookie(COOKIE, path="/")
    return resp


@router.get("/me")
def me(request: Request):
    user = get_session_user(request)
    if not user:
        return fail(1001, "未登录或会话已过期", 401)
    with db() as conn:
        perms = role_permissions(conn, user)
    menus = [m for m in MENUS if m["permission"] in perms]
    return ok({"user": public_user(user), "permissions": sorted(perms), "menus": menus})
