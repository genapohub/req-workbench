# 需求智能工作台 v2 API 接口契约（v1.0）

## 1. 基本约定

| 项 | 约定 |
|---|---|
| Base URL | `http://127.0.0.1:8012/api` |
| 鉴权 | HttpOnly Cookie `workbench_session` |
| 统一响应 | `{ "code": 0, "data": {...}, "message": "ok" }` |
| 错误响应 | `{ "code": <业务码>, "data": null, "message": "中文可读" }` |

## 2. 错误码

| code | HTTP | 场景 |
|---|---|---|
| 0 | 200 | 成功 |
| 1001 | 401 | 未登录或会话过期 |
| 1002 | 401 | 账号或密码错误 |
| 1003 | 403 | 无权限 |
| 2001 | 404 | 资源不存在 |
| 2002 | 409 | 唯一性冲突 |
| 3001 | 422 | 参数校验失败，含基座信息缺失 |

## 3. 接口清单

| 模块 | 接口 | 权限 |
|---|---|---|
| 健康检查 | GET /healthz | 公开 |
| 鉴权 | POST /auth/login、POST /auth/logout、GET /auth/me | 登录 |
| 工作概览 | GET /dashboard | overview.view |
| 基座信息 | GET /projects、POST /projects、PUT /projects/{id} | projects.view / projects.manage |
| 需求挖掘 | GET /requirements、POST /requirements、GET /requirements/{id}、PATCH /requirements/{id} | requirements.view / create / review |
| 辅助操作 | POST /requirements/{id}/clarifications、/evidence、/analyze、/deep-dive | requirements.analyze 或本人补充 |
| 导出 | GET /requirements/{id}/export.md | requirements.export |

## 4. 基座字段

| 字段 | 说明 |
|---|---|
| company_business | 公司业务 |
| project_background | 项目背景 |
| progress | 项目进度 |
| business_goals | 业务目标 |
| business_process | 关键流程 |
| constraints | 限制条件 |

`company_business`、`project_background`、`progress` 均非空时，`base_complete=true`。

## 5. 判断字段

| 字段 | 取值 |
|---|---|
| authenticity | pending / supported / contradicted |
| business_relevance | unknown / direct / indirect |
| priority | unassessed / high / medium / low |
| status | draft / clarifying / review / pooled / deferred / rejected |


## 8. 2026-09-30 接口补充契约

### 8.1 公开提需表单

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/public/projects/{project_id}/form` | 无需登录 | 获取项目提需表单展示信息 |
| POST | `/api/public/projects/{project_id}/requirements` | 无需登录 | 公开提交需求原话，生成草稿需求 |

提交字段：`title`、`original` 必填；`scenario`、`problem`、`impact`、`submitter_name`、`submitter_department` 可选。项目基座不完整时返回 `3001`。

### 8.2 账号管理

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/users` | `users.view` | 账号列表和角色选项 |
| POST | `/api/users` | `users.manage` | 新增账号 |
| PUT | `/api/users/{user_id}` | `users.manage` | 编辑账号、角色、部门、状态、密码 |
| DELETE | `/api/users/{user_id}` | `users.manage` | 删除账号，禁止删除当前登录账号 |

角色、菜单和权限当前只作为预留模型返回，不做完整配置页面。

### 8.3 方法论检查字段

需求详情返回 `method_cards`，每项包含：`name`、`status`、`text`。当前内置 JTBD 场景、5 Whys、证据链、RICE 四维四项检查。
