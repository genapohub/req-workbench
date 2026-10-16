from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import now, uid
from app.database import db, row, put
from app.deps import current_user, role_permissions
from app.resp import ok, fail
from app.schemas import RequirementIn, RequirementPatch, ClarificationIn, EvidenceIn
from app.analysis import (
    enrich_requirement, visible_requirements, get_requirement_for_user,
    auto_analyze_requirement, build_deep_dive_suggestions,
    render_requirement_markdown, build_timeline, project_base_complete, project_base_message,
)

router = APIRouter(prefix="/requirements", tags=["requirements"])


def _default_solutions():
    return [
        {"name": "维持现状", "benefit": "无开发成本", "cost": "问题继续存在", "risk": "隐性人力损耗扩大"},
        {"name": "流程调整", "benefit": "低成本先验证", "cost": "需要业务配合", "risk": "无法解决系统性瓶颈"},
        {"name": "产品改造", "benefit": "沉淀为长期能力", "cost": "需要技术投入", "risk": "证据不足时容易做偏"},
    ]


def _enrich_list(conn, reqs):
    return [enrich_requirement(conn, r) for r in reqs]


def _ensure_base(project: dict | None):
    if not project_base_complete(project):
        return fail(3001, project_base_message(project), 422)
    return None


@router.get("")
def list_requirements(user: dict = Depends(current_user)):
    with db() as conn:
        reqs = visible_requirements(conn, user)
        items = _enrich_list(conn, reqs)
    return ok({"items": items, "total": len(items)})


@router.post("")
def create_requirement(body: RequirementIn, user: dict = Depends(current_user)):
    with db() as conn:
        proj = row(conn, "projects", body.project_id)
        if not proj:
            return fail(2001, "项目不存在", 404)
        blocked = _ensure_base(proj)
        if blocked:
            return blocked
        perms = role_permissions(conn, user)
        if "requirements.create" not in perms:
            return fail(1003, "无权限：需要 requirements.create", 403)
        if not body.title.strip() or not body.original.strip():
            return fail(3001, "标题和用户原话不能为空", 422)
        t = now()
        item = {
            "id": uid(),
            "project_id": body.project_id,
            "proposer_id": user["id"],
            "title": body.title.strip(),
            "original": body.original,
            "scenario": body.scenario or "待补充场景。",
            "problem": body.problem or "待从用户原话中还原真实问题。",
            "impact": body.impact or "待补充影响范围、发生频率、时间损失或风险后果。",
            "authenticity": "pending",
            "business_relevance": "unknown",
            "priority": "unassessed",
            "depth": 0,
            "scope_score": 0,
            "intensity_score": 0,
            "value_score": 0,
            "cost_score": 0,
            "priority_reason": "证据不足，暂不生成综合优先级。",
            "status": "draft",
            "clarifications": [],
            "evidence": [],
            "solutions": _default_solutions(),
            "analysis_history": [],
            "deep_dive_suggestions": [],
            "created_at": t,
            "updated_at": t,
            "updated_by": user["id"],
        }
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item)
    return ok(item)


@router.get("/{rid}")
def get_requirement(rid: str, user: dict = Depends(current_user)):
    with db() as conn:
        item = get_requirement_for_user(conn, rid, user)
        item = enrich_requirement(conn, item, with_endorsements=True)
        item["timeline"] = build_timeline(item)
    return ok(item)


def _judge_user(request: Request) -> dict:
    user = current_user(request)
    with db() as conn:
        perms = role_permissions(conn, user)
    if "requirements.review" not in perms and "requirements.analyze" not in perms:
        raise HTTPException(status_code=403, detail="无权限：需要评审或分析权限")
    return user


@router.patch("/{rid}")
def patch_requirement(rid: str, body: RequirementPatch, user: dict = Depends(_judge_user)):
    with db() as conn:
        item = row(conn, "requirements", rid)
        if not item:
            return fail(2001, "需求不存在", 404)
        if body.title is not None and not body.title.strip():
            return fail(3001, "标题不能为空", 422)
        if body.original is not None and not body.original.strip():
            return fail(3001, "用户原话不能为空", 422)
        for k, v in body.model_dump(exclude_none=True).items():
            item[k] = v
        item["updated_at"] = now()
        item["updated_by"] = user["id"]
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item)
    return ok(item)


@router.post("/{rid}/clarifications")
def add_clarification(rid: str, body: ClarificationIn, user: dict = Depends(current_user)):
    with db() as conn:
        item = row(conn, "requirements", rid)
        if not item:
            return fail(2001, "需求不存在", 404)
        perms = role_permissions(conn, user)
        editable = "requirements.review" in perms or "requirements.analyze" in perms or item.get("proposer_id") == user["id"]
        if not editable:
            return fail(1003, "无权限：需评审/分析权限或本人提交", 403)
        item.setdefault("clarifications", []).append({
            "id": uid(), "question": body.question, "answer": body.answer or "待补充",
            "asked_by": user["id"], "answered_by": user["id"] if body.answer else "", "created_at": now(),
        })
        item["updated_at"] = now()
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item)
    return ok(item)


@router.post("/{rid}/evidence")
def add_evidence(rid: str, body: EvidenceIn, user: dict = Depends(current_user)):
    with db() as conn:
        item = row(conn, "requirements", rid)
        if not item:
            return fail(2001, "需求不存在", 404)
        perms = role_permissions(conn, user)
        editable = "requirements.review" in perms or "requirements.analyze" in perms or item.get("proposer_id") == user["id"]
        if not editable:
            return fail(1003, "无权限：需评审/分析权限或本人提交", 403)
        item.setdefault("evidence", []).append({
            "id": uid(), "title": body.title, "content": body.content,
            "kind": body.kind or "未填", "source": body.source or "未填",
            "supports": body.supports, "created_at": now(), "created_by": user["id"],
        })
        item["updated_at"] = now()
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item)
    return ok(item)


@router.post("/{rid}/analyze")
def analyze_requirement(rid: str, user: dict = Depends(current_user)):
    with db() as conn:
        item = get_requirement_for_user(conn, rid, user)
        perms = role_permissions(conn, user)
        if "requirements.analyze" not in perms:
            return fail(1003, "无权限：需要 requirements.analyze", 403)
        project = row(conn, "projects", item.get("project_id"))
        blocked = _ensure_base(project)
        if blocked:
            return blocked
        result = auto_analyze_requirement(item, project, conn)
        for k in ("authenticity", "business_relevance", "depth", "priority", "priority_reason"):
            item[k] = result[k]
        item["deep_dive_suggestions"] = result["deep_dive_suggestions"]
        item.setdefault("analysis_history", []).append({"at": now(), "summary": result["summary"]})
        item["updated_at"] = now()
        item["updated_by"] = user["id"]
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item, with_endorsements=True)
        item["analysis"] = result
    return ok(item)


@router.post("/{rid}/deep-dive")
def deep_dive(rid: str, user: dict = Depends(current_user)):
    with db() as conn:
        item = get_requirement_for_user(conn, rid, user)
        perms = role_permissions(conn, user)
        if "requirements.analyze" not in perms and "requirements.review" not in perms:
            return fail(1003, "无权限：需要分析或评审权限", 403)
        project = row(conn, "projects", item.get("project_id"))
        item["deep_dive_suggestions"] = build_deep_dive_suggestions(item, project)
        item["updated_at"] = now()
        put(conn, "requirements", item)
        item = enrich_requirement(conn, item)
    return ok(item)


@router.get("/{rid}/export.md")
def export_markdown(rid: str, user: dict = Depends(current_user)):
    with db() as conn:
        item = get_requirement_for_user(conn, rid, user)
        project = row(conn, "projects", item.get("project_id"))
        md = render_requirement_markdown(enrich_requirement(conn, item), project)
    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")
