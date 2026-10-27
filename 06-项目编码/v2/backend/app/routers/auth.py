from __future__ import annotations
import logging
import time

from fastapi import APIRouter, Request

from app.config import COOKIE, MENUS
from app.database import db, row, rows, delete, put
from app.deps import verify_password, hash_password, create_session, get_session_user, role_permissions, public_user
from app.resp import ok, fail
from app.schemas import LoginIn, ChangePasswordIn

logger = logging.getLogger("workbench.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

# 登录防爆破：同一账号连续失败 5 次锁定 10 分钟（内存计数，重启清零）
LOGIN_MAX_FAILURES = 5
LOGIN_LOCK_SECONDS = 600
_login_failures: dict[str, list[float]] = {}


def _lock_remaining(username: str) -> int:
    fails = [t for t in _login_failures.get(username, []) if time.time() - t < LOGIN_LOCK_SECONDS]
    _login_failures[username] = fails
    if len(fails) >= LOGIN_MAX_FAILURES:
        return int(LOGIN_LOCK_SECONDS - (time.time() - fails[0])) or 1
    return 0


def _record_failure(username: str):
    _login_failures.setdefault(username, []).append(time.time())
    logger.warning("登录失败：username=%s 累计失败=%d", username, len(_login_failures[username]))


def _find_user_by_username(conn, username: str):
    for r in rows(conn, "users"):
        if r.get("username") == username:
            return r
    return None


@router.post("/login")
def login(body: LoginIn):
    remaining = _lock_remaining(body.username)
    if remaining > 0:
        return fail(1002, f"连续失败次数过多，账号已锁定，请 {remaining // 60 + 1} 分钟后再试", 429)
    with db() as conn:
        user = _find_user_by_username(conn, body.username)
        if not user or not verify_password(body.password, user.get("password", "")):
            _record_failure(body.username)
            return fail(1002, "账号或密码错误", 401)
        if user.get("status") == "disabled":
            return fail(1003, "账号已禁用", 403)
        _login_failures.pop(body.username, None)
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


def _password_strength_error(pw: str, username: str) -> str | None:
    if len(pw) < 8:
        return "新密码至少 8 位"
    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        return "新密码需同时包含字母和数字"
    if pw == username:
        return "新密码不能与账号相同"
    return None


@router.post("/change-password")
def change_password(request: Request, body: ChangePasswordIn):
    user = get_session_user(request)
    if not user:
        return fail(1001, "未登录或会话已过期", 401)
    if not verify_password(body.old_password, user.get("password", "")):
        return fail(1002, "原密码错误", 401)
    err = _password_strength_error(body.new_password, user.get("username", ""))
    if err:
        return fail(3001, err, 422)
    if body.new_password == body.old_password:
        return fail(3001, "新密码不能与原密码相同", 422)
    current_sid = request.cookies.get(COOKIE)
    with db() as conn:
        user["password"] = hash_password(body.new_password)
        user["must_change_password"] = False
        user["updated_at"] = int(time.time())
        put(conn, "users", user)
        # 改密后失效该账号的其它会话，仅保留当前会话
        for s in rows(conn, "sessions"):
            if s.get("user_id") == user["id"] and s.get("id") != current_sid:
                delete(conn, "sessions", s["id"])
    logger.info("用户自助改密成功：username=%s", user.get("username"))
    return ok({"id": user["id"]})
