from __future__ import annotations

from fastapi import APIRouter, Depends

from app.database import db, rows
from app.deps import require_perm
from app.resp import ok

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(action: str | None = None, username: str | None = None,
                    limit: int = 100, user: dict = Depends(require_perm("audit.view"))):
    with db() as conn:
        items = rows(conn, "audit_logs")
    if action:
        items = [i for i in items if i.get("action") == action]
    if username:
        items = [i for i in items if i.get("username") == username]
    items.sort(key=lambda i: i.get("created_at", 0), reverse=True)
    limit = max(1, min(limit, 500))
    return ok({"items": items[:limit], "total": len(items)})
