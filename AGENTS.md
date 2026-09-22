# AGENTS.md — 鹊随金印 (docStamp) 项目规范

## 项目概述

鹊随金印是一站式文档处理工具箱。Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 前端，Flask REST API 后端。SynTime Royal Blue 品牌色系，仪表盘 + 侧边导航 + 多页面路由，中英文双语。

**定位**：单体工具，无用户系统，无认证，AI 可选（未配 Key 自动降级）——即开即用，随用随走。

## 技术栈

| 层 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Nuxt 3 (SPA) | 3.15.4 (锁死) |
| UI 库 | Nuxt UI v2 | ^2.21 |
| CSS | Tailwind CSS v3 | tailwind.config.ts |
| i18n | @nuxtjs/i18n v9 | zh-CN / en |
| 后端框架 | Flask | ^3.1 |
| 参数校验 | Pydantic v2 | ^2.13 |
| 异步任务 | Celery | ^5.6 (dev: memory://) |
| 数据库 | SQLite (WAL) | tasks.db |
| 部署 | Docker Compose | 3 容器 |

## 项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂 (<70 行，仅蓝图注册 + SPA fallback)
│   ├── config.py               # 集中配置
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult[T] + ServiceError
│   ├── schemas.py              # Pydantic v2 请求 DTO
│   ├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
│   ├── json_logging.py         # JSON 结构化日志 (30 天轮转)
│   ├── models.py               # TaskRecord + OperationLog + BaseCRUD (原始 SQL)
│   ├── cache.py                # Flask-Caching SimpleCache
│   ├── celery_app.py           # Celery (3 队列: convert/pdf/office)
│   ├── gunicorn.conf.py        # 生产: bind 0.0.0.0:5000, workers=2
│   ├── blueprints/             # HTTP 路由层 (每功能一个文件)
│   ├── services/               # 业务逻辑层 (纯函数，零 Flask 依赖，返回 ServiceResult[T])
│   ├── tasks/                  # Celery 异步任务
│   └── utils/                  # 通用工具 (file_security / rate_limit / retry / crypto)
├── frontend/
│   ├── nuxt.config.ts          # SSG + i18n + Nuxt UI v2
│   ├── tailwind.config.ts      # Tailwind v3 品牌色阶
│   ├── assets/css/main.css     # CSS 变量 (SynTime Royal Blue token)
│   ├── composables/            # tools.config / useValidation / useTaskStream / useApi / useDownload / useAi
│   ├── components/             # 业务组件 + ui/ 原子组件
│   ├── layouts/default.vue     # 侧边导航壳
│   ├── pages/                  # 路由页面
│   └── locales/                # zh-CN / en
├── docs/
│   └── vibecoding-blog.md      # 开发经验分享
├── manage.sh                   # dev/docker 管理
├── Dockerfile
├── SPEC.md                     # 详细设计规范
└── AGENTS.md                   # 本文件
```

## 功能模块

| # | 模块 | 路由 | 说明 |
|---|------|------|------|
| 1 | 仪表盘 | `/` | 工具卡片网格 |
| 2 | MD 转公文 | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX + AI 纠错 |
| 3 | 文档转 MD | `/doc-to-md` | PDF/Word/PPT/图片 → Markdown (MinerU) |
| 4 | 格式规范 | `/format-docx` | GB/T 9704-2012 格式化 |
| 5 | 视频转换 | `/video-convert` | MP4 → WMV (PPT 嵌入) |
| 6 | RSS 探测 | `/rss-detect` | 输入 URL，自动发现 RSS/Atom 订阅 |
| 7 | 属性修改 | `/properties` | 元数据修改 + 清理 (双 Tab) |
| 8 | Excel 合并 | `/excel-merge` | .xlsx/.csv 同结构合并 |
| 9 | 文件组装 | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 10 | 打印分组 | `/print-split` | 批次拆分 PDF |
| 11 | PDF 编辑 | `/pdf-editor` | 删除/插入/重排页面 |
| 12 | 调整 PDF | `/pdf-tools` | PDF 转文本 + 压缩 + 页码页眉页脚 |
| 13 | PDF 合并 | `/pdf-merge` | 多 PDF 合并，拖拽排序 |
| 14 | 使用统计 | `/status` | 模块调用量 + 访客统计 (ECharts) |

## 开发环境

```bash
# 开发模式 (Flask :5000 + Nuxt :8080)
./manage.sh start

# Docker 部署 (3 容器)
./manage.sh docker-up

# 停止
./manage.sh stop
./manage.sh docker-down

# 测试
./manage.sh test
```

## 核心规范

### 后端分层

| 层 | 职责 | 约束 |
|----|------|------|
| Blueprint | HTTP 请求/响应 | ≤ 20 行，只做参数提取 → 调 service → 返回响应 |
| Service | 业务逻辑 | 零 Flask 依赖，全部返回 `ServiceResult[T]` |
| Utils | 通用工具 | 可被任意层引用 |
| Tasks | Celery 异步任务 | 更新 TaskRecord 进度 + SSE 推送 |

### Service 层

所有 Service 函数必须返回 `ServiceResult[T]`：

```python
from errors import ServiceResult, ErrorCode

def my_service(path: str) -> ServiceResult[dict]:
    try:
        data = do_work(path)
        return ServiceResult.ok(data)
    except ValueError as e:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, str(e))
```

需要中断调用栈时抛 `ServiceError(code, msg, status)`，全局 handler 自动转为标准化 JSON `{code, msg, requestId}`。

### API 层

- `@validate_request(body=Schema)` 把 Pydantic 对象作为 `body=` 关键字传入函数
- 全局异常拦截器自动处理所有异常
- 每个请求自动分配 `requestId`（12 位 hex），通过 `X-Request-Id` 响应头返回

### 前端规范

- UI 组件：Nuxt UI v2 (`UFormGroup`, `UButton`, `UInput`, `USelect`, `UTabs`)
- 图标：Heroicons (`i-heroicons-*`)，本地模式，禁止 emoji
- 所有 UI 文本用 `$t()`，禁止硬编码
- 颜色通过 CSS 变量或 Tailwind token，禁止 inline hex
- 禁止 `transition: all`，用具体属性列表
- 表单校验：Vuelidate (`useValidation` composable)
- 异步进度：SSE (`useTaskStream` composable)
- API 错误提取：统一使用 `extractError(e)` (`composables/useError.ts`)

### 工具配置单一数据源

`composables/tools.config.ts` 是所有工具定义的唯一来源。Sidebar 和 Dashboard 从此读取，新增工具只改这一个文件。

## 设计 Token (SynTime Royal Blue)

### 品牌色阶

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-500` | `#4C7DF0` | 品牌主色 |
| `--color-brand-600` | `#3B63D8` | 悬停/强调 |
| `--color-brand-700` | `#2F4FB0` | 深色文本/渐变终点 |
| `--color-brand-soft` | `rgba(76,125,240,0.10)` | 柔和底色 |

### 表面色

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-page` | `#EEF0F4` | 页面底色 (navy-gray) |
| `--color-surface` | `#ffffff` | 卡片白色 |
| `--color-muted` | `#F4F6FA` | 次级区域 |

### 文本色

| Token | 值 | 对比度 |
|-------|-----|--------|
| `--color-text-primary` | `#1F2A44` | ~12:1 |
| `--color-text-secondary` | `#56627A` | ~5.5:1 |
| `--color-text-tertiary` | `#6E7A93` | ~4.5:1 (WCAG AA) |

### 边框与阴影

| Token | 值 |
|-------|-----|
| `--color-border-default` | `#E3E8F0` |
| `--shadow-card` | `0 2px 6px rgba(26,43,79,0.05)` |
| `--shadow-elevated` | `0 6px 14px -2px rgba(26,43,79,0.07)` |

### 侧边栏

深色极光渐变面板，宽度 256px (展开) / 72px (收起)，移动端悬浮叠加模式。

```css
background: linear-gradient(168deg, #2A2166 0%, #23337A 30%, #1E4E7E 55%, #17646B 80%, #4A3D20 100%);
```

### 品牌点缀

印章红 `--color-seal-red: #C0392B`，用于侧边栏 Logo "印" 字。

## 命名规范

| 层级 | 规范 | 示例 |
|------|------|------|
| 后端 Blueprint | `<feature>_bp.py` | `convert.py`, `watermark_bp.py` |
| 后端 Service | 单数名词 | `converter.py`, `watermark.py` |
| 前端组件 | PascalCase | `ToolCard.vue`, `Sidebar.vue` |
| 前端 composables | `useXxx.ts` | `useValidation.ts` |
| 前端 pages | kebab-case | `md-to-docx.vue` |

## 关键约定

### 后端

- 第三方包函数内延迟导入（裸机部署兼容）
- 环境变量从 `Config` 类读，不模块级 `os.environ`
- 中文 prompt 用单引号字符串（避免中文引号冲突）
- Celery broker 生产默认 Redis，不用 `memory://`

### 前端

- `tools.config.ts` 单一数据源，新增工具只改这一个文件
- Sidebar 子菜单同时支持 hover + click（触摸设备兼容）
- `prefers-reduced-motion: reduce` 全局禁用动画
- 触摸目标 ≥ 44px (`min-h-[44px]`)

### Docker

- 一镜像多容器，`command:` 区分角色
- `.env` 不进镜像，通过 compose `${VAR}` 注入
- HEALTHCHECK 在 compose 中按 service 单独定义
- npm ci 需要 lockfile 同步

## 统计持久化

统计数据存储在 `backend/tasks.db` (SQLite)，独立于代码文件。`init_db()` 使用 `CREATE TABLE IF NOT EXISTS`（幂等），无重置逻辑。`.gitignore` 已排除 `backend/tasks.db*`。代码更新不影响历史数据。

## 详细文档

- `SPEC.md` — 完整设计规范、API 端点全集、版本历史
- `docs/vibecoding-blog.md` — 开发经验分享博客
