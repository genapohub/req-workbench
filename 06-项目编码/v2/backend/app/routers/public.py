from __future__ import annotations

from fastapi import APIRouter

from app.config import now, uid
from app.database import db, row, put
from app.resp import ok, fail
from app.schemas import PublicRequirementIn
from app.analysis import project_base_complete, project_base_message, enrich_project_base

router = APIRouter(prefix="/public", tags=["public"] )


def _default_solutions():
    return [
        {"name": "维持现状", "benefit": "不产生开发成本", "cost": "问题继续存在", "risk": "真实影响可能继续扩大"},
        {"name": "流程调整", "benefit": "先用低成本方式验证", "cost": "需要业务配合", "risk": "只适合流程类问题"},
        {"name": "产品改造", "benefit": "可沉淀为长期能力", "cost": "需要研发投入", "risk": "证据不足时容易做偏"},
    ]


@router.get("/projects/{project_id}/form")
def get_project_form(project_id: str):
    with db() as conn:
        project = row(conn, "projects", project_id)
    if not project:
        return fail(2001, "项目不存在", 404)
    enriched = enrich_project_base(project)
    return ok({
        "project": {
            "id": enriched["id"],
            "name": enriched["name"],
            "base_complete": enriched["base_complete"],
            "base_status_label": enriched["base_status_label"],
            "base_message": project_base_message(project),
            "company_business": enriched.get("company_business"),
            "project_background": enriched.get("project_background"),
            "progress": enriched.get("progress"),
        }
    })


@router.post("/projects/{project_id}/requirements")
def submit_project_requirement(project_id: str, body: PublicRequirementIn):
    with db() as conn:
        project = row(conn, "projects", project_id)
        if not project:
            return fail(2001, "项目不存在", 404)
        if not project_base_complete(project):
            return fail(3001, project_base_message(project), 422)
        if not body.title.strip() or not body.original.strip():
            return fail(3001, "标题和用户原话不能为空", 422)
        t = now()
        item = {
            "id": uid(),
            "project_id": project_id,
            "proposer_id": "public",
            "proposer_name_text": body.submitter_name or "公开表单提交人",
            "submitter_department": body.submitter_department or "",
            "source": "public_form",
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
            "priority_reason": "公开表单只记录原话，需 PM 补证据后再判断优先级。",
            "status": "draft",
            "clarifications": [],
            "evidence": [],
            "solutions": _default_solutions(),
            "analysis_history": [],
            "deep_dive_suggestions": [],
            "created_at": t,
            "updated_at": t,
            "updated_by": "public_form",
        }
        put(conn, "requirements", item)
    return ok({"id": item["id"], "status": item["status"], "message": "需求已提交，PM 会在后台继续挖掘和评审。"})
