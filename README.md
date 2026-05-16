# AI 项目管理系统

基于 **FastAPI + SQLite + Vue 3 + Element Plus** 搭建的前后端分离项目管理系统。

## 目录结构

```
.
├── backend/                 FastAPI 后端
│   ├── main.py              入口：CORS、路由挂载、全局认证、admin 初始化
│   ├── database.py          SQLAlchemy 引擎 / Session
│   ├── models.py            ORM 模型（含 User 表）
│   ├── schemas.py           Pydantic 请求/响应模型
│   ├── auth.py              密码哈希 + JWT + get_current_user / require_admin
│   ├── config.json          可配置项（当前阶段下拉选项等）
│   ├── routers/
│   │   ├── auth.py          /api/auth/login /register /me
│   │   ├── users.py         /api/users  (仅 admin)
│   │   ├── config.py        /api/config 读取配置
│   │   ├── customer_status.py
│   │   ├── versions.py
│   │   └── iterations.py
│   └── requirements.txt
└── frontend/                Vue 3 前端
    ├── package.json
    ├── vite.config.js       /api 反向代理到 8000
    └── src/
        ├── main.js
        ├── App.vue          整体布局（侧边导航 + 顶部用户条）
        ├── router/          路由 + 登录守卫
        ├── store/auth.js    简易全局 auth 状态
        ├── api/index.js     axios 封装（自动带 token + 401 跳登录）
        └── views/
            ├── Login.vue                    登录 / 注册
            ├── ProjectIntro.vue             项目简介
            ├── CustomerStatus.vue           客户面状态
            ├── VersionManagement.vue        版本管理
            ├── IterationManagement.vue      迭代管理
            └── UserManagement.vue           用户管理（仅 admin 可见）
```

## 启动

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- 启动后访问 http://127.0.0.1:8000/docs 查看 Swagger 文档
- 首次启动自动创建 SQLite 数据库 `app.db`，并写入：
  - 默认管理员账号：**admin / admin123**（请尽快修改）
  - 少量业务示例数据

> 如果你在前一版本上跑过、表结构发生过变更（例如 `customer_status` 长度改变、加了 `users` 表），最简单的方式是删除 `backend/app.db` 后重启，让 SQLAlchemy 重新建表。

#### 生产部署环境变量

| 变量名 | 说明 |
| --- | --- |
| `APP_SECRET_KEY` | JWT 签名密钥，必须修改！默认值 `dev-secret-please-change-in-prod` |

### 前端

```powershell
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5173 进入登录页。

## 页面与功能

| 页面 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| 登录 | `/login` | 公开 | 支持登录与自助注册（注册默认 normal 角色） |
| 项目简介 | `/intro` | 登录用户 | 静态展示 |
| 客户面状态 | `/customer-status` | 登录用户 | 列：机台编号 / 战场 / 当前阶段 / 现场版本 / 近期关注度 / 客户面进展 / 近期重点事务 / 关键问题 |
| 版本管理 | `/versions` | 登录用户 | 含跳转链接 |
| 迭代管理 | `/iterations` | 登录用户 | 含状态、负责人、起止时间 |
| 用户管理 | `/users` | 仅 admin | 增删用户、改角色、禁用、重置密码 |

### 客户面状态特性

- **机台编号 / 战场** 创建后锁定（编辑时禁用），且新建时机台编号唯一校验。
- **当前阶段** 下拉选择，候选项来自 [backend/config.json](backend/config.json) 中的 `current_stages`，运维改文件即可调整选项，前端无需发版。
- **现场版本** 紧跟在「当前阶段」之后，记录机台目前部署的软件版本号；表格内双击可改。
- **近期关注度** 1-5 星，表格内点击星星即时保存。
- **近期重点事务 / 关键问题** 表格内 **双击单元格** 直接编辑，回车保存、ESC 取消。

### 配置文件示例 [backend/config.json](backend/config.json)

```json
{
  "current_stages": ["装机", "T0-T1", "T1-T2", "T2-T3", "T3 Release", "验收完成"]
}
```

## 用户管理与认证

- **认证方式**：本地账号 + JWT（HS256，7 天有效），通过 `Authorization: Bearer <token>` 携带。
- **角色**：
  - `admin` — 可访问用户管理；其他业务接口同 normal。
  - `normal` — 可读写所有业务数据。
- **注册策略**：
  - 自助注册：`/login` 页面 "注册" Tab，固定生成 normal 角色。
  - 管理员创建：`/users` 页面，可指定角色。
- **企业 SSO 预留**：`users` 表带 `auth_provider` 字段（local / company_sso），后续接公司账号体系时新增对应登录路径即可，不必改表结构。

## 后续可优化方向

- 接入公司 SSO（OIDC / LDAP）的实际实现
- 用户操作审计日志
- 表格筛选、分页、导出 Excel
- 版本管理增加 changelog Markdown 渲染、附件上传
- 迭代管理增加甘特图视图
- 使用 Alembic 管理数据库迁移（替代 `create_all`）
- Docker Compose 一键部署 + Nginx 反向代理

## 更新日志

### v0.5.0 — 2026-05-16

**客户面状态页改造**
- 列结构调整：机台编号 / 客户（原战场，仅 UI 重命名）/ 型号（新字段 `model`） / 当前阶段 / 现场版本 / 近期关注度 / 当前进展 / 近期现场关键诉求 / 软件类风险和问题。
- 创建后锁定：机台编号、客户、型号（编辑弹窗禁用，后端 schema 也不接受）。
- 字段级权限：
  - **仅管理员可改**：当前阶段、现场版本、近期关注度（前端控件 disable，后端 PUT 校验返回 403）。
  - **所有登录用户可改**：当前进展、近期现场关键诉求、软件类风险和问题（行内双击编辑，立即保存）。
- 新增 / 编辑 / 删除按钮均收紧为管理员可见。
- 新增「导出 PPT」按钮（admin 限定），调用 `GET /api/customer-status/export.pptx`，单页 16:9 表格输出当前全量数据。

**迭代管理页面重构**
- 顶层视图改为年度规划：年份切换器 + 12 行月度迭代表格（不存在的月份自动占位）。
  - 列：月份 / 迭代名称 / 负责人 / 状态 / 迭代目标。
  - 迭代名称、负责人、目标、状态：仅管理员可改（双击或下拉切换）。
  - 点击「迭代名称」或「进入」跳转 `/iterations/:id` 子页面。
- 子页面 `IterationDetail`：需求清单表格。
  - 列：序号 / 需求编号（带超链接）/ 需求标题 / 责任人 / 优先级 / 计划交付版本 / 交付进展跟踪（含 6 个子状态列：需求串讲 / 反串讲 / STC设计 / 编码 / BBIT / 转测澄清）。
  - 子状态枚举：未开始 / 进行中 / 已完成 / 已延期 / 不涉及，直接下拉即时保存。
  - 普通字段支持双击行内编辑或「完整编辑」弹窗。
  - 「导出 PPT」按钮（admin 限定）：调用 `GET /api/annual-iterations/{id}/export.pptx`，输出该迭代全量需求的单页 16:9 表格。

**数据模型 & 路由**
- 新增 `AnnualIteration`（年/月唯一）、`IterationRequirement`（外键挂到年度迭代）两张表，旧的 `iterations` 表保留兼容。
- 新增 [routers/annual_iterations.py](backend/routers/annual_iterations.py)、[routers/iteration_requirements.py](backend/routers/iteration_requirements.py)、[pptx_utils.py](backend/pptx_utils.py)（PPT 生成）。
- [migrate.py](backend/migrate.py) 自动给老库补 `customer_status.model` 列；新增的两张表通过 `Base.metadata.create_all` 自动建。
- 启动种子：当前自然年自动生成 12 个迭代占位 + 当前月份示例需求一条。

**依赖**
- requirements.txt 新增 `python-pptx==1.0.2`，请在后端环境执行 `pip install -r requirements.txt`。

**升级提示**
- 老库（v0.4.0 → v0.5.0）无需删 `app.db`，启动会自动迁移并补齐种子。

### v0.4.0 — 2026-05-14

**客户面状态页：新增「现场版本」列**
- 数据模型：[models.py](backend/models.py) `CustomerStatus.field_version`（VARCHAR(128)，默认空串）；[schemas.py](backend/schemas.py) 同步加字段。
- 列位置在「当前阶段」与「近期关注度」之间。
- 支持表格内双击行内编辑（与「近期重点事务」「关键问题」一致），回车保存、ESC 回滚。
- 新增 / 编辑弹窗也加了「现场版本」输入框。
- 种子示例数据补 `field_version` 值。

**轻量迁移**
- [migrate.py](backend/migrate.py) `_ADDITIONS` 追加 `customer_status.field_version` 一项，老库（v0.3.0）启动时自动 `ALTER TABLE ADD COLUMN`，无需删 `app.db`。

### v0.3.0 — 2026-05-13

**客户面状态页增强**
- 「当前阶段」下拉候选改为固定的项目阶段：装机 / T0-T1 / T1-T2 / T2-T3 / T3 Release / 验收完成，写在 [backend/config.json](backend/config.json)，运维改文件即可调整。
- 新增「近期关注度」列，紧跟在「当前阶段」之后，使用 1-5 星表示（0 表示未评估）：
  - 数据模型：[models.py](backend/models.py) `CustomerStatus.attention_level` 整型字段，默认 0；schema 在 `CustomerStatusBase` / `CustomerStatusUpdate` 同步加字段。
  - 表格内点击星星即时保存（局部 `PUT { attention_level }`），无需打开编辑弹窗；失败自动回滚。
  - 新增 / 编辑弹窗中也加了 `el-rate` 控件。
- 种子示例数据带上 `attention_level`，启动后立刻能看到星级效果。

**轻量数据库迁移**
- 新增 [backend/migrate.py](backend/migrate.py)，启动时检查 `customer_status` 表是否缺少 `attention_level` 列，通过 `ALTER TABLE ADD COLUMN` 自动补齐。后续再有简单加列场景只需在 `_ADDITIONS` 列表追加一项。
- 老库 **无需删除** `app.db` 即可平滑升级到本版本（v0.2.0 → v0.3.0）。如果你是从 v0.1.0 直接升级，由于当时还没有 `users` 表 / `customer_status` 字段长度变更，仍建议删 db 重启。

### v0.2.0 — 2026-05-13

**客户面状态页改进**
- 机台编号、战场首次保存后锁定，编辑弹窗中两个字段 `disabled`；后端 `PUT /api/customer-status/{id}` 的 schema 收窄为仅接受 `current_stage / customer_status / recent_focus / key_issues` 四个字段（[backend/schemas.py](backend/schemas.py) 中 `CustomerStatusUpdate`），即使前端被绕过也无法改这两列。
- 新建时机台编号唯一性校验（[routers/customer_status.py](backend/routers/customer_status.py)）。
- "当前阶段" 改为下拉，候选项由 [backend/config.json](backend/config.json) 的 `current_stages` 提供，通过新接口 `GET /api/config` 暴露给前端；运维改文件即可调整，前端无需发版。
- 字段重命名：「客户面状态」→「客户面进展」（仅 UI 标签变更，数据库字段名保留 `customer_status` 以避免迁移）。
- 「近期重点事务」「关键问题」两列支持 **双击单元格行内编辑**，回车 / 失焦保存（局部 PUT，只发改动字段），ESC 取消并回滚。

**新增用户管理系统**
- 后端：新增 [auth.py](backend/auth.py)（bcrypt 哈希 + python-jose JWT + `get_current_user` / `require_admin` 依赖）、[routers/auth.py](backend/routers/auth.py)（`/login` `/register` `/me`）、[routers/users.py](backend/routers/users.py)（admin 专属 CRUD）。
- 业务路由全部挂载 `Depends(get_current_user)` 全局认证；用户管理路由内层挂 `require_admin`。
- 数据模型新增 `User` 表（[models.py](backend/models.py)），字段含 `role` (admin/normal)、`is_active`、`auth_provider` (local/company_sso，为公司 SSO 预留)。
- 首次启动自动注入 `admin / admin123` 账号（[main.py](backend/main.py) `seed_initial_data`）。
- 安全约束：管理员不能修改自己的角色、不能禁用自己、不能删除自己。
- 前端：新增 [store/auth.js](frontend/src/store/auth.js) 全局 auth 状态（token + user，持久化到 localStorage）、[Login.vue](frontend/src/views/Login.vue)（登录 / 注册 Tab）、[UserManagement.vue](frontend/src/views/UserManagement.vue)（admin 可见的用户表格）。
- axios 拦截器自动注入 `Authorization: Bearer ...`，收到 401 自动清 session 并跳登录页（[api/index.js](frontend/src/api/index.js)）。
- 路由守卫：未登录跳 `/login`、`requireAdmin` 路由对 normal 用户隐藏（[router/index.js](frontend/src/router/index.js)）；侧边菜单同步按角色过滤。
- [App.vue](frontend/src/App.vue) 头部加用户下拉（显示姓名 + admin 标签 + 退出）；登录页使用独立无侧栏布局（`meta.layout: 'blank'`）。

**部署相关**
- 新增环境变量 `APP_SECRET_KEY` 用于 JWT 签名，默认 `dev-secret-please-change-in-prod`，**生产必须覆盖**。
- requirements.txt 新增依赖：`python-jose[cryptography]`、`bcrypt`、`python-multipart`。

**迁移注意**
- 数据库表结构有变更（新增 `users` 表、`customer_status.customer_status` 字段长度由 128 增至 256）。SQLAlchemy 的 `create_all` 不会修改已有表，**升级时请删除 `backend/app.db` 后重启**让其重新建表。

### v0.1.0 — 2026-05-13

- 初版骨架：FastAPI + SQLite + Vue 3 + Element Plus
- 4 个页面：项目简介 / 客户面状态 / 版本管理 / 迭代管理
- 所有业务模块基础 CRUD
