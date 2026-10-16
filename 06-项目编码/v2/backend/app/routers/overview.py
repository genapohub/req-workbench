from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import STATUS_LABELS
from app.database import db, rows
from app.deps import require_perm
from app.resp import ok
from app.analysis import visible_requirements, project_base_complete

router = APIRouter(prefix="/dashboard", tags=["overview"])


def _count_by(items, key):
    out: dict[str, int] = {}
    for it in items:
        k = it.get(key)
        if k:
            out[k] = out.get(k, 0) + 1
    return out


@router.get("")
def dashboard(user: dict = Depends(require_perm("overview.view"))):
    with db() as conn:
        reqs = visible_requirements(conn, user)
        projects = rows(conn, "projects")
    base_complete = sum(1 for p in projects if project_base_complete(p))
    return ok({
        "total_requirements": len(reqs),
        "by_status": {STATUS_LABELS.get(k, k): c for k, c in _count_by(reqs, "status").items()},
        "by_authenticity": _count_by(reqs, "authenticity"),
        "by_priority": _count_by(reqs, "priority"),
        "total_projects": len(projects),
        "base_complete_projects": base_complete,
        "base_incomplete_projects": max(0, len(projects) - base_complete),
        "recent_requirements": reqs[-6:][::-1],
    })
