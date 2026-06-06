# docStamp RPD — 需求与规划文档

> 反向推导自 SPEC.md + 实际代码实现  
> 状态标记：✅ 已落地 / 🔧 规划中 / 🗑 已移除

---

## 一、项目定义

| 属性 | 值 |
|------|-----|
| 名称 | docStamp |
| 类型 | 一站式文档处理工具箱 |
| 前端 | Nuxt 4 + Nuxt UI v4 + Tailwind CSS v4 |
| 后端 | Flask 3 + Python 3.12 |
| 数据库 | SQLite（规划支持 MySQL/PG 迁移） |
| 认证 | Flask Session（规划中） |
| 品牌色 | #008a3d（绿鹃绿）+ #f9f7e8（米黄底） |
| i18n | zh-CN（主）+ en（入口保留） |

---

## 二、功能矩阵

### 已落地（✅）

| F# | 功能 | 路由 | 分组 | 核心能力 |
|----|------|------|------|---------|
| F1 | MD 转公文 | `/md-to-docx` | — | Markdown → GB/T 9704-2012 DOCX，marked.js 实时预览，Pandoc + python-docx 后处理，自动下载 |
| F2 | 水印管理 | `/watermark` | — | 添加（文字/图片，Canvas 预览）+ 去除（DOCX 页眉清除 + PDF 三层策略） |
| F3 | 属性修改 | `/properties` | Office | .docx/.xlsx/.pptx 元数据，单文件/批量，统一/分别时间 |
| F4 | Excel 合并 | `/excel-merge` | Office | .xlsx/.csv 合并，openpyxl 逐行追加，列标题一致性校验 |
| F5 | 格式规范 | `/format-docx` | Office | DOCX → GB/T 9704-2012，页边距/字体/行距/标题层级/页码 |
| F6 | 文件组装 | `/file-assembly` | PDF | 图片→PDF（img2pdf/reportlab）+ PDF→图片（pdftoppm，进度条） |
| F7 | 打印分组 | `/print-split` | PDF | pypdf 拆分，暂停/继续/终止，定时自动下载 |
| F8 | PDF 编辑 | `/pdf-editor` | PDF | 删除/插入/重排页面，pdftoppm 缩略图，拖拽排序 |

### 规划中（🔧）

| F# | 功能 | 路由 | 依赖 |
|----|------|------|------|
| F9 | 用户登录 | `/login` | SQLite + Flask Session + werkzeug，60/40 分屏设计 |
| F10 | 个人信息 | `/profile` | 首字 SVG 默认头像 + 自定义上传 + 昵称修改 |
| F11 | 管理后台 | `/admin` | 用户管理 + 功能开关（feature_toggles 表） |
| F12 | 系统设置 | `/settings` | AI 配置（厂商/密钥/模型/Prompt）+ 数据库迁移 |
| F13 | AI Chat | `/ai-chat` | 支持 MaxKB 嵌入 / 直连 API 双模式 |
| F14 | 看板 | `/kanban` | 隐藏功能，管理员开启后可见 |
| F15 | 资源汇总 | `/resources` | 隐藏功能，管理员开启后可见 |

### 已移除（🗑）

| 功能 | 原因 |
|------|------|
| 电子书转 MD | 优先级调整 |

---

## 三、架构设计

### 后端解耦（规划中）

```
backend/
├── app.py              # Flask 工厂（<50行）
├── config.py           # 统一配置
├── db.py               # SQLite 层（支持 MySQL/PG 适配）
├── blueprints/         # 路由层
│   ├── auth.py, admin.py, chat.py
│   ├── convert.py, files.py, download.py
├── services/           # 业务逻辑（纯函数）
└── utils/              # 工具函数
```

### 前端分层（✅）

```
frontend/
├── pages/              # 8 个路由页面
├── components/         # 15+ 组件
│   ├── Sidebar.vue     # 分组悬浮子菜单
│   ├── DigitalClock.vue # 7 段数码管时钟
│   └── ...
├── composables/        # useDownload.ts
├── layouts/default.vue # provide/inject 侧栏状态
└── i18n/locales/       # zh-CN / en
```

### 数据库（规划中）

```sql
users(id, username, password_hash, role, nickname, avatar_type, avatar_color)
feature_toggles(id, username, feature, enabled)
settings(key, value, updated_at)
```

---

## 四、UI 设计规范

### 配色系统

| Token | 值 | 用途 |
|-------|-----|------|
| brand-700 | #008a3d | 主色 |
| page | #f9f7e8 | 页面底 |
| surface | #ffffff | 卡片白 |
| muted | #f4f2e4 | 次级区域 |
| text-primary | #1a1a1a | 正文 |
| text-secondary | #5c5c5c | 辅助 |
| text-tertiary | #8c8a7a | 提示 |
| border-default | #e8e6d8 | 边框 |
| border-subtle | #f0efe5 | 细线 |

### 布局

- 侧栏：240px（可折叠 64px），localStorage 持久化，provide/inject 共享
- 内容：max-w-5xl，mx-auto
- 仪表盘：DigitalClock + 3 列工具卡片网格
- 子功能：2 列卡片式切换
- 标题：text-balance，正文：text-pretty

### 组件体系

Nuxt UI v4：UButton, UInput, USelect, UTabs, UFormField, UAlert, UProgress, UIcon

### baseline-ui 合规

- h-dvh ✓
- aria-label 图标按钮 ✓
- safe-area-inset 固定元素 ✓
- CSS 变量禁止硬编码颜色 ✓
- 禁止 transition:all ✓

---

## 五、API 端点

### 已实现（21 个）

| Method | Path | 对应功能 |
|--------|------|---------|
| GET | /api/health | 健康检查 |
| GET | /api/stats | 转换计数 |
| POST | /api/preview | F1 |
| POST | /api/convert | F1 |
| POST | /api/convert/format-docx | F5 |
| GET | /api/download/<id> | F1/F5 |
| POST | /api/properties | F3 |
| POST | /api/properties/info | F3 |
| POST | /api/properties/batch | F3 |
| POST | /api/img2pdf | F6 |
| POST | /api/pdf2img | F6 |
| POST | /api/print-split | F7 |
| GET | /api/print-split/<id>/batch/<n> | F7 |
| POST | /api/watermark | F2 |
| POST | /api/watermark/remove | F2 |
| POST | /api/pdf-editor/info | F8 |
| GET | /api/pdf-editor/thumb/... | F8 |
| POST | /api/pdf-editor/delete | F8 |
| POST | /api/pdf-editor/insert | F8 |
| POST | /api/pdf-editor/reorder | F8 |
| POST | /api/excel-merge | F4 |

### 规划中（11 个）

| Method | Path | 对应功能 |
|--------|------|---------|
| POST | /api/auth/login | F9 |
| POST | /api/auth/logout | F9 |
| GET | /api/auth/status | F9 |
| GET/PUT | /api/user/profile | F10 |
| POST/DELETE | /api/user/avatar | F10 |
| GET | /api/avatar/<username>.svg | F10 |
| GET | /api/admin/users | F11 |
| PUT | /api/admin/toggle | F11 |
| GET/PUT | /api/admin/settings | F12 |
| PUT | /api/admin/settings/database | F12 |
| POST | /api/admin/settings/database/migrate | F12 |
| POST | /api/chat | F13 |

### 已移除

| Method | Path |
|--------|------|
| POST | /api/convert/doc2md |

---

## 六、依赖

| 层 | 依赖 |
|----|------|
| Python | flask, flask-cors, flask-babel, python-docx, openpyxl, python-pptx, markdown, bleach, img2pdf, pypdf, Pillow, reportlab, gunicorn |
| 系统工具 | Pandoc, LibreOffice (headless), poppler-utils (pdftoppm) |
| Nuxt | nuxt@^4.4, @nuxt/ui@^4.8, @nuxt/icon@^2.2, @nuxtjs/i18n@^10.4 |
| 前端 lib | axios, marked, highlight.js, dompurify, mermaid, katex (可选) |
| 规划新增 | werkzeug, pymysql, psycopg2 |

---

## 七、通用组件清单（✅）

| 组件 | 用途 | Props |
|------|------|-------|
| Sidebar | 分组悬浮子菜单导航 | collapsed (provide) |
| PageHeader | 返回链接 | backTo |
| ToolCard | 仪表盘工具卡片 | icon, title, description, to |
| FileUploader | 文件拖放上传 | icon, hint, accept |
| FileList | 文件列表 | files: FileItem[] |
| EmptyState | 空状态占位 | icon, title, description |
| DigitalClock | 7 段数码管时钟 | digitColor, offColor, glowColor |
| LanguageSwitcher | 语言切换 | collapsed |

---

## 八、版本演进

| 版本 | 日期 | 关键变更 |
|------|------|---------|
| v1.0 | 2026-06 | 5 功能，Buefy + Flask |
| v2.0 | 2026-06 | Nuxt 4 架构升级，新增 4 功能 |
| v2.1 | 2026-06 | baseline-ui 合规，水印增强 |
| v2.2 | 2026-06 | 移除电子书转 MD，SPEC+DEV_GUIDE 合并 |
| v2.3 | 2026-06 | 侧栏分组菜单，DigitalClock，侧栏持久化 |
| v2.4 | 规划 | 用户认证，AI Chat，数据库迁移 |
