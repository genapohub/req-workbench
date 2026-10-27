from __future__ import annotations
import json
import os
import re
import time

import httpx

from app.audit import record as audit

# OpenAI 兼容接入：不配 WORKBENCH_LM_API_KEY 时全部能力回退规则引擎，零回归。
# 密钥只走环境变量，不入库不入仓。
DEFAULT_BASE_URL = "https://api.openai.com/v1"
TIMEOUT_SECONDS = 20


def enabled() -> bool:
    return bool(os.environ.get("WORKBENCH_LM_API_KEY"))


def _config() -> tuple[str, str, str]:
    return (
        os.environ.get("WORKBENCH_LM_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        os.environ.get("WORKBENCH_LM_API_KEY", ""),
        os.environ.get("WORKBENCH_LM_MODEL", "gpt-4o-mini"),
    )


def chat(messages: list[dict], purpose: str, conn=None, user: dict | None = None) -> str | None:
    """调用 LLM 并落审计；未启用或失败时返回 None（调用方回退规则引擎）。"""
    if not enabled():
        return None
    base_url, api_key, model = _config()
    started = time.time()
    content = None
    error = ""
    usage = {}
    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, "temperature": 0.2},
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
    except Exception as e:  # 网络/鉴权/解析失败一律回退，不影响主链路
        error = str(e)[:200]
    if conn is not None:
        audit(conn, "llm.call", user=user, detail={
            "purpose": purpose,
            "model": model,
            "duration_ms": int((time.time() - started) * 1000),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "success": content is not None,
            "error": error,
        })
    return content


def extract_json_array(text: str | None) -> list:
    """从 LLM 输出中宽容提取第一个 JSON 数组；失败返回 []。"""
    if not text:
        return []
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, list) else []
    except Exception:
        return []
