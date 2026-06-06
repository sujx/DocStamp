# 用户管理与后台管理功能实施计划

## 概述

为 docStamp 增加用户管理、后台管理功能，页面可直接浏览。管理员 admin/Admin123。管理员可为用户开启隐藏功能（AI Chat、看板、资源汇总）。

---

## 架构

**认证方案**：Flask session + SQLite 本地数据库  
**前端方案**：Nuxt composable 管理认证状态 + 登录页 + 管理后台 + 路由守卫

---

## 数据库设计

### SQLite 表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',    -- 'admin' | 'user'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 功能开关表
CREATE TABLE feature_toggles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    feature TEXT NOT NULL,       -- 'ai-chat' | 'kanban' | 'resources'
    enabled INTEGER DEFAULT 0,  -- 0=关闭, 1=开启
    UNIQUE(username, feature),
    FOREIGN KEY(username) REFERENCES users(username)
);
```

### 初始化数据

```sql
-- 管理员账号（密码：Admin123，werkzeug 哈希）
INSERT INTO users (username, password_hash, role)
VALUES ('admin', 'pbkdf2:sha256:...', 'admin');

-- 默认开启的功能
INSERT INTO feature_toggles (username, feature, enabled) VALUES
('admin', 'ai-chat', 0),
('admin', 'kanban', 0),
('admin', 'resources', 0);
```

---

## 后端实现

### 文件：`backend/auth.py`（新建）

```
Flask Blueprint 路由：
  POST /api/auth/login       — 登录（验证用户名密码，设置 session）
  POST /api/auth/logout      — 登出（清除 session）
  GET  /api/auth/status      — 返回当前用户状态（logged_in, username, role, features）
  GET  /api/admin/users      — [admin] 列出所有用户
  PUT  /api/admin/toggle     — [admin] 切换用户功能开关
```

### 文件：`backend/db.py`（新建）

```
数据库操作：
  init_db()                  — 创建表 + 初始化 admin 账号
  get_db()                   — 获取数据库连接（g 上下文）
  verify_user(username, pw)  — 验证用户密码
  get_features(username)     — 获取用户已开启的功能列表
  set_feature(username, feature, enabled) — 设置功能开关
  get_all_users()            — 获取所有用户列表
```

### 文件：`backend/app.py`（修改）

- `app.config["SECRET_KEY"] = "docstamp-secret-2026"`
- `app.config["DATABASE"] = "docstamp.db"`
- CORS 配置 `supports_credentials=True`
- 注册 auth blueprint
- `@app.before_request` 初始化数据库

---

## 前端实现

### 文件：`frontend/composables/useAuth.ts`（新建）

```typescript
export function useAuth() {
  const user = ref(null)                    // { username, role }
  const features = ref([])                  // ['ai-chat', 'kanban', ...]
  const isAdmin = computed(...)

  async function checkStatus()    // GET /api/auth/status
  async function login(u, p)      // POST /api/auth/login
  async function logout()         // POST /api/auth/logout
  function hasFeature(f)          // 检查功能是否开启

  return { user, features, isAdmin, checkStatus, login, logout, hasFeature }
}
```

### 文件：`frontend/pages/login.vue`（新建）

居中登录卡片：
- 用户名输入框 + 密码输入框
- 登录按钮 + 错误提示
- 成功后跳转首页

### 文件：`frontend/pages/admin.vue`（新建）

管理后台（仅 admin 可访问）：
- 用户列表表格（用户名、角色、已开启功能）
- 每行：功能开关（ai-chat / kanban / resources 复选框）
- 保存按钮

### 文件：隐藏页面（新建 3 个）

- `frontend/pages/ai-chat.vue` — AI 对话页面（默认占位）
- `frontend/pages/kanban.vue` — 看板页面（默认占位）
- `frontend/pages/resources.vue` — 资源汇总页面（默认占位）

### 文件：`frontend/components/Sidebar.vue`（修改）

导航列表动态化：
- 底部增加"登录"/"管理后台"/"登出"入口
- 隐藏页面（ai-chat / kanban / resources）根据 `hasFeature()` 条件显示
- 未登录显示公共导航 + "登录"按钮
- 登录后根据功能开关显示隐藏页面

### 文件：`frontend/layouts/default.vue`（修改）

- `onMounted` 时调用 `useAuth().checkStatus()`
- 顶部栏显示用户名

### 文件：`frontend/middleware/auth.ts`（新建）

路由守卫（可选）：
- 访问 `/admin` 时检查 admin 角色
- 访问隐藏页面时检查功能开关

---

## 实施步骤

1. 安装 `werkzeug` 依赖 → 创建 `backend/db.py`（SQLite 初始化 + 操作函数）
2. 创建 `backend/auth.py`（Flask Blueprint 路由）
3. 修改 `backend/app.py`（注册路由、CORS 配置、数据库初始化）
4. 创建 `frontend/composables/useAuth.ts`
5. 创建 `frontend/pages/login.vue`
6. 创建 `frontend/pages/admin.vue`
7. 创建 3 个隐藏页面（ai-chat / kanban / resources）
8. 修改 `frontend/components/Sidebar.vue`（条件导航）
9. 修改 `frontend/layouts/default.vue`（启动时检查认证）
10. 验证：登录/登出、功能开关、隐藏页面可见性

---

## 验证

- [ ] `/` 仪表盘无需登录可访问（公开）
- [ ] `/login` 登录页，admin/Admin123 登录成功
- [ ] 登录后侧栏显示"管理后台"链接
- [ ] `/admin` 管理页面可切换功能开关
- [ ] 开启 ai-chat 后侧栏出现"AI Chat"链接
- [ ] `/ai-chat` / `/kanban` / `/resources` 页面正常显示
- [ ] 登出后隐藏页面消失
- [ ] `nuxt generate` 构建成功

---

## 附录 A：解耦合设计方案

### 当前问题

`backend/app.py` 1300+ 行，包含全部 24 个路由、配置、中间件、工具函数。随着功能增加（用户管理、后台管理），单文件将进一步膨胀，难以维护。

### 目标架构

```
backend/
├── app.py              # 仅工厂函数 create_app()（<50行）
│                        #   - 创建 Flask 实例
│                        #   - 注册所有 Blueprint
│                        #   - 配置 CORS/Babel/日志
├── config.py           # 配置类 Config（集中管理所有常量）
│                        #   - SECRET_KEY, DATABASE, UPLOAD_FOLDER
│                        #   - 文件扩展名白名单
│                        #   - 日志配置
├── db.py               # SQLite 数据库层（独立模块，零 Flask 依赖）
│                        #   - init_db() / get_db()
│                        #   - 用户 CRUD / 功能开关 CRUD
│                        #   - 使用 Flask g 上下文管理连接
├── utils/
│   ├── file_helpers.py # 文件验证 _validate_filename()
│   │                    # 文件上传 _save_upload()
│   │                    # 文件清理 _cleanup_files()
│   └── security.py     # 密码哈希 / 登录装饰器
├── blueprints/          # 路由层（每个文件只处理 HTTP 请求/响应）
│   ├── auth.py         # /api/auth/*     (登录/登出/状态)
│   ├── admin.py        # /api/admin/*    (用户管理/功能开关)
│   ├── convert.py      # /api/convert/*  (MD→DOCX/反向/格式化)
│   ├── files.py        # /api/properties, /api/img2pdf, /api/watermark, ...
│   └── download.py     # /api/download, /api/health, /api/stats
└── services/            # 业务逻辑层（纯函数，零 Flask 依赖，可独立测试）
    ├── converter.py    # md_to_docx, convert_to_md, ...
    ├── formatter.py    # format_docx (GB/T 9704-2012)
    ├── watermark.py    # add_watermark, remove_watermark
    ├── pdf_editor.py   # pdf_delete_pages, pdf_insert_pages, ...
    ├── img2pdf_handler.py
    ├── pdf_to_images.py
    ├── print_split.py
    ├── excel_merger.py
    └── properties.py
```

### 关键原则

| 原则 | 说明 |
|------|------|
| **Blueprint 只做 HTTP** | 路由函数不超过 10 行，只负责参数提取/调用 service/返回响应 |
| **services 零依赖** | 不 import Flask/request/session，纯输入→输出函数，可独立单元测试 |
| **db.py 隔离数据层** | 所有 SQL 操作集中在一个模块，其他模块只调用函数接口 |
| **config 集中管理** | 所有常量和配置项统一在 Config 类中，不散落各处 |
| **utils 可复用** | 文件处理、安全工具提取到 utils/，Blueprint 和 services 都可以引用 |

### 迁移路径

1. **先提取 utils** — `_validate_filename`/`_save_upload`/`_cleanup_files` → `utils/file_helpers.py`
2. **再拆分 blueprint** — 按功能域将路由拆分到 `blueprints/` 目录
3. **最后抽离 config** — 将 Config 类移到 `config.py`
4. **数据库独立** — `db.py` 管理 SQLite 连接和操作
5. **保持 services 不变** — 已有的 converter/formatter/watermark 等已是纯函数，直接复用

### 解耦后的 `app.py`（示例）

```python
from flask import Flask
from flask_babel import Babel
from flask_cors import CORS
from config import Config
from db import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, supports_credentials=True)
    Babel(app)
    
    # 注册 Blueprint
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.convert import convert_bp
    from blueprints.files import files_bp
    from blueprints.download import download_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(convert_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(download_bp)
    
    with app.app_context():
        init_db()
    
    return app
```

### 前端解耦

| 层 | 位置 | 职责 |
|----|------|------|
| 页面 | `pages/` | 路由入口，只组装组件 |
| 组件 | `components/` | UI 呈现，通过 props/emits 通信 |
| 组合式函数 | `composables/` | 共享逻辑（useAuth, useDownload） |
| 状态 | `composables/useAuth.ts` | 全局认证状态（替代 Pinia） |
| 布局 | `layouts/` | 页面框架壳 |
