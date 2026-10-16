#!/usr/bin/env bash
# 启动 v2 后端（端口 8012，与 v1.4 的 8011 隔离）
set -e
cd "$(dirname "$0")"
export WORKBENCH_DATA_DIR="${WORKBENCH_DATA_DIR:-$(pwd)/运行数据}"
exec /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8012 --reload
