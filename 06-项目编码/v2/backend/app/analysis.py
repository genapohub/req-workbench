from __future__ import annotations
import re

from app.config import STATUS_LABELS
from app.database import row, rows
from app.deps import role_permissions

BASE_FIELDS = ["company_business", "project_background", "progress"]
BASE_LABELS = {"company_business": "公司业务", "project_background": "项目背景", "progress": "项目进度"}

# 「已实现需求」的判定口径：一期没有「已实现/已上线」状态，
# 以「已入池」= 已确认投入作为可背书的历史需求来源（贴合一期只做挖掘与辨伪的范围）。
ENDORSABLE_STATUSES = ["pooled"]


def _tokens(text) -> set[str]:
    """中英混合轻量分词，用于业务词重合度比对。

    中文没有空格，按标点切会把整句变成一个超长 token，导致交集永远为空；
    因此中文按「字符 2-gram」切（如「导出报表」→ 导出 / 出报 / 报表），
    英文数字按词切。不引入 jieba 等第三方依赖，保持部署轻量。
    """
    if not text:
        return set()
    s = str(text)
    out: set[str] = set()
    for w in re.findall(r"[A-Za-z0-9]{2,}", s):
        out.add(w.lower())
    for seg in re.findall(r"[\u4e00-\u9fff]+", s):
        if len(seg) == 1:
            out.add(seg)
        for i in range(len(seg) - 1):
            out.add(seg[i : i + 2])
    return out


def _req_text(item: dict) -> str:
    return " ".join(
        str(item.get(k) or "")
        for k in ("title", "problem", "scenario", "impact")
    )


def endorsable_requirements(conn, item: dict) -> list[dict]:
    """同项目下、已确认（已入池）且非自身的历史需求：基座背书的候选池。"""
    project_id = item.get("project_id")
    if not project_id:
        return []
    return [
        r for r in rows(conn, "requirements")
        if r.get("project_id") == project_id
        and r.get("id") != item.get("id")
        and r.get("status") in ENDORSABLE_STATUSES
    ]


def base_endorsements(conn, item: dict, limit: int = 3) -> list[dict]:
    """基座背书：把同项目已确认的历史需求按业务词重合度取最相关若干条。

    定位：只作为「历史上确认过同类需求」的证据线索，供 PM 参考，
    绝不替代人工判断，也不自动改写任何基座字段（基座字段仍由人维护）。
    词面重合不足时，若启用了 LLM（WORKBENCH_LM_API_KEY），追加一次语义匹配兜底，
    命中条目标记 source=ai 展示为「AI 建议」（仅在响应时计算，不落库）。
    """
    current = _tokens(_req_text(item))
    if not current:
        return []
    out = []
    for r in endorsable_requirements(conn, item):
        shared = current & _tokens(_req_text(r))
        if not shared:
            continue
        out.append({
            "id": r.get("id"),
            "title": r.get("title", ""),
            "status": r.get("status", ""),
            "status_label": STATUS_LABELS.get(r.get("status"), r.get("status", "")),
            "priority": r.get("priority", ""),
            "problem": r.get("problem", "") or r.get("original", ""),
            "shared_terms": sorted(shared)[:6],
            "overlap": len(shared),
            "overlap_level": "high" if len(shared) >= 3 else "medium",
            "source": "lexical",
        })
    out.sort(key=lambda x: -x["overlap"])
    results = out[:limit]
    if len(results) < limit:
        results += _semantic_endorsements(conn, item, exclude={r["id"] for r in results},
                                          limit=limit - len(results))
    return results


def _semantic_endorsements(conn, item: dict, exclude: set, limit: int) -> list[dict]:
    """LLM 语义兜底：词面重合为空/不足时，让模型判断候选与当前需求是否语义同类。
    只影响展示层的背书线索，不参与真实性/相关性/优先级结论（判断层红线）。"""
    from app.llm import chat, enabled, extract_json_array

    if limit <= 0 or not enabled():
        return []
    candidates = [r for r in endorsable_requirements(conn, item) if r.get("id") not in exclude][:10]
    if not candidates:
        return []
    numbered = "\n".join(
        f"{i + 1}. {c.get('title', '')}｜{c.get('problem', '') or c.get('original', '')}"
        for i, c in enumerate(candidates)
    )
    content = chat([
        {"role": "system", "content": "你是需求分析助手。判断候选历史需求与当前需求是否在语义上指向同一类业务问题（词面可以完全不同）。只输出 JSON 数组，元素为 {\"index\": 序号, \"reason\": \"一句话理由\"}；没有语义同类的就输出 []。"},
        {"role": "user", "content": f"当前需求：{_req_text(item)}\n\n候选历史需求：\n{numbered}"},
    ], purpose="base_endorsements.semantic", conn=conn)
    out = []
    for hit in extract_json_array(content):
        try:
            idx = int(hit.get("index")) - 1
        except Exception:
            continue
        if not (0 <= idx < len(candidates)):
            continue
        c = candidates[idx]
        out.append({
            "id": c.get("id"),
            "title": c.get("title", ""),
            "status": c.get("status", ""),
            "status_label": STATUS_LABELS.get(c.get("status"), c.get("status", "")),
            "priority": c.get("priority", ""),
            "problem": c.get("problem", "") or c.get("original", ""),
            "shared_terms": [],
            "overlap": 0,
            "overlap_level": "semantic",
            "source": "ai",
            "ai_reason": str(hit.get("reason", ""))[:100],
        })
        if len(out) >= limit:
            break
    return out


def llm_deep_dive_suggestions(conn, item: dict, project: dict | None, limit: int = 3) -> list[dict]:
    """LLM 追问建议（增强层）：针对原话/场景/问题生成具体追问，标注 source=ai。
    仅在响应时追加，不落库；未启用或失败返回 []，调用方回退纯规则建议。"""
    from app.llm import chat, enabled, extract_json_array

    if not enabled():
        return []
    content = chat([
        {"role": "system", "content": "你是需求挖掘助手。根据员工原话与已有场景/问题/影响，提出最缺的追问（帮 PM 验证真实性、量化影响、确认业务相关性）。只输出 JSON 字符串数组，最多 3 条，每条一句具体问题。"},
        {"role": "user", "content": (
            f"标题：{item.get('title', '')}\n原话：{item.get('original', '')}\n"
            f"场景：{item.get('scenario', '')}\n问题：{item.get('problem', '')}\n"
            f"影响：{item.get('impact', '')}\n"
            f"项目基座：{(project or {}).get('company_business', '')}｜{(project or {}).get('progress', '')}"
        )},
    ], purpose="deep_dive.suggestions", conn=conn)
    out = []
    for q in extract_json_array(content):
        text = str(q).strip()
        if text:
            out.append({"type": "AI 追问", "text": text, "source": "ai"})
        if len(out) >= limit:
            break
    return out


def useful_text(value) -> bool:
    return bool(value and isinstance(value, str) and "待补充" not in value and "待从" not in value)


def project_base_missing(project: dict | None) -> list[str]:
    if not project:
        return BASE_FIELDS[:]
    return [f for f in BASE_FIELDS if not str(project.get(f) or "").strip()]


def project_base_complete(project: dict | None) -> bool:
    return not project_base_missing(project)


def project_base_message(project: dict | None) -> str:
    missing = project_base_missing(project)
    if not missing:
        return "基座信息完整"
    labels = "、".join(BASE_LABELS[f] for f in missing)
    return f"请先补充{labels}，再使用需求挖掘与辨伪。"


def enrich_project_base(project: dict | None) -> dict | None:
    if not project:
        return None
    missing = project_base_missing(project)
    return {
        **project,
        "base_complete": not missing,
        "base_missing_fields": missing,
        "base_status_label": "完整" if not missing else "缺" + "、".join(BASE_LABELS[f] for f in missing),
    }


def enrich_requirement(conn, item: dict, with_endorsements: bool = False) -> dict:
    """with_endorsements：仅详情页/分析接口开启（列表接口关闭，避免 O(n²) 比对）"""
    project = row(conn, "projects", item.get("project_id", "")) if item.get("project_id") else None
    proposer = row(conn, "users", item.get("proposer_id", "")) if item.get("proposer_id") else None
    enriched = dict(item)
    enriched.pop("version_id", None)
    enriched.pop("delivery_status", None)
    enriched.pop("schedule_history", None)
    enriched.pop("sync_history", None)
    enriched["project"] = enrich_project_base(project)
    enriched["base_complete"] = project_base_complete(project)
    enriched["base_message"] = project_base_message(project)
    enriched["proposer_name"] = proposer.get("name") if proposer else item.get("proposer_name_text") or item.get("proposer_id", "")
    enriched["method_cards"] = build_method_cards(enriched, project)
    if with_endorsements:
        enriched["endorsements"] = base_endorsements(conn, item)
    return enriched



def build_method_cards(item: dict, project: dict | None) -> list[dict]:
    evidence = item.get("evidence", []) or []
    return [
        {
            "name": "JTBD 场景",
            "status": "ok" if useful_text(item.get("scenario")) else "missing",
            "text": "已描述谁在什么情况下要完成什么任务" if useful_text(item.get("scenario")) else "缺最近一次真实发生场景",
        },
        {
            "name": "5 Whys 追问",
            "status": "ok" if useful_text(item.get("problem")) and len(item.get("clarifications", [])) >= 1 else "missing",
            "text": "已有问题还原和追问记录" if len(item.get("clarifications", [])) >= 1 else "至少补一轮为什么，避免停在用户给的方案",
        },
        {
            "name": "证据链",
            "status": "ok" if evidence else "missing",
            "text": f"已有 {len(evidence)} 条证据或反证" if evidence else "缺截图、数据、工单或访谈摘录",
        },
        {
            "name": "RICE 四维",
            "status": "ok" if any(int(item.get(k) or 0) for k in ["scope_score", "intensity_score", "value_score", "cost_score"]) else "missing",
            "text": "已填写影响范围、问题强度、业务价值或实现成本" if any(int(item.get(k) or 0) for k in ["scope_score", "intensity_score", "value_score", "cost_score"]) else "缺四维评分，暂不生成综合优先级",
        },
    ]

def visible_requirements(conn, user: dict) -> list[dict]:
    perms = role_permissions(conn, user)
    reqs = rows(conn, "requirements")
    if "requirements.review" in perms or "requirements.analyze" in perms:
        return reqs
    return [r for r in reqs if r.get("proposer_id") == user["id"]]


def can_access_requirement(conn, user: dict, item: dict) -> bool:
    perms = role_permissions(conn, user)
    return "requirements.review" in perms or "requirements.analyze" in perms or item.get("proposer_id") == user["id"]


def get_requirement_for_user(conn, rid: str, user: dict) -> dict:
    item = row(conn, "requirements", rid)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "需求不存在")
    if not can_access_requirement(conn, user, item):
        from fastapi import HTTPException
        raise HTTPException(403, "无权查看该需求")
    return item


def auto_analyze_requirement(item: dict, project: dict | None, conn=None) -> dict:
    evidence = item.get("evidence", [])
    support_count = sum(e.get("supports") == "support" for e in evidence)
    contradict_count = sum(e.get("supports") == "contradict" for e in evidence)
    authenticity = item.get("authenticity", "pending")
    if contradict_count and not support_count:
        authenticity = "contradicted"
    elif support_count and useful_text(item.get("scenario")) and useful_text(item.get("problem")):
        authenticity = "supported"
    else:
        authenticity = "pending"

    business_relevance = item.get("business_relevance", "unknown")
    endorsed_by = ""
    if business_relevance == "unknown" and project and useful_text(item.get("problem")):
        haystack = "".join([item.get("problem", ""), item.get("scenario", ""), item.get("impact", "")])
        business_text = "".join([
            project.get("company_business", ""), project.get("project_background", ""), project.get("business_goals", ""),
            project.get("business_process", ""), project.get("progress", ""), project.get("north_star_metric", ""),
        ])
        if _tokens(business_text) & _tokens(haystack):
            business_relevance = "direct"
        else:
            # 基座文本未命中时，用同项目「已确认」需求的历史文本兜底：
            # 历史上确认过同类需求，即构成本次需求的业务相关性背书（基座持续积累）。
            best = None
            if conn is not None:
                for r in endorsable_requirements(conn, item):
                    shared = _tokens(_req_text(r)) & _tokens(haystack)
                    if shared and (best is None or len(shared) > len(best[1])):
                        best = (r, shared)
            if best:
                business_relevance = "direct"
                endorsed_by = best[0].get("id", "")
            else:
                business_relevance = "indirect"

    depth_checks = [
        useful_text(item.get("scenario")),
        useful_text(item.get("problem")),
        useful_text(item.get("impact")),
        bool(evidence),
        len(item.get("solutions", [])) >= 2,
    ]
    depth = sum(depth_checks)
    scores = [int(item.get(k) or 0) for k in ["scope_score", "intensity_score", "value_score", "cost_score"]]
    has_scores = any(scores)
    priority = item.get("priority", "unassessed")
    priority_reason = item.get("priority_reason", "证据不足，暂不生成综合优先级。")
    if authenticity == "contradicted":
        priority = "low"
        priority_reason = "存在反证，当前不建议投入开发资源。"
    elif authenticity == "supported" and business_relevance in ["direct", "indirect"] and has_scores:
        total = scores[0] + scores[1] + scores[2] - scores[3]
        priority = "high" if total >= 9 else "medium" if total >= 5 else "low"
        priority_reason = f"按影响范围、问题强度、业务价值、实现成本计算净分 {total}，建议优先级为 {priority}。"
    elif authenticity == "pending":
        priority = "unassessed"
        priority_reason = "证据或场景不足，先补材料，不自动判定优先级。"

    summary = f"方法论检查：真实性={authenticity}，业务相关性={business_relevance}，挖掘深度={depth}/5，优先级={priority}。AI 仅作辅助建议，最终由人确认。"
    return {
        "authenticity": authenticity,
        "business_relevance": business_relevance,
        "business_relevance_endorsed_by": endorsed_by,
        "depth": depth,
        "priority": priority,
        "priority_reason": priority_reason,
        "summary": summary,
        "deep_dive_suggestions": build_deep_dive_suggestions(
            {**item, "authenticity": authenticity, "business_relevance": business_relevance, "priority": priority, "depth": depth},
            project,
        ),
    }


def build_deep_dive_suggestions(item: dict, project: dict | None) -> list[dict]:
    suggestions = []
    missing = project_base_missing(project)
    if missing:
        suggestions.append({"type": "基座", "text": project_base_message(project)})
    if not useful_text(item.get("scenario")):
        suggestions.append({"type": "追问", "text": "请补充最近一次真实发生场景：谁、何时、在哪个业务环节、要完成什么任务。"})
    if not useful_text(item.get("impact")):
        suggestions.append({"type": "证据", "text": "请补充发生频率、影响人数、单次耗时、错误率或客户投诉等至少一项证据。"})
    if not item.get("evidence"):
        suggestions.append({"type": "验证", "text": "当前没有证据记录，不能把用户原话直接判为真需求；建议补工单、截图、数据或访谈摘录。"})
    if item.get("business_relevance") in (None, "unknown"):
        goals = (project or {}).get("business_goals") or (project or {}).get("company_business") or "公司业务和项目目标"
        suggestions.append({"type": "业务对齐", "text": f"把需求影响明确挂到“{goals}”，否则保持业务相关性为待明确。"})
    if item.get("priority") == "unassessed":
        suggestions.append({"type": "优先级", "text": "补齐影响范围、问题强度、业务价值、实现成本四项评分，再由 PM 确认最终优先级。"})
    if not suggestions:
        suggestions.append({"type": "结论", "text": "关键上下文已较完整，可以进入评审；仍需评审负责人确认入池、暂缓或不采纳。"})
    return suggestions


def build_timeline(item: dict) -> list[dict]:
    events: list[dict] = []
    if item.get("created_at"):
        events.append({"at": item["created_at"], "type": "提交", "text": f"{item.get('proposer_name') or item.get('proposer_id','')} 提交了需求"})
    for c in item.get("clarifications", []):
        events.append({"at": c.get("created_at") or item.get("created_at"), "type": "追问", "text": c.get("question", "")})
    for e in item.get("evidence", []):
        events.append({"at": e.get("created_at") or item.get("created_at"), "type": "证据", "text": e.get("title", "")})
    for h in item.get("analysis_history", []):
        events.append({"at": h.get("at") or item.get("created_at"), "type": "分析", "text": h.get("summary", "")})
    if item.get("status"):
        events.append({"at": item.get("updated_at") or item.get("created_at"), "type": "状态", "text": f"当前状态：{STATUS_LABELS.get(item['status'], item['status'])}"})
    seen = set()
    ordered = []
    for e in sorted(events, key=lambda x: x.get("at") or 0):
        key = (e.get("at"), e.get("type"), e.get("text"))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(e)
    return ordered


def render_requirement_markdown(item: dict, project: dict | None) -> str:
    project = project or {}
    evidence_lines = "\n".join(
        f"- {e.get('title','未命名证据')}：{e.get('content','')}（来源：{e.get('source','未填')}，类型：{e.get('kind','未填')}，结论：{e.get('supports','未填')}）"
        for e in item.get("evidence", [])
    ) or "- 暂无证据，不能把 AI 推断或用户原话直接当事实。"
    clarification_lines = "\n".join(
        f"- 问：{c.get('question','')}\n  答：{c.get('answer') or '待补充'}"
        for c in item.get("clarifications", [])
    ) or "- 暂无追问记录。"
    solution_lines = "\n".join(
        f"- {s.get('name','候选方案')}：收益 {s.get('benefit','待补充')}；成本 {s.get('cost','待补充')}；风险 {s.get('risk','待补充')}。"
        for s in item.get("solutions", [])
    ) or "- 暂无候选方案。"
    suggestion_lines = "\n".join(
        f"- {s.get('type','建议')}：{s.get('text','')}"
        for s in build_deep_dive_suggestions(item, project)
    )
    return f"""# {item.get('title','未命名需求')}_需求卡_PRD草案

## 1. 基本信息

| 字段 | 内容 |
|---|---|
| 所属项目 | {project.get('name','未归属')} |
| 提出人 | {item.get('proposer_name') or item.get('proposer_id','')} |
| 当前状态 | {STATUS_LABELS.get(item.get('status'), item.get('status','待判断'))} |

## 2. 基座信息

- 公司业务：{project.get('company_business','待补充')}
- 项目背景：{project.get('project_background','待补充')}
- 项目进度：{project.get('progress','待补充')}
- 业务目标：{project.get('business_goals','待补充')}
- 关键流程：{project.get('business_process','待补充')}
- 限制条件：{project.get('constraints','待补充')}

## 3. 用户原话与真实问题

- 用户原话：{item.get('original','')}
- 发生场景：{item.get('scenario','待补充')}
- 还原后的问题：{item.get('problem','待补充')}
- 影响说明：{item.get('impact','待补充')}

## 4. 真伪判断与优先级

| 判断项 | 结论 |
|---|---|
| 问题真实性 | {item.get('authenticity','pending')} |
| 业务相关性 | {item.get('business_relevance','unknown')} |
| 优先级 | {item.get('priority','unassessed')} |
| 挖掘深度 | {item.get('depth',0)}/5 |

| 维度 | 分值 |
|---|---|
| 影响范围 | {item.get('scope_score',0)}/5 |
| 问题强度 | {item.get('intensity_score',0)}/5 |
| 业务价值 | {item.get('value_score',0)}/5 |
| 实现成本 | {item.get('cost_score',0)}/5 |

优先级理由：{item.get('priority_reason','待补充')}

## 5. 追问记录

{clarification_lines}

## 6. 证据与疑点

{evidence_lines}

## 7. 候选方案比较

{solution_lines}

## 8. 深挖建议

{suggestion_lines}

## 9. 评审记录

- 评审结论：{STATUS_LABELS.get(item.get('status'), item.get('status','待判断'))}
- 评审理由：{item.get('review_reason') or '待补充'}

> 说明：本导出对应当前需求版本。已入池表示需求评审通过，不代表承诺开发。
"""
