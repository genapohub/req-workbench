from __future__ import annotations
import os
import time
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("WORKBENCH_DATA_DIR", str(BACKEND_ROOT / "运行数据")))
DB = DATA / "工作台.sqlite3"
COOKIE = "workbench_session"
PORT = 8012

VERSION = "2.1.0-narrow"


def uid() -> str:
    return uuid.uuid4().hex


def now() -> int:
    return int(time.time())


PERMISSIONS: dict[str, str] = {
    "overview.view": "工作概览",
    "projects.view": "查看基座信息",
    "projects.manage": "维护基座信息",
    "requirements.view": "查看需求",
    "requirements.create": "提交需求",
    "requirements.analyze": "需求挖掘与辨伪",
    "requirements.review": "需求评审",
    "requirements.export": "需求导出",
    "users.view": "查看账号",
    "users.manage": "管理账号",
    "audit.view": "查看审计日志",
}

MENUS = [
    {"id": "overview", "label": "工作概览", "permission": "overview.view"},
    {"id": "requirements", "label": "需求挖掘", "permission": "requirements.view"},
    {"id": "projects", "label": "基座信息", "permission": "projects.view"},
    {"id": "users", "label": "账号管理", "permission": "users.view"},
    {"id": "audit-logs", "label": "审计日志", "permission": "audit.view"},
]

ROLE_DEFAULTS = {
    "admin": list(PERMISSIONS.keys()),
    "pm": [
        "overview.view", "projects.view", "projects.manage",
        "requirements.view", "requirements.create", "requirements.analyze",
        "requirements.review", "requirements.export", "users.view", "users.manage",
    ],
    "staff": ["overview.view", "projects.view", "requirements.view", "requirements.create"],
    "tech": ["overview.view", "projects.view", "requirements.view", "requirements.review"],
}

STATUS_LABELS = {
    "draft": "草稿", "clarifying": "澄清中", "review": "待评审",
    "pooled": "已入池", "deferred": "暂缓", "rejected": "不采纳",
}

AUTHENTICITY_LABELS = {
    "pending": "待验证", "supported": "已佐证", "contradicted": "存在反证",
}

BUSINESS_RELEVANCE_LABELS = {
    "unknown": "待明确", "direct": "直接相关", "indirect": "间接相关",
}
