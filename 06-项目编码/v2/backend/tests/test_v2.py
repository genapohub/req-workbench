from __future__ import annotations
import os
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="wb_v2_test_")
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
    return r.json()["data"]["user"]


def uniq(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:6]}"


def create_complete_project(client, name="完整基座"):
    auth(client, "product")
    r = client.post("/api/projects", json={
        "name": uniq(name),
        "company_business": "公司为内部业务团队提供数字化提效工具。",
        "project_background": "当前项目用于验证需求挖掘与辨伪闭环。",
        "progress": "MVP 收窄开发中",
        "business_goals": "减少伪需求进入评审。",
        "business_process": "提交诉求 -> 挖掘场景 -> 补证据 -> 辨伪评审。",
    })
    assert r.json()["code"] == 0, r.text
    assert r.json()["data"]["base_complete"] is True
    return r.json()["data"]["id"]


def create_req(client, project_id: str, title="日报自动化"):
    auth(client, "employee")
    r = client.post("/api/requirements", json={
        "project_id": project_id,
        "title": uniq(title),
        "original": "希望日报能自动汇总三个系统的数据。",
        "scenario": "每个工作日上午。",
        "problem": "人工跨系统复制汇总，易错且耗时。",
        "impact": "运营每天 1 次，约 30 分钟。",
    })
    assert r.json()["code"] == 0, r.text
    return r.json()["data"]["id"]


def test_healthz(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json()["code"] == 0


def test_login_and_menus_are_narrow(client):
    auth(client, "admin")
    body = client.get("/api/auth/me").json()["data"]
    labels = {m["label"] for m in body["menus"]}
    assert labels == {"工作概览", "基座信息", "需求挖掘", "账号管理"}
    assert "versions.view" not in body["permissions"]
    assert "requirements.schedule" not in body["permissions"]


def test_project_base_can_be_incomplete_and_then_edited(client):
    auth(client, "product")
    r = client.post("/api/projects", json={"name": uniq("缺基座")})
    body = r.json()["data"]
    assert body["base_complete"] is False
    assert set(body["base_missing_fields"]) == {"company_business", "project_background", "progress"}

    r = client.put(f"/api/projects/{body['id']}", json={
        "name": body["name"],
        "company_business": "内部工具业务",
        "project_background": "用于 PM 判断需求真伪",
        "progress": "试点中",
    })
    assert r.json()["data"]["base_complete"] is True


def test_requirement_create_requires_base_information(client):
    auth(client, "product")
    p = client.post("/api/projects", json={"name": uniq("仍缺基座"), "company_business": "内部工具"}).json()["data"]
    auth(client, "employee")
    r = client.post("/api/requirements", json={"project_id": p["id"], "title": "x", "original": "x"})
    assert r.status_code == 422
    assert r.json()["code"] == 3001
    assert "公司业务" in r.json()["message"] or "项目背景" in r.json()["message"]


def test_requirement_analyze_without_evidence_stays_pending(client):
    pid = create_complete_project(client)
    rid = create_req(client, pid, "无证据")
    auth(client, "product")
    res = client.post(f"/api/requirements/{rid}/analyze").json()["data"]
    assert res["authenticity"] == "pending"
    assert res["priority"] == "unassessed"
    assert res["depth"] >= 3


def test_requirement_analyze_with_supporting_evidence_can_be_supported(client):
    pid = create_complete_project(client, "有证据")
    rid = create_req(client, pid, "证据需求")
    auth(client, "product")
    client.patch(f"/api/requirements/{rid}", json={"scope_score": 4, "intensity_score": 4, "value_score": 5, "cost_score": 2})
    client.post(f"/api/requirements/{rid}/evidence", json={"title": "工单统计", "content": "近 30 天出现 27 次同类反馈", "supports": "support"})
    res = client.post(f"/api/requirements/{rid}/analyze").json()["data"]
    assert res["authenticity"] == "supported"
    assert res["priority"] == "high"
    assert res["base_complete"] is True


def test_contradicting_evidence_marks_low_priority(client):
    pid = create_complete_project(client, "反证")
    rid = create_req(client, pid, "反证需求")
    auth(client, "product")
    client.post(f"/api/requirements/{rid}/evidence", json={"title": "日志", "content": "近 90 天无人使用相关入口", "supports": "contradict"})
    res = client.post(f"/api/requirements/{rid}/analyze").json()["data"]
    assert res["authenticity"] == "contradicted"
    assert res["priority"] == "low"


def test_staff_visibility_isolated(client):
    pid = create_complete_project(client, "隔离")
    rid = create_req(client, pid, "自己的需求")
    auth(client, "employee")
    items = client.get("/api/requirements").json()["data"]["items"]
    assert any(r["id"] == rid for r in items)


def test_removed_old_scope_endpoints_are_not_registered(client):
    auth(client, "admin")
    for path in ["/api/versions", "/api/integrations", "/api/departments", "/api/roles"]:
        r = client.get(path)
        assert r.status_code == 404, path

    r = client.get("/api/users")
    assert r.status_code == 200
    assert "items" in r.json()["data"]

    pid = create_complete_project(client, "旧接口")
    rid = create_req(client, pid, "旧接口需求")
    auth(client, "product")
    for path in [f"/api/requirements/{rid}/schedule", f"/api/requirements/{rid}/delivery", f"/api/requirements/{rid}/sync"]:
        r = client.post(path, json={})
        assert r.status_code == 404, path


def test_export_markdown_contains_base_info(client):
    pid = create_complete_project(client, "导出")
    rid = create_req(client, pid, "导出需求")
    auth(client, "product")
    r = client.get(f"/api/requirements/{rid}/export.md")
    assert r.status_code == 200
    text = r.text
    assert "公司业务" in text
    assert "项目背景" in text
    assert "项目进度" in text
    assert "不代表承诺开发" in text


def test_users_crud_and_public_project_form(client):
    auth(client, "product")
    username = uniq("pm")
    r = client.post("/api/users", json={
        "username": username,
        "name": "试点 PM",
        "department_id": "产品部",
        "role_ids": ["pm"],
        "status": "active",
        "password": "Workbench2026!",
    })
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    uid = r.json()["data"]["id"]
    r = client.put(f"/api/users/{uid}", json={"name": "试点 PM 更新", "status": "disabled"})
    assert r.json()["data"]["status"] == "disabled"

    pid = create_complete_project(client, "公开提需")
    client.cookies.clear()
    form = client.get(f"/api/public/projects/{pid}/form")
    assert form.status_code == 200
    assert form.json()["data"]["project"]["base_complete"] is True
    sub = client.post(f"/api/public/projects/{pid}/requirements", json={
        "title": "公开表单提交",
        "original": "扫码后提交一条需求",
        "scenario": "员工手机扫码时",
    })
    assert sub.status_code == 200 and sub.json()["code"] == 0, sub.text
