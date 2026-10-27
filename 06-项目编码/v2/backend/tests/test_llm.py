"""LLM 增强层验收：开关回退、语义背书、AI 追问、调用审计。

红线断言：LLM 不碰判断层——真实性/相关性/优先级结论与状态流转不出现 LLM 路径。
"""
from __future__ import annotations
import os
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="wb_v2_llm_")
os.environ["WORKBENCH_DATA_DIR"] = _TMP
os.environ.setdefault("WORKBENCH_INIT_PASSWORD", "Workbench2026!")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

import pytest  # noqa: E402

PW = "Workbench2026!"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client, username="product"):
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"username": username, "password": PW})
    assert r.json()["code"] == 0, r.text


def make_project(client):
    login(client, "product")
    r = client.post("/api/projects", json={
        "name": f"LLM项目-{uuid.uuid4().hex[:6]}",
        "company_business": "公司为内部业务团队提供数字化提效工具。",
        "project_background": "用于 LLM 增强层测试。",
        "progress": "二期",
    })
    return r.json()["data"]["id"]


def make_req(client, pid, title, original, problem, scenario="每周例会后。", impact="每周约 1 小时。"):
    login(client, "employee")
    r = client.post("/api/requirements", json={
        "project_id": pid, "title": title, "original": original,
        "scenario": scenario, "problem": problem, "impact": impact,
    })
    assert r.json()["code"] == 0, r.text
    return r.json()["data"]["id"]


def test_llm_disabled_fallback(client, monkeypatch):
    """不配 key：ai_suggestions 为空、背书无语义项，行为与纯规则一致。"""
    monkeypatch.delenv("WORKBENCH_LM_API_KEY", raising=False)
    pid = make_project(client)
    rid = make_req(client, pid, f"回退-{uuid.uuid4().hex[:6]}", "希望导出报表。", "人工拼表耗时。")
    login(client, "product")
    r = client.post(f"/api/requirements/{rid}/deep-dive")
    assert r.json()["code"] == 0
    assert r.json()["data"]["ai_suggestions"] == []
    detail = client.get(f"/api/requirements/{rid}").json()["data"]
    assert all(e.get("source") != "ai" for e in detail.get("endorsements", []))


def test_llm_deep_dive_suggestions_with_stub(client, monkeypatch):
    """替身返回两条追问：响应带 source=ai 的 AI 建议，且不落库。"""
    monkeypatch.setenv("WORKBENCH_LM_API_KEY", "test-key")
    monkeypatch.setattr("app.llm.chat", lambda messages, purpose, conn=None, user=None: '["最近一个月发生了几次？","每次大约消耗多少人力？"]')
    pid = make_project(client)
    rid = make_req(client, pid, f"追问-{uuid.uuid4().hex[:6]}", "希望日报自动汇总。", "跨系统复制耗时。")
    login(client, "product")
    r = client.post(f"/api/requirements/{rid}/deep-dive")
    data = r.json()["data"]
    assert [s["text"] for s in data["ai_suggestions"]] == ["最近一个月发生了几次？", "每次大约消耗多少人力？"]
    assert all(s["source"] == "ai" for s in data["ai_suggestions"])
    # 不落库：重新拉详情，持久化的 deep_dive_suggestions 不含 AI 条目
    detail = client.get(f"/api/requirements/{rid}").json()["data"]
    assert all(s.get("source") != "ai" for s in detail.get("deep_dive_suggestions", []))
    # 红线：判断层字段未被 LLM 触碰
    assert detail["authenticity"] == "pending" and detail["priority"] == "unassessed"


def test_llm_semantic_endorsement_with_stub(client, monkeypatch):
    """词面零重合时，LLM 语义兜底把已入池需求标记为 AI 背书。"""
    monkeypatch.setenv("WORKBENCH_LM_API_KEY", "test-key")
    monkeypatch.setattr("app.llm.chat", lambda messages, purpose, conn=None, user=None: '[{"index": 1, "reason": "都指向手工汇总数据的效率损耗"}]')
    pid = make_project(client)
    # 已入池历史需求：与当前需求词面零重合（场景/影响也解耦，确保走语义通道）
    rid_old = make_req(client, pid, f"旧-{uuid.uuid4().hex[:6]}", "考勤统计太麻烦。", "手工核对打卡记录。",
                       scenario="月初结账时。", impact="财务月底加班。")
    login(client, "product")
    client.patch(f"/api/requirements/{rid_old}", json={"status": "pooled"})
    # 当前需求：语义同类但词面完全不同
    rid_new = make_req(client, pid, f"新-{uuid.uuid4().hex[:6]}", "希望薪资核算自动化。", "每月人工计算出错。",
                       scenario="发薪日前一周。", impact="人事重复劳动。")
    login(client, "product")
    detail = client.get(f"/api/requirements/{rid_new}").json()["data"]
    ai_hits = [e for e in detail.get("endorsements", []) if e.get("source") == "ai"]
    assert ai_hits and ai_hits[0]["id"] == rid_old
    assert ai_hits[0]["overlap_level"] == "semantic"
    assert "效率" in ai_hits[0]["ai_reason"] or ai_hits[0]["ai_reason"]


def test_llm_call_audited(client, monkeypatch):
    """真实 chat() 路径（替身 httpx）：成功与失败都落 llm.call 审计。"""
    import app.llm as llm
    from app.database import db, rows

    monkeypatch.setenv("WORKBENCH_LM_API_KEY", "test-key")

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    monkeypatch.setattr(llm.httpx, "post", lambda *a, **kw: FakeResp())
    with db() as conn:
        assert llm.chat([{"role": "user", "content": "hi"}], purpose="test.stub", conn=conn) == "ok"
        logs = [i for i in rows(conn, "audit_logs") if i.get("action") == "llm.call" and i["detail"].get("purpose") == "test.stub"]
        assert logs and logs[-1]["detail"]["success"] is True and logs[-1]["detail"]["prompt_tokens"] == 10

        def boom(*a, **kw):
            raise RuntimeError("network down")

        monkeypatch.setattr(llm.httpx, "post", boom)
        assert llm.chat([{"role": "user", "content": "hi"}], purpose="test.fail", conn=conn) is None
        logs = [i for i in rows(conn, "audit_logs") if i.get("action") == "llm.call" and i["detail"].get("purpose") == "test.fail"]
        assert logs and logs[-1]["detail"]["success"] is False
