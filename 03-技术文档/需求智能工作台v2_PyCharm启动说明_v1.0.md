# 需求智能工作台 v2 · PyCharm 启动说明（v1.0）

## 结论

当前保留 3 个 PyCharm 运行配置，分别用于后端、前端 Mock 验收、前端真实 API 联调。

| 运行配置 | 用途 | 是否依赖后端 |
|---|---|---|
| 后端 FastAPI v2 8012 | 启动真实后端 API | - |
| Web 前端 v2 5173 Mock验收 | 验收前端页面和流程 Mock 效果 | 不依赖 |
| Web 前端 v2 5173 API联调 | 验收前端连接真实后端接口 | 依赖后端 8012 |

## 1. 前端 Mock 验收

用于先看页面、交互、状态、流程是否符合产品设计。

启动：

```text
Web 前端 v2 5173 Mock验收
```

环境变量：

```text
VITE_USE_MOCK=true
VITE_API_TARGET=http://127.0.0.1:8012
```

访问：

```text
http://127.0.0.1:5173
```

## 2. 真实 API 联调验收

启动顺序：

1. 启动 `后端 FastAPI v2 8012`。
2. 打开 `http://127.0.0.1:8012/api/healthz`，确认后端返回 ok。
3. 启动 `Web 前端 v2 5173 API联调`。
4. 打开 `http://127.0.0.1:5173` 验收真实 API 效果。

前端 API 联调环境变量：

```text
VITE_USE_MOCK=false
VITE_API_TARGET=http://127.0.0.1:8012
```

## 3. 后端解释器

```text
/Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/.venv/bin/python
```

如果 PyCharm 仍显示无解释器，手动选择这个解释器。

## 4. 兜底启动命令

后端：

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/backend
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012 --reload
```

前端 Mock 验收：

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/frontend
VITE_USE_MOCK=true npm run dev
```

前端 API 联调：

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/frontend
VITE_USE_MOCK=false VITE_API_TARGET=http://127.0.0.1:8012 npm run dev
```


## Playwright Mock 页面验收

已安装 `@playwright/test`，并提供 Mock 登录页冒烟验收脚本：

```bash
cd /Users/macos/Downloads/WorkBuddy/req-workbench/06-项目编码/v2/frontend
VITE_USE_MOCK=true ./node_modules/.bin/vite --host 127.0.0.1 --port 5175 --strictPort
SMOKE_URL=http://127.0.0.1:5175/login node scripts/smoke-mock-login.mjs
```

该脚本会用本机 Chrome 打开登录页，检查页面不再出现 `insertBefore` 渲染错误。


## 6. 前端启动互斥说明

`Web 前端 v2 5173 Mock验收` 和 `Web 前端 v2 5173 API联调` 都使用 5173 端口，同一时间只能启动其中一个。

- 验收前端页面、二维码、公开表单和账号管理 Mock 效果：启动 Mock 验收。
- 验收真实接口、公开提需写入和账号 CRUD：先启动后端 8012，再启动 API 联调。

如需切换模式，先停止当前前端服务，再启动另一个前端配置。
