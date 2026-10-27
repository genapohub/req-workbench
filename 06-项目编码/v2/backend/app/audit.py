from __future__ import annotations

from app.config import now, uid
from app.database import put


def record(conn, action: str, user: dict | None = None, username: str = "",
           target_type: str = "", target_id: str = "", detail: dict | None = None):
    """关键写操作落审计。user 为操作者（公开表单等无登录态场景传 username）。"""
    put(conn, "audit_logs", {
        "id": uid(),
        "user_id": (user or {}).get("id", ""),
        "username": (user or {}).get("username") or username,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "detail": detail or {},
        "created_at": now(),
    })


def changed_fields(before: dict, patch: dict) -> dict:
    """计算前后值差异，供审计 detail 使用。"""
    diff = {}
    for k, v in patch.items():
        old = before.get(k)
        if old != v:
            diff[k] = [old, v]
    return diff
