from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import now, uid
from app.database import db, row, rows, put, delete
from app.deps import require_perm, hash_password, public_user
from app.resp import ok, fail
from app.schemas import UserIn, UserPatch

router = APIRouter(prefix="/users", tags=["users"])


def _username_exists(conn, username: str, exclude_id: str | None = None) -> bool:
    return any(u.get("username") == username and u.get("id") != exclude_id for u in rows(conn, "users"))


@router.get("")
def list_users(user: dict = Depends(require_perm("users.view"))):
    with db() as conn:
        items = [public_user(u) for u in rows(conn, "users")]
        role_items = rows(conn, "roles")
    return ok({"items": items, "roles": role_items, "total": len(items)})


@router.post("")
def create_user(body: UserIn, user: dict = Depends(require_perm("users.manage"))):
    username = body.username.strip()
    name = body.name.strip()
    if not username or not name:
        return fail(3001, "账号和姓名不能为空", 422)
    with db() as conn:
        if _username_exists(conn, username):
            return fail(2002, "账号已存在", 409)
        t = now()
        item = {
            "id": uid(),
            "username": username,
            "name": name,
            "department_id": body.department_id or "",
            "role_ids": body.role_ids or ["pm"],
            "status": body.status,
            "password": hash_password(body.password or "Workbench2026!"),
            "created_at": t,
            "updated_at": t,
            "updated_by": user.get("id"),
        }
        put(conn, "users", item)
    return ok(public_user(item))


@router.put("/{user_id}")
def update_user(user_id: str, body: UserPatch, user: dict = Depends(require_perm("users.manage"))):
    with db() as conn:
        item = row(conn, "users", user_id)
        if not item:
            return fail(2001, "账号不存在", 404)
        data = body.model_dump(exclude_none=True)
        if "username" in data:
            data["username"] = data["username"].strip()
            if not data["username"]:
                return fail(3001, "账号不能为空", 422)
            if _username_exists(conn, data["username"], user_id):
                return fail(2002, "账号已存在", 409)
        if "name" in data:
            data["name"] = data["name"].strip()
            if not data["name"]:
                return fail(3001, "姓名不能为空", 422)
        if "password" in data:
            if data["password"]:
                data["password"] = hash_password(data["password"])
            else:
                data.pop("password")
        item.update(data)
        item["updated_at"] = now()
        item["updated_by"] = user.get("id")
        put(conn, "users", item)
    return ok(public_user(item))


@router.delete("/{user_id}")
def delete_user(user_id: str, user: dict = Depends(require_perm("users.manage"))):
    if user_id == user.get("id"):
        return fail(3001, "不能删除当前登录账号", 422)
    with db() as conn:
        if not row(conn, "users", user_id):
            return fail(2001, "账号不存在", 404)
        delete(conn, "users", user_id)
    return ok({"id": user_id})
