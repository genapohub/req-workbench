"""P0 安全项验收：自助改密、登录防爆破、初始密码与强制改密标记。

注意：本文件与既有测试同进程运行，登录防爆破用不存在的账号验证，
改密测试用后即改回，避免影响其它测试文件的种子账号登录。
"""
from __future__ import annotations
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="wb_v2_sec_")
os.environ["WORKBENCH_DATA_DIR"] = _TMP
os.environ.setdefault("WORKBENCH_INIT_PASSWORD", "Workbench2026!")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

import pytest  # noqa: E402

PW = "Workbench2026!"
NEW_PW = "NewPass2026x"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client, username, password):
    client.cookies.clear()
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_change_password_wrong_old(client):
    assert login(client, "engineer", PW).json()["code"] == 0
    r = client.post("/api/auth/change-password", json={"old_password": "wrong-old", "new_password": NEW_PW})
    assert r.status_code == 401 and r.json()["code"] == 1002


def test_change_password_weak_new(client):
    assert login(client, "engineer", PW).json()["code"] == 0
    r = client.post("/api/auth/change-password", json={"old_password": PW, "new_password": "short"})
    assert r.status_code == 422 and r.json()["code"] == 3001
    r = client.post("/api/auth/change-password", json={"old_password": PW, "new_password": "onlyletters"})
    assert r.status_code == 422


def test_change_password_success_and_session_invalidation(client):
    # 会话 A
    assert login(client, "engineer", PW).json()["code"] == 0
    sid_a = client.cookies.get("workbench_session")
    # 会话 B（同一账号再登录一次）
    assert login(client, "engineer", PW).json()["code"] == 0
    # 在会话 B 改密
    r = client.post("/api/auth/change-password", json={"old_password": PW, "new_password": NEW_PW})
    assert r.json()["code"] == 0, r.text
    # 旧密码登录失败，新密码成功
    assert login(client, "engineer", PW).json()["code"] == 1002
    assert login(client, "engineer", NEW_PW).json()["code"] == 0
    # 会话 A 已失效
    client.cookies.set("workbench_session", sid_a)
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.json()["code"] == 1001
    # must_change_password 标记已清除
    assert login(client, "engineer", NEW_PW).json()["code"] == 0
    me = client.get("/api/auth/me").json()["data"]
    assert me["user"].get("must_change_password") is False
    # 改回原密码，不影响其它测试
    r = client.post("/api/auth/change-password", json={"old_password": NEW_PW, "new_password": PW})
    assert r.json()["code"] == 0, r.text
    assert login(client, "engineer", PW).json()["code"] == 0


def test_login_lockout_after_five_failures(client):
    # 用不存在的账号验证，避免锁定真实种子账号影响其它测试
    for _ in range(5):
        r = login(client, "ghost-user", "bad-pass-1")
        assert r.json()["code"] == 1002
        assert r.status_code == 401
    r = login(client, "ghost-user", "bad-pass-1")
    assert r.status_code == 429
    assert "锁定" in r.json()["message"]
    # 其它账号不受影响
    assert login(client, "admin", PW).json()["code"] == 0


def test_create_user_random_initial_password(client):
    assert login(client, "admin", PW).json()["code"] == 0
    r = client.post("/api/users", json={"username": "sec-temp-user", "name": "安全测试临时账号"})
    assert r.json()["code"] == 0, r.text
    data = r.json()["data"]
    assert data.get("must_change_password") is True
    initial = data.get("initial_password")
    assert initial and initial != PW
    # 初始密码可登录
    assert login(client, "sec-temp-user", initial).json()["code"] == 0
    # 清理
    assert login(client, "admin", PW).json()["code"] == 0
    r = client.delete(f"/api/users/{data['id']}")
    assert r.json()["code"] == 0


def test_seeded_users_marked_must_change_password(client):
    assert login(client, "admin", PW).json()["code"] == 0
    users = client.get("/api/users").json()["data"]["items"]
    seeded = {u["username"]: u for u in users if u["username"] in {"admin", "product", "employee", "engineer"}}
    # engineer 在上面的测试中已改密过一次（虽改回），标记应为 False；其余初始账号为 True
    assert seeded["admin"]["must_change_password"] is True
    assert seeded["engineer"]["must_change_password"] is False
