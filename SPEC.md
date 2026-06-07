# docStamp — 设计规范与开发指南

## 一、项目概述

docStamp 是一站式文档处理工具箱。Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 前端，Flask REST API 后端。绿鹃品牌色系（`#008A3D` + `#F9F7E8`），仪表盘 + 侧边导航 + 多页面路由。

**定位**：单体工具，无用户系统，无认证，无 AI — 即开即用，随用随走。

**i18n**：中英文双语，`locales/zh-CN.json` + `locales/en.json`，默认 `zh-CN`。

---

## 二、功能模块（15 个，归为 4 组）

**侧栏导航**：

```
MD 转公文        → /md-to-docx
水印管理          → /watermark       (添加/去除)
Office 工具 ▸     → /properties  /excel-merge  /format-docx  /format-convert  /metadata-clean
PDF 工具 ▸        → /file-assembly  /print-split  /pdf-editor  /pdf-to-text  /pdf-merge  /pdf-compress  /page-decorate  /image-process
```

| # | 模块 | 路由 | 分组 | 说明 |
|---|------|------|------|------|
| 1 | MD 转公文 | `/md-to-docx` | — | Markdown → GB/T 9704-2012 DOCX，实时预览 |
| 2 | 水印管理 | `/watermark` | — | 添加/去除文字和图片水印 |
| 3 | 属性修改 | `/properties` | Office | .docx/.xlsx/.pptx 元数据修改 |
| 4 | Excel 合并 | `/excel-merge` | Office | .xlsx/.csv 结构相同合并 |
| 5 | 格式规范 | `/format-docx` | Office | GB/T 9704-2012 格式化 |
| 6 | 格式互转 | `/format-convert` | Office | DOCX/HTML → PDF |
| 7 | 元数据清理 | `/metadata-clean` | Office | 清除文档元数据，保护隐私 |
| 8 | 文件组装 | `/file-assembly` | PDF | 图片合并 + PDF 拆解 |
| 9 | 打印分组 | `/print-split` | PDF | 批次拆分、暂停/继续/终止 |
| 10 | PDF 编辑 | `/pdf-editor` | PDF | 删除/插入/重排页面 |
| 11 | PDF 转文本 | `/pdf-to-text` | PDF | 提取 PDF 文本内容 |
| 12 | PDF 合并 | `/pdf-merge` | PDF | 多 PDF 合并，拖拽排序 |
| 13 | PDF 压缩 | `/pdf-compress` | PDF | 三级压缩（轻度/中度/深度） |
| 14 | 页码页眉页脚 | `/page-decorate` | PDF | 添加页码/页眉/页脚 |
| 15 | 图片处理 | `/image-process` | PDF | 缩放/裁剪/格式转换/压缩 |

---

## 三、设计系统

### 配色 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-700` | `#008a3d` | 品牌主色 |
| `--color-brand-800` | `#00662b` | 悬停加深 |
| `--color-brand-soft` | `rgba(0,138,61,0.08)` | 柔和底色 |
| `--color-page` | `#f9f7e8` | 米黄页面底 |
| `--color-surface` | `#ffffff` | 卡片/面板白 |
| `--color-muted` | `#f4f2e4` | 次级区域 |
| `--color-text-primary` | `#1a1a1a` | 正文 |
| `--color-text-secondary` | `#5c5c5c` | 辅助文字 |
| `--color-text-tertiary` | `#8c8a7a` | 提示/脚注 |
| `--color-border-default` | `#e8e6d8` | 默认边框 |
| `--color-border-subtle` | `#f0efe5` | 细分隔线 |

### 字体

- UI：PingFang SC / Microsoft YaHei / system-ui
- 编辑区：JetBrains Mono / Fira Code
- 公文预览：仿宋_GB2312 / FangSong / 黑体 / 楷体

### 组件库

Nuxt UI v2（`UFormGroup`, `UButton`, `UInput`, `USelect`, `UTabs`, `UAlert`, `UProgress`, `UIcon`）。图标：Heroicons（`i-heroicons-*`，本地模式）。

### baseline-ui / WCAG 2.1 合规

- 所有标题 `text-balance`，正文 `text-pretty`
- 使用 `h-dvh` 替代 `h-screen`
- 图标按钮 `aria-label`，表单错误 `aria-describedby`
- 拖拽元素提供 ▲/▼ 键盘替代 + `touch-action: manipulation`
- 固定元素 `safe-area-inset` 适配
- 禁止硬编码颜色（CSS 变量）、禁止 `transition: all`、禁止 `linear-gradient`（除非明确要求）
- 高对比度模式 `@media (prefers-contrast: high)`

### 布局

侧边导航（240px，可折叠至 64px）+ 右侧内容区。仪表盘为数字时钟 + 工具卡片网格（3 列）。侧栏状态通过 `localStorage("sidebar_collapsed")` 持久化。

### 仪表盘数字时钟

7 段数码管 LED 时钟（`DigitalClock.vue`）。响应式尺寸：`clamp(2.25rem, 5vw, 3.375rem)`，`role="timer"` + `aria-label`，暖纸主题配色。每秒更新，卸载时清除定时器。

---

## 四、后端架构（解耦）

```
backend/
├── app.py                  # Flask 工厂 (<70 行)
├── config.py               # 集中配置
├── errors.py               # ErrorCode 枚举 + ServiceResult + ServiceError
├── schemas.py              # Pydantic v2 请求 DTO (15+ Schema)
├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
├── json_logging.py         # JSON 结构化日志 (TimedRotatingFileHandler, 30 天)
├── models.py               # TaskRecord + OperationLog + BaseCRUD (原始 SQL)
├── cache.py                # Flask-Caching SimpleCache
├── cel.py                  # Celery (memory:// broker, 3 队列)
├── config_validators.py    # 启动时配置校验
├── gunicorn.conf.py        # 生产配置
├── blueprints/             # HTTP 路由层（每功能一个文件，共 12 个）
│   ├── convert.py          # /api/convert, /api/preview, /api/stats
│   ├── download.py         # /api/download, /api/health, /api/tasks/*
│   ├── properties_bp.py    # /api/properties/*
│   ├── img2pdf_bp.py       # /api/img2pdf
│   ├── pdf2img_bp.py       # /api/pdf2img
│   ├── print_split_bp.py   # /api/print-split/*
│   ├── watermark_bp.py     # /api/watermark/*
│   ├── pdf_editor_bp.py    # /api/pdf-editor/*
│   ├── excel_merge_bp.py   # /api/excel-merge
│   ├── pdf_to_text_bp.py   # /api/pdf-to-text
│   ├── pdf_merge_bp.py     # /api/pdf-merge
│   ├── pdf_compress_bp.py  # /api/pdf-compress
│   ├── metadata_clean_bp.py # /api/metadata-clean
│   ├── format_convert_bp.py # /api/convert/format
│   ├── page_decorate_bp.py # /api/page-decorate
│   └── image_process_bp.py # /api/image-process
├── services/               # 业务逻辑层 (纯函数，零 Flask 依赖，全部返回 ServiceResult[T])
│   ├── converter.py        # MD → DOCX (Pandoc)
│   ├── formatter.py        # GB/T 9704-2012 格式化
│   ├── watermark.py        # 水印添加/去除
│   ├── pdf_editor.py       # PDF 删除/插入/重排
│   ├── excel_merger.py     # Excel/CSV 合并
│   ├── img2pdf_handler.py  # 图片 → PDF
│   ├── pdf_to_images.py    # PDF → 图片 (pdftoppm)
│   ├── pdf_to_text.py      # PDF → 文本 (pdfminer)
│   ├── print_split.py      # 打印分组
│   ├── properties.py       # Office 属性读写
│   ├── pdf_merger.py       # PDF 合并 (pypdf)
│   ├── pdf_compressor.py   # PDF 压缩
│   ├── metadata_cleaner.py # 元数据清理
│   ├── format_converter.py # 格式互转 (LibreOffice/WeasyPrint)
│   ├── page_decorator.py   # 页码页眉页脚 (reportlab)
│   └── image_processor.py  # 图片处理 (Pillow)
├── tasks/                  # Celery 异步任务
│   ├── convert.py          # convert_queue
│   ├── pdf.py              # pdf_queue (8 tasks)
│   ├── office.py           # office_queue (3 tasks)
│   └── maintenance.py      # Beat: 定时清理
├── utils/
│   ├── base/               # file_helpers / validators
│   ├── file_security.py    # 魔数校验
│   ├── file_cleanup.py     # 定时文件清理
│   ├── retry.py            # @retry_on_failure
│   └── crypto.py           # AES-256 Fernet
└── tests/
```

### 分层原则

| 层 | 职责 | 约束 |
|----|------|------|
| **Blueprint** | HTTP 请求/响应 | 不包含业务逻辑，函数不超过 20 行 |
| **Service** | 业务逻辑 | 零 Flask 依赖，纯输入→输出函数 |
| **Utils** | 通用工具 | 可被任意层引用 |
| **Tasks** | 异步任务 | Celery task，更新 TaskRecord 进度 |

### Service 层规范

所有 Service 函数必须返回 `ServiceResult[T]`，通过 `ServiceResult.ok(data)` / `ServiceResult.fail(error, msg)` 构造。需要中断流程时 raise `ServiceError(code, msg, status)`，由全局 handler 自动捕获并转为标准化 JSON。

### 全局异常拦截

所有异常 → 标准化响应 `{code: <int>, msg: "<string>", requestId: "<hex>"}`。每个请求通过 `@app.before_request` 注入 `g.request_id`，响应头 `X-Request-Id` 回传，日志中贯穿。

Pydantic `ValidationError` → 422，`ServiceError` → 指定 status，`ValueError` → 400，`Exception` → 500（生产环境隐藏详情）。

---

## 五、API 端点全集

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/stats` | 转换计数 |
| `POST` | `/api/preview` | MD → HTML 预览 |
| `POST` | `/api/convert` | MD → DOCX |
| `POST` | `/api/convert/doc2md` | DOCX 格式化 |
| `GET` | `/api/download/<id>` | 下载文件（支持 Range） |
| `POST` | `/api/properties` | 修改属性 |
| `POST` | `/api/properties/info` | 读取属性 |
| `POST` | `/api/properties/batch` | 批量修改 |
| `POST` | `/api/img2pdf` | 图片合并 PDF |
| `POST` | `/api/pdf2img` | PDF 拆解为图片 |
| `POST` | `/api/print-split` | 打印分组 |
| `GET` | `/api/print-split/<id>/batch/<n>` | 下载批次 |
| `POST` | `/api/watermark` | 添加水印 |
| `POST` | `/api/watermark/remove` | 去除水印 |
| `POST` | `/api/pdf-editor/info` | PDF 页面信息 |
| `GET` | `/api/pdf-editor/thumb/...` | 页面缩略图 |
| `POST` | `/api/pdf-editor/delete` | 删除页面 |
| `POST` | `/api/pdf-editor/insert` | 插入页面 |
| `POST` | `/api/pdf-editor/reorder` | 重排页面 |
| `POST` | `/api/excel-merge` | Excel 合并 |
| `POST` | `/api/pdf-to-text` | PDF 提取文本 |
| `POST` | `/api/pdf-merge` | 合并多个 PDF |
| `POST` | `/api/pdf-compress` | 压缩 PDF |
| `POST` | `/api/metadata-clean` | 清除元数据 |
| `POST` | `/api/convert/format` | 格式互转 (DOCX/HTML→PDF) |
| `POST` | `/api/page-decorate` | 添加页码/页眉/页脚 |
| `POST` | `/api/image-process` | 图片处理 (缩放/裁剪/转换/压缩) |
| `GET` | `/api/tasks/<id>` | 任务状态轮询 |
| `GET` | `/api/tasks/<id>/stream` | 任务进度 SSE |

---

## 六、异步任务框架

### Celery 配置

- Broker: `memory://`（开发），生产换 Redis/RabbitMQ
- Result backend: `db+sqlite:///tasks.db`
- 3 个队列：`convert_queue` / `pdf_queue` / `office_queue`
- 每队列独立 Worker 进程，避免资源抢占
- Celery Beat: 每日凌晨 3 点清理 7 天前临时文件

### 任务追踪

`task_records` 表（SQLite）记录任务完整生命周期：`pending → started → progress → success/failure`。`operation_logs` 表记录操作审计（操作类型、资源 ID、文件大小、IP、耗时）。

### 进度推送

SSE（Server-Sent Events）：`GET /api/tasks/{id}/stream`。前端 `useTaskStream` composable 自动连接/断开，提供 `{ progress, status, message, result, error }` 响应式状态。轮询端点 `/api/tasks/{id}` 作为降级方案。

---

## 七、文件安全

### 三层校验

1. **大小限制**：单文件 ≤ 100MB
2. **扩展名白名单**：仅允许 `pdf/docx/xlsx/pptx/png/jpg/jpeg/tiff/tif/csv/md`
3. **魔数签名**：校验文件头字节与扩展名匹配（防改扩展名攻击）

### 定时清理

替代原有的 `@after_this_request` 即时删除模式。Celery Beat 每日清理超过 7 天的临时文件。文件保留 7 天便于调试和重试下载。

### 加密

AES-256 Fernet（cryptography 库）。密钥通过环境变量 `DOCSTAMP_ENCRYPTION_KEY` 注入。当前预留能力，用于未来敏感字段（如邮箱配置）加密存储。

### 重试

`@retry_on_failure(max_retries=2)` 装饰器。应用于依赖外部工具（Pandoc/pdftoppm）的 Service 函数。2 次重试后降级为 `CONVERSION_RETRY_EXHAUSTED` 错误提示。

---

## 八、前端架构

### 技术栈

| 组件 | 版本 |
|------|------|
| Nuxt | 3.15.4 (锁死) |
| @nuxt/ui | ^2.21 |
| @nuxtjs/i18n | ^9.5 |
| @nuxt/icon | ^1.10 |
| Tailwind CSS | v3 (tailwind.config.ts) |
| Vuelidate | @vuelidate/core |

### Composables

| Composable | 功能 |
|-----------|------|
| `useValidation` | Vuelidate 封装：`v$` 状态 + `errors` 字典 + `validate()` |
| `useTaskStream` | SSE 进度监听：`{ progress, status, message, result, error, connect, close }` |
| `useApi` | 通用 API 封装：`{ data, loading, pagination, fetchList }` + `useCache` |
| `useDownload` | Blob 下载封装 |

### 原子组件 (`components/ui/`)

| 组件 | 说明 |
|------|------|
| `ButtonPrimary.vue` | 品牌绿主按钮 |
| `CardBase.vue` | 基础卡片（shadow/radius token） |
| `ProgressBar.vue` | 进度条（含 ARIA `role="progressbar"`） |

### 命名规范

| 层级 | 规范 | 示例 |
|------|------|------|
| 组件 | PascalCase | `DigitalClock.vue`, `ProgressBar.vue` |
| composables | `useXxx.ts` | `useValidation.ts`, `useTaskStream.ts` |
| pages | kebab-case 路由路径 | `md-to-docx.vue`, `file-assembly.vue` |

---

## 九、部署

### 开发模式

```bash
./manage.sh start    # Flask :5000 + Nuxt :8080 (HMR)
```

### 生产模式

```bash
./manage.sh prod     # Gunicorn 4 workers :5000 单端口, 含前端静态
```

Flask SPA fallback 路由直接提供 Nuxt 构建输出（`.output/public/`），无需独立 Node.js 进程。

### Gunicorn 配置

`gunicorn.conf.py`: `bind 0.0.0.0:5000`, `workers=4`, `timeout=120`。日志输出到 `/var/log/docstamp/`。

---

## 十、开发经验

### 后端

| 问题 | 原因 | 解决 |
|------|------|------|
| `logging.py` 模块冲突 | 文件名遮蔽 stdlib `logging` | 重命名为 `json_logging.py` |
| `config/` 目录冲突 | `config.py` 与 `config/` 包同名 | 删除 `config/` 目录，改为 `config_validators.py` |
| 变量名不匹配 500 | 批量替换只改定义未改引用 | 修改后 grep JSON 响应字段一致性 |
| 中文字体不生效 | `run.font.name` 只读西文 | 读 XML `w:rFonts/w:eastAsia` |
| Pandoc 标题蓝色 | Pandoc Heading 自带颜色 | 移除 `w:pStyle` 后重设字体 |
| Nuxt `import.meta.client` | composable 条件调用 | `useHead()` 必须在顶层无条件调用 |

### 前端

| 问题 | 原因 | 解决 |
|------|------|------|
| Nuxt 3.21.x dev 500 | `rollupOptions.input` 空 bug | 锁死 Nuxt 3.15.4 |
| 布局动态导入失败 | 旧 `.nuxt` 缓存 + composable 违规 | manage.sh 启动时清理缓存; `useHead` 移出条件块 |
| `UFormField` 不存在 | Nuxt UI v4→v2 API 差异 | 全局替换为 `UFormGroup` |
| i18n locale 404 | `@nuxtjs/i18n` v9 路径变更 | 从 `i18n/locales/` 移到 `locales/` |
| Tailwind v4→v3 | `@import "tailwindcss"` 语法差异 | 改为 `@tailwind base/components/utilities` + `tailwind.config.ts` |

### 部署

| 问题 | 解决 |
|------|------|
| SPA fallback 目录路由 404 | Flask `static_url_path=""` 拦截 → 移除此配置，手动处理 Nuxt dir/index.html |
| 旧进程占用端口 | `manage.sh` 内置 `fuser -k` |
| 日志权限 | `mkdir -p /var/log/docstamp` + chown |
| Gunicorn 僵死 PID | `_start_backend()` 启动前检查 PID 有效性 |

---

## 十一、版本历史

### v3.1 (2026-06)
- **新增 7 个工具**：PDF 合并、PDF 压缩、格式互转、图片处理、页码页眉页脚、元数据清理、PDF 转文本
- **蓝图拆分**：`files.py`（678 行）拆分为 12 个独立蓝图文件，功能边界清晰
- **ServiceResult 全面应用**：所有 16 个 service 统一返回 `ServiceResult[T]`，消除裸 `raise ValueError`
- **新依赖**：weasyprint (HTML→PDF)、libreoffice-core (DOCX→PDF)

### v3.0 (2026-06)
- **架构解耦**：app.py 1278 行 → 62 行 (Blueprint + Service + Utils 分层)
- **Nuxt 4 → Nuxt 3** 降级（稳定 LTS）
- 后端基础设施：ErrorCode + ServiceResult + Pydantic v2 + 全局异常拦截 + JSON 日志
- 异步框架：Celery 3 队列 + TaskRecord + OperationLog + SSE 进度推送
- 文件安全：魔数校验 + 定时清理 + 重试装饰器 + AES 加密
- 前端：Vuelidate + 代码分割 + DigitalClock 响应式 + WCAG 2.1 无障碍
- 代码质量：pre-commit (black/flake8/isort/mypy) + ESLint + Prettier
- 生产模式：Gunicorn 单端口 + SPA fallback
- 去除用户系统、登录、AI Chat、隐藏页面

### v2.3 (2026-06)
- 侧栏分组悬浮子菜单；数字时钟；侧栏持久化

### v2.2 (2026-06)
- 移除电子书转 MD

### v2.1 (2026-06)
- PDF 水印去除增强；baseline-ui 合规

### v2.0 (2026-06)
- Buefy → Nuxt 4 + Nuxt UI v4 架构升级

### v1.0 (2026-06)
- 5 大核心功能、Buefy + Flask 初始版本
