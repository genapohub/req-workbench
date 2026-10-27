"""审计日志验收：关键写操作落审计、查询接口权限与筛选。

与既有测试同进程运行，只新增数据不改动种子账号。
"""
from __future__ import annotations
import os
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="wb_v2_audit_")
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


def login(client, username, password=PW):
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.json()["code"] == 0, r.text


def audit_items(client, action=None):
    r = client.get("/api/audit-logs", params={"action": action} if action else {})
    assert r.json()["code"] == 0, r.text
    return r.json()["data"]["items"]


def test_login_and_failure_are_audited(client):
    login(client, "admin")
    items = audit_items(client, "auth.login")
    assert any(i["username"] == "admin" for i in items)
    client.cookies.clear()
    client.post("/api/auth/login", json={"username": "admin", "password": "wrong-pass-1"})
    login(client, "admin")
    failed = audit_items(client, "auth.login_failed")
    assert any(i["username"] == "admin" for i in failed)


def test_user_crud_audited_with_diff(client):
    login(client, "admin")
    name = f"审计测试-{uuid.uuid4().hex[:6]}"
    r = client.post("/api/users", json={"username": name, "name": name, "password": "Init2026pass"})
    uid_new = r.json()["data"]["id"]
    client.put(f"/api/users/{uid_new}", json={"name": name + "-改"})
    client.delete(f"/api/users/{uid_new}")
    creates = [i for i in audit_items(client, "users.create") if i["target_id"] == uid_new]
    updates = [i for i in audit_items(client, "users.update") if i["target_id"] == uid_new]
    deletes = [i for i in audit_items(client, "users.delete") if i["target_id"] == uid_new]
    assert creates and updates and deletes
    assert creates[0]["detail"]["username"] == name
    assert updates[0]["detail"]["changed"]["name"] == [name, name + "-改"]


def test_project_and_requirement_audited(client):
    login(client, "product")
    r = client.post("/api/projects", json={
        "name": f"审计项目-{uuid.uuid4().hex[:6]}",
        "company_business": "公司为内部业务团队提供数字化提效工具。",
        "project_background": "用于审计测试。",
        "progress": "MVP 阶段",
    })
    pid = r.json()["data"]["id"]
    r = client.put(f"/api/projects/{pid}", json={"name": "审计项目", "progress": "二期"})
    assert r.json()["code"] == 0, r.text
    r = client.post("/api/requirements", json={
        "project_id": pid, "title": f"审计需求-{uuid.uuid4().hex[:6]}",
        "original": "希望审计日志覆盖关键操作。",
        "scenario": "每次操作。", "problem": "操作不留痕。", "impact": "无法追责。",
    })
    rid = r.json()["data"]["id"]
    client.patch(f"/api/requirements/{rid}", json={"status": "review"})
    client.get(f"/api/requirements/{rid}/export.md")
    login(client, "admin")  # 查询审计需要 audit.view（仅 admin）
    assert any(i["target_id"] == pid for i in audit_items(client, "projects.create"))
    upd = [i for i in audit_items(client, "projects.update") if i["target_id"] == pid]
    assert upd and upd[0]["detail"]["changed"]["progress"] == ["MVP 阶段", "二期"]
    assert any(i["target_id"] == rid for i in audit_items(client, "requirements.create"))
    rev = [i for i in audit_items(client, "requirements.review") if i["target_id"] == rid]
    assert rev and rev[0]["detail"]["changed"]["status"] == ["draft", "review"]
    assert any(i["target_id"] == rid for i in audit_items(client, "requirements.export"))


def test_public_submit_audited(client):
    login(client, "product")
    r = client.get("/api/projects")
    pid = next(p["id"] for p in r.json()["data"]["items"] if p["base_complete"])
    client.cookies.clear()
    r = client.post(f"/api/public/projects/{pid}/requirements",
                    json={"title": f"公开审计-{uuid.uuid4().hex[:6]}", "original": "公开提交也要留痕。",
                          "submitter_name": "审计员工"})
    rid = r.json()["data"]["id"]
    login(client, "admin")
    pubs = [i for i in audit_items(client, "public.submit") if i["target_id"] == rid]
    assert pubs and pubs[0]["username"] == "审计员工"


def test_audit_view_permission(client):
    login(client, "employee")
    r = client.get("/api/audit-logs")
    assert r.status_code == 403
    login(client, "product")
    r = client.get("/api/audit-logs")
    assert r.status_code == 403  # audit.view 仅 admin
    login(client, "admin")
    r = client.get("/api/audit-logs")
    assert r.json()["code"] == 0 and r.json()["data"]["total"] > 0
    # 审计记录不含敏感字段
    assert all("password" not in str(i["detail"]).lower() or "已重置" in str(i["detail"]) for i in r.json()["data"]["items"])
