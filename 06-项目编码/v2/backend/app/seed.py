from __future__ import annotations

from app.config import ROLE_DEFAULTS, now, uid
from app.database import db, row, rows, put
from app.deps import hash_password


def default_project() -> dict:
    t = now()
    return {
        "id": "project-default",
        "name": "需求智能工作台试点",
        "company_business": "公司为内部业务团队提供数字化提效工具，核心链路是员工提出问题、产品还原需求、技术评估方案、评审确认投入。",
        "project_background": "当前处于 v2 MVP 重构阶段，目标是让 PM 更快判断员工诉求是否为真实需求，而不是做排期交付管理。",
        "stage": "一期试点",
        "business_goals": "帮助 PM 基于公司业务、项目背景和项目进度判断需求真伪与投入优先级。",
        "north_star_metric": "从提交到首次可评审的中位时长、已入池需求关键判断可追溯率。",
        "business_process": "内部员工提交诉求 -> PM 挖掘真实场景 -> 补充证据 -> 辨伪判断 -> 人工评审。",
        "target_users": "公司内部员工、产品经理、技术评估人、评审负责人。",
        "market_context": "内部提效类工作台，不强制做市场趋势验证。",
        "progress": "MVP 收窄开发中",
        "constraints": "一期只做需求挖掘和辨伪；AI 推断不得自动变成事实。",
        "created_at": t,
        "updated_at": t,
        "updated_by": "system",
    }


def default_requirements() -> list[dict]:
    t = now()
    return [
        {
            "id": uid(),
            "project_id": "project-default",
            "title": "运营日报重复整理",
            "original": "我每天要从三个系统手动拼运营日报，希望减少重复整理。",
            "scenario": "每个工作日上午提交运营日报前。",
            "problem": "运营需要跨系统汇总日报，当前依赖人工复制、核对和拼表。",
            "impact": "每天约 1 次，影响运营日报产出效率；具体耗时和人数待补证据。",
            "proposer_id": "employee",
            "authenticity": "pending",
            "business_relevance": "direct",
            "priority": "medium",
            "depth": 3,
            "scope_score": 3,
            "intensity_score": 3,
            "value_score": 4,
            "cost_score": 2,
            "priority_reason": "落在内部提效主链路，但缺少耗时和人数证据，暂定中优先级。",
            "status": "clarifying",
            "clarifications": [
                {"id": uid(), "question": "最近一次真实发生是在什么时候？", "answer": "待提出人补充", "asked_by": "system", "answered_by": "", "created_at": t},
                {"id": uid(), "question": "当前具体从哪三个系统取数？每次耗时多久？", "answer": "待提出人补充", "asked_by": "system", "answered_by": "", "created_at": t},
            ],
            "evidence": [],
            "solutions": [
                {"name": "维持现状", "benefit": "无开发成本", "cost": "继续消耗人工", "risk": "长期效率损耗被低估"},
                {"name": "流程调整", "benefit": "统一日报模板，先减少口径差异", "cost": "低", "risk": "仍需人工复制"},
                {"name": "半自动汇总", "benefit": "低成本验证自动报表价值", "cost": "中", "risk": "需要数据源权限"},
            ],
            "analysis_history": [],
            "deep_dive_suggestions": [],
            "created_at": t,
            "updated_at": t,
            "updated_by": "product",
        }
    ]


def bootstrap():
    with db() as conn:
        # 角色权限是菜单显示和接口权限的基础。
        # 旧版本本地数据库可能已经有 roles 表，不能只在空表时写入；
        # 每次启动都按代码里的 ROLE_DEFAULTS 做一次轻量 upsert，保证新增菜单/权限能生效。
        for role_id, permissions in ROLE_DEFAULTS.items():
            put(conn, "roles", {
                "id": role_id,
                "name": {"admin": "系统管理员", "pm": "需求负责人", "staff": "普通员工", "tech": "技术评估人"}[role_id],
                "description": {"admin": "内置管理账号", "pm": "维护基座、需求挖掘、辨伪评审", "staff": "提交需求、查看自己的需求", "tech": "查看需求、补充技术风险"}[role_id],
                "permissions": permissions,
            })
        if not rows(conn, "users"):
            pwd = hash_password("Workbench2026!")
            for item in [
                {"id": "admin", "username": "admin", "name": "管理员", "department_id": "dept-tech", "role_ids": ["admin"], "status": "active", "password": pwd},
                {"id": "product", "username": "product", "name": "陈思 · 需求负责人", "department_id": "dept-ops", "role_ids": ["pm"], "status": "active", "password": pwd},
                {"id": "employee", "username": "employee", "name": "林晓 · 提出人", "department_id": "dept-ops", "role_ids": ["staff"], "status": "active", "password": pwd},
                {"id": "engineer", "username": "engineer", "name": "周远 · 技术评估", "department_id": "dept-tech", "role_ids": ["tech"], "status": "active", "password": pwd},
            ]:
                put(conn, "users", item)
        if not rows(conn, "projects"):
            put(conn, "projects", default_project())
        if not rows(conn, "requirements"):
            default_id = rows(conn, "projects")[0]["id"]
            for req in default_requirements():
                req["project_id"] = default_id
                put(conn, "requirements", req)
