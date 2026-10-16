#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="/Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/.venv/bin/python"
PORT="${WORKBENCH_PORT:-8012}"
if [ ! -x "$PYTHON" ]; then
  echo "找不到项目 Python 解释器：$PYTHON"
  exit 1
fi
"$PYTHON" - <<'CHECK'
import importlib
for name in ["uvicorn", "fastapi", "app.main"]:
    importlib.import_module(name)
print("依赖检查通过")
CHECK
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --reload
