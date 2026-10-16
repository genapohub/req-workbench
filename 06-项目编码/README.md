# 需求智能工作台 v2 编码说明

## 1. 当前保留内容

```text
06-项目编码/
├── .venv/          # 项目本地 Python 解释器
├── README.md
└── v2/
    ├── backend/    # FastAPI 后端
    └── frontend/   # Vue Web 前端
```

## 2. PyCharm 运行配置

| 配置 | 用途 |
|---|---|
| 后端 FastAPI v2 8012 | 启动真实后端 API |
| Web 前端 v2 5173 Mock验收 | 验收前端 Mock 页面和流程 |
| Web 前端 v2 5173 API联调 | 验收前端连接真实后端 API |

Mock 验收不依赖后端；API 联调需要先启动后端。

## 3. 验证命令

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/backend
../../.venv/bin/python -m pytest tests -q
```

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/frontend
npm run build
```


## Playwright Mock 页面验收

已安装 `@playwright/test`，并提供 Mock 登录页冒烟验收脚本：

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/frontend
VITE_USE_MOCK=true ./node_modules/.bin/vite --host 127.0.0.1 --port 5175 --strictPort
SMOKE_URL=http://127.0.0.1:5175/login node scripts/smoke-mock-login.mjs
```

该脚本会用本机 Chrome 打开登录页，检查页面不再出现 `insertBefore` 渲染错误。
