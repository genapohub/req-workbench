#!/usr/bin/env bash
# v2 后端状态检查脚本（AC-25）
set -u
URL="${WB_V2_URL:-http://127.0.0.1:8012/api/healthz}"
if curl -s --noproxy '*' --max-time 3 "$URL" >/dev/null 2>&1; then
  echo "v2 后端（8012）运行中，健康检查："
  curl -s --noproxy '*' "$URL"
  echo
else
  echo "v2 后端（8012）未运行"
fi
