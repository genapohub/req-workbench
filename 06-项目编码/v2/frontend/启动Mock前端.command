#!/bin/bash
# 双击启动：需求智能工作台 v2 前端（Mock 模式，无需后端）
# 启动后浏览器打开 http://127.0.0.1:5173
# 登录：admin / Workbench2026! （或点登录页 demo 快捷按钮）
# 停止：在本窗口按 Ctrl+C
cd "$(dirname "$0")" || exit 1

NPM="/Users/macos/.workbuddy/binaries/node/versions/22.22.2-3/bin/npm"
if [ ! -x "$NPM" ]; then
  export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
  NPM="npm"
fi

echo "=========================================="
echo " 需求智能工作台 v2 · 前端 Mock 模式启动中..."
echo " 启动后请用浏览器打开: http://127.0.0.1:5173"
echo " 登录: admin / Workbench2026!"
echo " 停止: 按 Ctrl+C"
echo "=========================================="
exec "$NPM" run dev
