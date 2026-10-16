"""收窄版验收：只验证基座信息、需求挖掘、需求辨伪。"""
from __future__ import annotations
import os
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="wb_v2_acc_")
os.environ["WORKBENCH_DATA_DIR"] = _TMP

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

import pytest  # noqa: E402

PW = "Workbench2026!"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth(client, username: str):
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"username": username, "password": PW})
    assert r.status_code == 200 and r.json()["code"] == 0, r.text


def uniq(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:6]}"


def project(client, **overrides):
    auth(client, "product")
    data = {
        "name": uniq("验收项目"),
        "company_business": "企业内部数字化提效业务。",
        "project_background": "用于验证员工原话到真实需求的挖掘闭环。",
        "progress": "部门试点中",
        "business_goals": "减少伪需求和返工。",
        "business_process": "提交 -> 挖掘 -> 证据 -> 辨伪 -> 评审。",
    }
    data.update(overrides)
    return client.post("/api/projects", json=data).json()["data"]


def requirement(client, pid, original="想加一个导出按钮"):
    auth(client, "employee")
    r = client.post("/api/requirements", json={
        "project_id": pid,
        "title": uniq("需求"),
        "original": original,
        "scenario": "每周做经营复盘前。",
        "problem": "当前要手动汇总多处数据后再给负责人汇报。",
        "impact": "每周一次，单次约 1 小时，影响运营和产品。",
    })
    assert r.json()["code"] == 0, r.text
    return r.json()["data"]


def test_ac_menu_contains_workspace_items(client):
    auth(client, "product")
    labels = [m["label"] for m in client.get("/api/auth/me").json()["data"]["menus"]]
    assert labels == ["工作概览", "需求挖掘", "基座信息", "账号管理"]


def test_ac_dashboard_exposes_base_completeness(client):
    project(client)
    body = client.get("/api/dashboard").json()["data"]
    assert "base_complete_projects" in body
    assert "total_versions" not in body
    assert "by_delivery" not in body


def test_ac_base_incomplete_blocks_submit(client):
    p = project(client, project_background="", progress="")
    auth(client, "employee")
    r = client.post("/api/requirements", json={"project_id": p["id"], "title": "x", "original": "x"})
    assert r.status_code == 422
    assert r.json()["code"] == 3001


def test_ac_export_button_scope_is_requirement_card_only(client):
    p = project(client)
    req = requirement(client, p["id"])
    auth(client, "product")
    text = client.get(f"/api/requirements/{req['id']}/export.md").text
    assert "需求卡_PRD草案" in text
    assert "TAPD" not in text
    assert "归入版本" not in text


def test_ac_low_frequency_high_impact_not_auto_rejected(client):
    p = project(client)
    req = requirement(client, p["id"], "一年一次的合规报表如果错了会被处罚")
    auth(client, "product")
    client.post(f"/api/requirements/{req['id']}/evidence", json={"title": "合规说明", "content": "错误会触发处罚", "supports": "support"})
    res = client.post(f"/api/requirements/{req['id']}/analyze").json()["data"]
    assert res["authenticity"] == "supported"
    assert res["status"] != "rejected"


def test_ac_ai_does_not_invent_response_time(client):
    p = project(client)
    req = requirement(client, p["id"], "系统太慢了")
    auth(client, "product")
    res = client.post(f"/api/requirements/{req['id']}/analyze").json()["data"]
    combined = str(res)
    assert "响应时间" not in combined or "待" in combined
    assert res["authenticity"] == "pending"
