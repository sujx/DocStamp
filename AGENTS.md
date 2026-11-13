# AGENTS.md — 鹊随金印 (docStamp) 项目规范

## 项目概述

鹊随金印是一站式文档处理工具箱。Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 前端，Flask REST API 后端。SynTime Royal Blue 品牌色系，仪表盘 + 侧边导航 + 多页面路由，中英文双语。

**定位**：单体工具，无用户系统，无认证——即开即用，随用随走。

## 技术栈

| 层 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Nuxt 3 (SPA) | 3.15.4 (锁死) |
| UI 库 | Nuxt UI v2 | ^2.21 |
| CSS | Tailwind CSS v3 | tailwind.config.ts |
| i18n | @nuxtjs/i18n v9 | zh-CN / en |
| 后端运行时 | Python | 3.13 |
| 后端依赖管理 | uv (`pyproject.toml` + `uv.lock`) | lock revision 5 |
| 后端框架 | Flask | ^3.1 |
| 参数校验 | Pydantic v2 | ^2.13 |
| 异步任务 | 无独立 worker；每日临时文件清理由 gunicorn `on_starting` 启动的守护线程负责 | backend/utils/file_cleanup.py |
| 数据库 | SQLite (WAL) | tasks.db |
| 部署 | Docker Compose | 单容器 |

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
│   ├── models.py               # OperationLog + BaseCRUD (原始 SQL)
│   ├── cache.py                # Flask-Caching SimpleCache
│   ├── babel.cfg               # pybabel 提取配置
│   ├── fill_zh_po.py         # 中文消息表 → translations/zh_Hans_CN/…/messages.po
│   ├── translations/           # messages.pot + zh_Hans_CN/LC_MESSAGES/messages.{po,mo}
│   ├── gunicorn.conf.py        # 生产: bind 0.0.0.0:5000, workers=2, on_starting 启动每日清理
│   ├── pyproject.toml          # 后端依赖唯一声明处 (uv, requires-python >=3.13)
│   ├── uv.lock                 # 锁文件，与 pyproject.toml 一起提交；镜像构建按它 --frozen 安装
│   ├── blueprints/             # HTTP 路由层 (每功能一个文件)
│   ├── services/               # 业务逻辑层 (纯函数，零 Flask 依赖，返回 ServiceResult[T])
│   └── utils/                  # 通用工具 (file_security / file_cleanup / rate_limit / retry / crypto)
├── frontend/
│   ├── nuxt.config.ts          # SSG + i18n + Nuxt UI v2
│   ├── tailwind.config.ts      # Tailwind v3 品牌色阶
│   ├── assets/css/main.css     # CSS 变量 (SynTime Royal Blue token)
│   ├── composables/            # tools.config / useValidation / useApi / useDownload / useApiError / useSidebar / usePageView / usePdfRedactMarks
│   ├── components/             # 业务组件 + ui/ 原子组件
│   ├── components/landing/     # 宣传页区块 (LandingNav / LetterheadHero / ToolShowcase / PromiseBand / LandingFooter / SectionKicker)
│   ├── layouts/default.vue     # 侧边导航壳 (应用内: /tools + 14 个工具页)
│   ├── layouts/landing.vue     # 宣传页壳: sticky 顶栏 + 页脚 + UNotifications, 无侧栏
│   ├── pages/                  # 路由页面 (index.vue = 宣传页, tools.vue = 仪表盘)
│   ├── server/routes/          # Nitro 端点: sitemap.xml.ts (URL 来自 TOOLS, 不用 pages/)
│   └── i18n/locales/           # zh-CN / en
├── docs/
│   └── vibecoding-blog.md      # 开发经验分享
├── manage.sh                   # dev/docker 管理
├── sync-from-windows.sh        # Windows 编辑 → WSL 构建：拷文件并转 LF
├── Dockerfile
├── SPEC.md                     # 详细设计规范
└── AGENTS.md                   # 本文件
```

## 功能模块

功能模块 14 个（13 项工具 + 使用统计）；下表 16 行含宣传页与仪表盘两个导航页，二者都不计入。

| # | 模块 | 路由 | 说明 |
|---|------|------|------|
| 1 | 宣传页 | `/` | 对外首页：红头 hero + 14 件工具 + 隐私承诺 + 资源区 |
| 1b | 仪表盘 | `/tools` | 工具卡片网格（应用内首页，有侧栏） |
| 2 | MD 转公文 | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX |
| 3 | 格式规范 | `/format-docx` | GB/T 9704-2012 格式化 |
| 4 | RSS 探测 | `/rss-detect` | 输入 URL，自动发现 RSS/Atom 订阅 |
| 5 | 属性修改 | `/properties` | 元数据修改 + 清理 (双 Tab) |
| 6 | Excel 合并 | `/excel-merge` | .xlsx/.csv 同结构合并 |
| 7 | 文件组装 | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 8 | 打印分组 | `/print-split` | 批次拆分 PDF |
| 9 | PDF 编辑 | `/pdf-editor` | 删除/插入/重排页面 |
| 10 | 调整 PDF | `/pdf-tools` | PDF 转文本 + 压缩 + 页码页眉页脚 |
| 11 | PDF 合并 | `/pdf-merge` | 多 PDF 合并，拖拽排序 |
| 12 | PDF 脱敏 | `/pdf-redact` | 框选/关键词标记敏感区，生成带马赛克的新 PDF |
| 13 | WebP 转 JPEG | `/webp-to-jpeg` | WebP → JPEG，透明填白底，动图取首帧 |
| 14 | 密码生成 | `/password-gen` | 随机密码 + 可复现密码（纯前端，零数据留存） |
| 15 | 使用统计 | `/status` | 模块调用量 + 访客统计 (ECharts) |

## 开发环境

代码在 **Windows 侧编辑**（`D:\Workdir\DocStamp`，`core.autocrlf=true` 工作树是 CRLF），在 **WSL（AlmaLinux-10）** 里构建与测试（仓库位于 `/root/Project/DocStamp`）。两边靠 `sync-from-windows.sh` 打通：它默认覆盖**全仓库被跟踪的文件**（`git ls-files -s`，可传 pathspec 缩小范围），逐文件转 LF（直接 `cp` 会把 CRLF 带进去，git 会显示整文件重写），并按 index 记录的 mode 落权限（`/mnt/d` 一律报 0777；凭猜测 `chmod` 要么把 644 的文件抬成 mode change，要么把 `manage.sh` 这类 755 的压回去，两种都会让 clone 常年显脏）。**只同步跟踪文件是硬约束**：`backend/tasks.db*`、`backend/output/` 这类 gitignored 运行时状态在 Windows 侧是旧快照，早前按目录 `cp -r` 时就把 WSL 的统计库覆盖成 9-28 的副本（靠未 checkpoint 的 WAL 才找回），所以未跟踪文件一律不过去：

```bash
bash /root/sync-from-windows.sh              # 默认同步全仓库跟踪文件（含仓库根的 AGENTS.md / Dockerfile 等）
bash /root/sync-from-windows.sh frontend     # 只传某个 pathspec 时缩小范围
```

后端依赖由 **uv** 管理：`backend/pyproject.toml` 是唯一声明处，`backend/uv.lock` 锁死版本，环境建在 `backend/.venv`。入口一律走 `uv run`（`manage.sh` 已改），**「每个新会话先激活 venv」这一步已经作废**——`uv run` 会按锁文件自动对齐环境：

```bash
cd backend && uv sync                 # 首次 clone 或改依赖后；默认就装 dev 组
uv run pytest tests/ -v               # 等价于 ../manage.sh test
uv run mypy --strict <文件或包>       # 别用 /usr/bin/mypy：它走系统解释器的 site-packages，看不见 .venv
```

加依赖用 `uv add <pkg>` / `uv add --dev <pkg>`，`pyproject.toml` 和 `uv.lock` 一起提交。镜像构建走 `uv sync --frozen --no-dev`，dev 组不进镜像。国内网络下 `pypi.org` 只有几百 kB/s，需要镜像时临时加 `UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`——只在环境变量里换，写进 `pyproject.toml` 会把 `uv.lock` 的 registry 全部改写到国内源。

**WSL 已知环境差异**：AlmaLinux 无 `/etc/mime.types`，`mimetypes.guess_type("x.docx")` 返回 `None`，故 `tests/test_routes_critical.py::test_download_reports_binary_mimetype` 在 WSL 必失败（生产 Debian 镜像有该表，非代码缺陷）；其余 199 条用例为准。

```bash
# 开发模式 (Flask :5000 + Nuxt :8080)
./manage.sh start

# Docker 部署 (单容器)
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
- API 错误提示：`useApiError().showError(e)` 弹 toast；需要内联展示时用 `useApiError().extractError(e)` 取消息（自动识别 JSON 与 Blob 两种错误体）；全局 401 由 `plugins/axios.client.ts` 拦截
- Toast：`useToast().add({...})` 只往 `useState("notifications")` 里塞数据，**页面上必须有 `<UNotifications />` 容器才会渲染**——容器挂在 `layouts/default.vue` 与 `layouts/landing.vue`，新增独立 layout 时要一起带上，否则该页所有 toast 静默失效（v2 无自动注入，实测删掉容器后 `toast.add` 调用成功但 DOM 零节点）
- 文件下载：统一走 `useDownload().downloadBlob(blob, filename, successMsg?)`（挂 `<a>` → click → 延迟 100ms 摘除并 revoke，禁止在组件里手写这段；不传成功文案则不弹 toast）
- `/` 是宣传页（`layouts/landing.vue`，无侧栏），`/tools` 是仪表盘（`layouts/default.vue`，有侧栏）。任何 `TOOLS` 条目都不得把 `to` 指向 `/`（顶栏品牌链接 `to="/"` 是唯一例外），由 `composables/__tests__/tools.config.spec.ts` 钉住。新 layout 必须同时挂 `<UNotifications />` 与 `LanguageSwitcher`。

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

深色极光渐变面板，宽度 256px (展开) / 72px (收起)，移动端悬浮叠加模式。导航为一级扁平列表，无分组子菜单。

```css
background: linear-gradient(168deg, #2A2166 0%, #23337A 30%, #1E4E7E 55%, #17646B 80%, #4A3D20 100%);
```

### 品牌点缀

印章红 `--color-seal-red: #C0392B`，用于侧边栏 Logo "印" 字。

## 命名规范

| 层级 | 规范 | 示例 |
|------|------|------|
| 后端 Blueprint | `<feature>_bp.py` | `pdf_merge_bp.py`, `excel_merge_bp.py` |
| 后端 Service | 单数名词 | `converter.py`, `pdf_merger.py` |
| 前端组件 | PascalCase | `ToolCard.vue`, `Sidebar.vue` |
| 前端 composables | `useXxx.ts` | `useValidation.ts` |
| 前端 pages | kebab-case | `md-to-docx.vue` |

## 关键约定

### 后端

- 第三方包函数内延迟导入（裸机部署兼容）
- 环境变量从 `Config` 类读，不模块级 `os.environ`
- 中文 prompt 用单引号字符串（避免中文引号冲突）
- 每日临时文件清理：gunicorn `on_starting` 在 master 进程调 `utils/file_cleanup.start_cleanup_daemon`，无独立 worker
- 错误消息在**源头**翻译：服务层 / 工具层用 `lazy_gettext as _l` + `%(...)s` 命名插值，蓝图静态文案用 `gettext as _`，蓝图出口仍是 `str(e)` / `result.message`；新增用户可见消息必须走 msgid，不许拼 f-string 直出。目录名固定 `translations/zh_Hans_CN/`（`zh_CN` 会静默失配），提取要显式 `-k _l:1`。完整约定见 `SPEC.md`「四、后端架构 · 错误消息国际化」

### 前端

- `tools.config.ts` 单一数据源，新增工具只改这一个文件
- 侧栏是一级扁平导航（`SIDEBAR_ITEMS`），不设分组子菜单
- `prefers-reduced-motion: reduce` 全局禁用动画
- 触摸目标 ≥ 44px (`min-h-[44px]`)

### Docker

- 单容器（gunicorn API），不再有 worker 容器
- `.env` 不进镜像，通过 compose `${VAR}` 注入
- HEALTHCHECK 在 compose 中定义（打 `/api/v1/health`）
- npm ci 需要 lockfile 同步
- Python 依赖在 Stage 2 由 `uv sync --frozen --no-dev` 按 `backend/uv.lock` 解析，Stage 3 只拷成品 venv（两个 Stage 的 `python:3.13-slim-bookworm` 必须同版本，venv 里的解释器是软链）。`Dockerfile` 里不再有 pip 包清单，加依赖只改 `pyproject.toml` + `uv.lock`；`.dockerignore` 的 venv 规则是 `**/.venv/`——dockerignore 锚定构建上下文根，裸写 `.venv/` 挡不住 `backend/.venv`

## 统计持久化

统计数据存储在 `backend/tasks.db` (SQLite)，独立于代码文件。`init_db()` 使用 `CREATE TABLE IF NOT EXISTS`（幂等），无重置逻辑。`.gitignore` 已排除 `backend/tasks.db*`。代码更新不影响历史数据。

## 待办与已知遗留项

只收录**已知但刻意未做**的事项，每条注明「为什么没做」——避免下一轮把同一件事重新调研一遍。已完成的变更不在这里，见 `SPEC.md` 版本历史。条目勾掉时，把它的背景一并删掉。

### Docker / 部署

| 事项 | 为何未做 |
|------|----------|
| 服务器切到单容器新镜像 | 已定「服务器上先不动，后期更新 docker 镜像来解决」。本机镜像已验收（健康检查 200、SPA 217KB、`X-API-Version: 3.7`、pandoc 2.17.1.1 / pdftoppm 22.12.0、`.cleanup-stamp` 与 tasks.db(WAL) 正常落盘），但生产切换未经实证。v3.11.0（Python 3.13 + uv）本机重跑过同一串：health 200 + `X-API-Version: 3.11.0`、SPA 239KB、`gunicorn` 从 `/opt/docstamp/.venv/bin` 解析、镜像内无 `uv`、4 worker 日志正常落盘；同样只是本机证据，生产切换仍未实证 |
| 服务器运维 `.env` 删掉 AI / DeepSeek 残留行 | 仓库与开发机均无 `.env`（gitignored）；compose 已不再注入该变量，这行现在是惰性的，但 key 已吊销 |
| `Dockerfile` 的 `CMD` 补 `--workers` | compose 传了 `--workers 2`，裸 `docker run` 会落到 `gunicorn.conf.py` 的 `min(8, cpu*2+1)`（2 核 = 5 个 worker）。生产走 compose 故被兜住 |
| 删掉 `backend/gunicorn.conf.py` 的 `pidfile` | `"/var/run/docstamp.pid"` 恒被 `Dockerfile` 与 compose 的 `--pid /tmp/gunicorn.pid` 覆盖，且 `docstamp` 用户对 `/var/run` 无写权，属死配置 |
| `.dockerignore` / `.gitattributes` 钉 `eol=lf` | 现状只让 `git add` 警告「下次 touch 转 CRLF」；实测无碍（Go 行扫描剥 `\r`，git 属性解析也容忍 `\r`），故按「先证明再修」留着。v3.9.3 起 `backend/translations/*.po`/`.pot` 也进了仓库，每次 Windows 检出都是 CRLF，构建在 WSL clone（LF）里跑故未受影响 |

### 整站级

| 事项 | 为何未做 |
|------|----------|
| 开发模式没有清理线程 | 每日清理只挂在 gunicorn `on_starting`，`uv run python app.py` 不起它，dev 机器只能 `./manage.sh clean-output` 手动清 |
| 后端 `mypy --strict` 不是门槛 | v3.11.0 迁 uv 时实测：`uv run mypy --ignore-missing-imports --strict --explicit-package-bases $(git ls-files '*.py')` 报 **319 errors / 43 files**，全是存量（118 条 `no-untyped-def` + 63 条 `type-arg` + 55 条 `arg-type`）。`pyproject.toml` 写着 `strict = true`、`backend/.pre-commit-config.yaml` 也挂了 mypy，但 `.git/hooks/pre-commit` 不存在，所以这道门槛从未跑过。要修属一整批，不在依赖迁移里顺带动 |

### 宣传页 / 隐私文案

宣传页上的每条隐私承诺都按代码真相写（真相表见 `SPEC.md`「十一、宣传页首页」）。下表是「文案今天为真、但要做到更强的说法还得改存储或日志」的工程项——做完一条，文案才能升一级。

| 事项 | 为何未做 |
|------|----------|
| 产物目录改 tmpfs（或给 upload 挂 tmpfs） | `output_data` 是具名卷，落在物理盘（`docker-compose.yml:26`）；做不到就不能写「磁盘零写入」 |
| 硬 TTL 一小时 + 真定时扫描 | 通用临时文件是每日扫描、7 天上限（`backend/utils/file_cleanup.py:19-21`）；1 小时 TTL 只覆盖脱敏会话且惰性触发（`backend/utils/redact_session.py:24`） |
| 上传落盘不带原名 | 存盘名 `uuid_<安全化原名>`（`backend/utils/base/file_helpers.py:62-63`） |
| 三件两段式工具也做到取走即删 | MD转公文 / 格式规范 / 打印分组都是「生成 → 下载」：`backend/blueprints/convert.py:141-147,182-188` 与 `print_split_bp.py:48-56,66-78` 成功后只回 id，`download.py:75` 无删除钩子 |
| 运维日志不再带文件路径 | `backend/utils/file_cleanup.py:88` 清理失败时把临时文件全路径写进日志，`error_handler.py:94` + `json_logging.py:47-48` 还带堆栈，保留 30 天（`json_logging.py:21`）。做到才能把承诺带 item3 从「统计库里没有文件名」升回「日志里没有文件名」 |
| 脱敏会话目录纳入真定时清扫 | `cleanup_expired` 全仓库唯一调用点是下一次 `/open`（`backend/blueprints/pdf_redact_bp.py:67`），惰性触发；且 7 天清扫只按顶层条目 mtime 判龄（`backend/utils/file_cleanup.py:73-84`），`redact-sessions` 父目录 mtime 每次建/删会话都刷新 → 7 天内有人用过就整棵树跳过，废弃会话可能长期留存。做到才能对脱敏写「最长留 N」 |
| PDF 编辑的 `thumbs_*` 页面图片有人删 | `backend/blueprints/pdf_editor_bp.py:86-87,92-107` 渲染最多 50 张页面 PNG，`:125-126` 的 `finally` 只删上传件；全仓库无任何删除点，页面图片留到 7 天清扫。做到才能把它并进「响应结束即删」 |
| `operation_logs.file_size` 接上真实体积或删列 | 列存在但无任何调用方传值（`backend/models.py:135` 默认 0，`app.py:111-125` 与 `blueprints/stats_bp.py:37-48` 都不传），每行恒为 0；承诺带 item3 的「体积」因此被去掉 |
| 日志不再存 IP + UA（若决定匿名化） | `/status` 独立访客去重靠这两列（`backend/app.py:118-122`、`backend/models.py:52-65`），动了是功能减级 |
| 其余教程与政策/条款页 | 已落地一篇 `/guide/pdf-redact`（宣传页资源区、页脚、脱敏页、sitemap 均已接入）；其余教程及隐私政策/服务条款/更新日志仍无页面，原型里全是 `href="#"` 占位。每篇都要先把文案对代码核实，故不一次铺开 |
| 删掉 4 个零入链的孤儿路由页 | `frontend/pages/{metadata-clean,page-decorate,pdf-compress,pdf-to-text}.vue`；删页面属改仓库内容，需单独确认 |
| `manage.sh clean-output` 清不掉目录 | `manage.sh:251` 用 `rm -f` + glob：退出码 1、目录残留、跳过点文件。生产清理走 `backend/utils/file_cleanup.py` 是对的，只有 dev 手动清理受影响；建议改为调用 Python 清理入口 |
| `LanguageSwitcher` 28px 触摸目标 | 共享组件 scoped CSS 写死 `height: 28px`，本批只在 `LandingNav` 用 `:deep()` 局部提到 44px；根治要改共享组件，影响侧栏，属独立一批 |

### 前端组件

| 事项 | 为何未做 |
|------|----------|
| 全站 `color="neutral"` 无效 + `neutral-*` 类名惰性 | Nuxt UI v2 的灰阶值拼法是 `gray`（`neutral` 是 v3 拼法），故 `color="neutral"` 触发 `[Vue warn] Invalid prop`，组件退回默认灰阶；又因 `neutral` 是 Tailwind 内置色而未被 `safelistColors` 收录，`text-neutral-500` 一类 `neutral-*` 类名不在产物 CSS 里（实测该元素 `color` 为空、随父级）。存量问题、非本批引入，属独立一批 |
| Toast 的 `color: "warning"/"success"/"error"` 全部无效（20 处） | `UNotification` 的 `color` 校验是 `["gray", ...appConfig.ui.colors]`，本项目 `appConfig.ui.colors` 只有 Tailwind 色板名 + `brand`/`primary`，**没有** `warning`/`success`/`error` 这类语义名；实测控制台 `[Vue warn]: Invalid prop ... at <Notification>`，且渲染出的进度条类名 `bg-warning-500` 在产物 CSS 里不存在（`bg-warning-500` 计算样式 = `rgba(0,0,0,0)`），只有白卡生效。以前 toast 根本不挂载（缺 `<UNotifications />`），所以这条一直没人看见；v3.9.3 挂上容器后暴露。修法属一批：语义色要么进 `tailwind.config.ts` 色板 + `safelistColors`，要么 20 处改成 `amber`/`green`/`red` |
| primary solid 按钮白字对比度 3.82:1，不过 AA | Nuxt UI v2 的 default solid 是 `text-white bg-{color}-500`（`node_modules/@nuxt/ui/dist/runtime/ui.config/elements/button.js:56,76-77`），本项目 `app.config.ts` 把 `ui.primary = "brand"`，故全站约 45 个 primary 按钮都是白字 on `#4C7DF0`。修法二选一：solid 变体改 `bg-brand-600`（5.3:1）或整体调 primary 色阶；只改宣传页两个 CTA 会与站内不一致，属设计 token 批次 |
| 14 个工具页 `<title>` 仍是空 `%s`（`- 鹊随金印`） | 本批只修 `/` 与新建的 `/tools`；统一补需给 `ToolDef` 加 `titleKey` 并接 `useHead`，属 14 页批量 TDK 批次 |
| 宣传页工具组标签 `text-tertiary` 12px 对比度 ≈3.77:1，低于 AA | 与 R30 同属设计 token 批次；可改 `text-secondary` 或调深三级文本色 |
| `SITE_ORIGIN` 与 `pages/index.vue` 的 og 绝对地址是两处字面量 | 改需 runtimeConfig 或构建期常量；今天域名无分歧，暂不动 |
| sitemap 16 条 URL 共用同一个 UTC `lastmod` | 静态页每日都自称更新，属低信号；逐页 mtime 需构建期 plumbing |

### PDF 脱敏模块

| 事项 | 为何未做 |
|------|----------|
| 会话目录在 Windows 上删不掉 | 下载后的清理靠 POSIX unlink「删已打开的文件」语义；Windows 上 `send_file` 仍持有句柄，`shutil.rmtree(ignore_errors=True)` 静默失败，会话要等 1 小时 TTL 才消失。生产是 Linux 容器，故不改；「下载即删」只在容器里被实证 |
| `/apply` 不限制单次 marks 数量 | `rate_limit` 限的是请求数（20/分钟），不限一次提交多少框；每个框都要渲染一张 200 DPI 位图，理论上可被单请求拖垮。关键词侧已有 `MAX_MATCHES=500` 挡住批量场景，内网 12 人规模下按「先证明再修」留着 |
| 本机 `nuxt generate` 预渲染必失败 | Windows + Node 24 下 `@nuxt/icon` 生成的 `createRequire(globalThis._importMeta_.url)` 收到 `file:///_entry.js`，Node 拒收空 host 的 file URL 并抛错，`.output/public` 空产出。已用 HEAD 版 `nuxt.config.ts` 复现，且失败点在「Initializing prerenderer」——模块加载期，早于任何页面预渲染，与本模块改动无关；推测是本机 Node 由 24.18 升到 24.19 后收紧校验（v3.8 那批 `nuxt generate` 还是通的）。真实构建路径是 `Dockerfile` stage 1 的 node:22-alpine，镜像已验证，故不动 |
| 马赛克对图片只是视觉覆盖，原图仍可提取 | `backend/services/pdf_redact.py:349-358` 用 `apply_redactions(images=PDF_REDACT_IMAGE_NONE)` 保留整页图片、再 `insert_image(overlay=True)` 把像素化位图盖上去；`_leftovers`（`:390-408`）只复检文字层。`SPEC.md:582`（v3.9 条目）已记实现机制，但用户可见的局限没进待办。不改后端行为，属文案/产品决策 |

### 测试与数据

- **`backend/tasks.db.bak-20260923`（含 `-shm` / `-wal`）留在磁盘** —— 索引修复前的安全网，已确认 `integrity_check` ok，可择日删除。
- **Windows 侧 `backend/tasks.db` 是 2026-09-28 的死快照** —— 统计数据以 WSL clone 那份为准（生产在服务器卷里，另有副本）。2026-09-30 因 `sync-from-windows.sh` 按目录 `cp -r` 把它覆盖进 WSL，主库瞬间退回 9-28；WAL 未 checkpoint 才把 9-29 的行找回来（已手动 `wal_checkpoint(TRUNCATE)` 合并，`operation_logs` 2919 行、`integrity_check` ok）。修复前的主库副本另存在 `/tmp/nodelete-tasksdb-Sep28snapshot.db`（WSL 重启即消失）。同步脚本已改为只按 `git ls-files` 拷贝，未跟踪运行时状态不再跨界。
- **`backend/tests/__pycache__/` 残留 5 个已删模块的 `.pyc`**（`company_lookup` / `task_tracking` / `video_converter` / `watermark` / `worker`）—— 纯本机杂物，`.dockerignore` 已挡住不进镜像，可直接删该目录。

### 其他

| 事项 | 为何未做 |
|------|----------|
| Gitee 上的旧仓库未删除 | 已弃用 Gitee，GitHub（public）为唯一远端；要清理需自行去 Gitee 删 |
| `backend/.nuxt/` 31 个构建产物自 `07c348e`（first commit）就被跟踪 | `.gitignore` 第 35 行有 `.nuxt/`，但取消跟踪要 `git rm -r --cached`，属改仓库内容，未经确认不动。现状后果：WSL 里跑过 dev 构建后这些文件被重新生成，clone 的 `git status` 常年脏（489 KB 死产物）；`.dockerignore` 第 28 行已挡住，镜像不受影响 |
| `edffc8c` 的 commit message 含已吊销的 DeepSeek key | 无可达 blob（不在任何文件内容里），已披露，**刻意不改写历史** |
| `docs/` 被整目录 gitignore，但 `docs/vibecoding-blog.md` 已跟踪 | 新加到 `docs/` 的文件不会进仓库（`docs/plans/` 即未跟踪）。有意为之可忽略，否则需调 `.gitignore` 或用 `git add -f` |

### 刻意不动的历史产物（别再当「过期」去改）

- `docs/vibecoding-blog.md` —— 2026-06-19 已发布文章原文，模块数 / 页面数等计数已过期，但改它就是错的。
- `SPEC.md` 版本历史 —— `v3.7.6` 记删 AI、`v3.6` 起提到 Celery / SSE / worker / `useError.ts` 的条目是当时的发布记录，不随现状删改。

## 详细文档

- `SPEC.md` — 完整设计规范、API 端点全集、版本历史
- `docs/vibecoding-blog.md` — 开发经验分享博客
