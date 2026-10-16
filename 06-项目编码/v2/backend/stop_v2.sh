#!/usr/bin/env bash
# v2 后端停止脚本（AC-25）
# 仅匹配 8012 端口的 v2 uvicorn 进程，绝不波及 v1.4（8011）或其它服务。
set -u
PATTERN="uvicorn app.main:app --host 127.0.0.1 --port 8012"
PIDS="$(pgrep -f "$PATTERN" || true)"

if [ -z "$PIDS" ]; then
  echo "未找到 v2 后端进程（8012），无需停止"
  exit 0
fi

echo "将停止以下 v2 进程（PID）：$PIDS"
pkill -f "$PATTERN"

for _ in $(seq 1 10); do
  if pgrep -f "$PATTERN" >/dev/null 2>&1; then
    sleep 0.5
  else
    break
  fi
done

if pgrep -f "$PATTERN" >/dev/null 2>&1; then
  echo "警告：进程未在预期时间内退出" >&2
  exit 1
fi
echo "v2 后端（8012）已停止，端口已释放"
