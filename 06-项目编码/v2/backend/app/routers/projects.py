from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import now, uid
from app.database import db, row, rows, put
from app.deps import require_perm
from app.resp import ok, fail
from app.schemas import ProjectIn

router = APIRouter(prefix="/projects", tags=["projects"])

BASE_FIELDS = ["company_business", "project_background", "progress"]


def base_status(project: dict) -> dict:
    missing = [f for f in BASE_FIELDS if not str(project.get(f) or "").strip()]
    return {
        "base_complete": not missing,
        "base_missing_fields": missing,
        "base_status_label": "完整" if not missing else "缺" + "、".join({
            "company_business": "公司业务",
            "project_background": "项目背景",
            "progress": "项目进度",
        }[f] for f in missing),
    }


def enrich_project(project: dict, count: int = 0) -> dict:
    return {**project, **base_status(project), "requirement_count": count}


@router.get("")
def list_projects(user: dict = Depends(require_perm("projects.view"))):
    with db() as conn:
        projects = rows(conn, "projects")
        reqs = rows(conn, "requirements")
    counts = {}
    for r in reqs:
        pid = r.get("project_id")
        counts[pid] = counts.get(pid, 0) + 1
    items = [enrich_project(p, counts.get(p.get("id"), 0)) for p in projects]
    return ok({"items": items, "total": len(items)})


@router.post("")
def create_project(body: ProjectIn, user: dict = Depends(require_perm("projects.manage"))):
    if not body.name or not body.name.strip():
        return fail(3001, "项目名称不能为空", 422)
    t = now()
    item = {"id": uid(), "created_at": t, "updated_at": t, "updated_by": user.get("id"), **body.model_dump(exclude_none=True)}
    item["name"] = body.name.strip()
    with db() as conn:
        put(conn, "projects", item)
    return ok(enrich_project(item))


@router.put("/{pid}")
def update_project(pid: str, body: ProjectIn, user: dict = Depends(require_perm("projects.manage"))):
    with db() as conn:
        item = row(conn, "projects", pid)
        if not item:
            return fail(2001, "项目不存在", 404)
        for k, v in body.model_dump(exclude_none=True).items():
            item[k] = v
        item["name"] = item.get("name", "").strip()
        item["updated_at"] = now()
        item["updated_by"] = user.get("id")
        put(conn, "projects", item)
    return ok(enrich_project(item))
