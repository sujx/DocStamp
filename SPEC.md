# 鹊随金印 (docStamp) — 设计规范与开发指南

## 一、项目概述

鹊随金印是一站式文档处理工具箱。Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 前端，Flask REST API 后端。SynTime Royal Blue 品牌色系（`#4C7DF0` + `#EEF0F4`），仪表盘 + 侧边导航 + 多页面路由。

**定位**：单体工具，无用户系统，无认证，AI 功能可选（未配 Key 自动降级）——即开即用，随用随走。

**i18n**：中英文双语，`locales/zh-CN.json` + `locales/en.json`，默认 `zh-CN`。

---

## 二、功能模块（14 个）

**侧栏导航**：

```
首页              → /
MD 转公文          → /md-to-docx
文档转 MD          → /doc-to-md
格式规范          → /format-docx
视频转换          → /video-convert   (MP4→WMV)
RSS 探测          → /rss-detect      (Feed 发现)
属性修改          → /properties      (元数据 + 清理)
Excel 合并        → /excel-merge
PDF 工具 ▸        → /file-assembly  /print-split  /pdf-editor  /pdf-tools  /pdf-merge
使用统计          → /status
```

| # | 模块 | 路由 | 说明 |
|---|------|------|------|
| 1 | 仪表盘 | `/` | 工具卡片网格（3 列） |
| 2 | MD 转公文 | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX + AI 纠错 |
| 3 | 文档转 MD | `/doc-to-md` | PDF/Word/PPT/图片 → Markdown（MinerU API） |
| 4 | 属性修改 | `/properties` | 元数据修改 + 元数据清理（双 Tab） |
| 5 | Excel 合并 | `/excel-merge` | .xlsx/.csv 结构相同合并 |
| 6 | 格式规范 | `/format-docx` | GB/T 9704-2012 格式化 |
| 7 | 视频转换 | `/video-convert` | MP4 → WMV（PPT 嵌入） |
| 8 | RSS 探测 | `/rss-detect` | 输入 URL，自动发现 RSS/Atom 订阅地址 |
| 9 | 文件组装 | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 10 | 打印分组 | `/print-split` | 批次拆分、暂停/继续/终止 |
| 11 | PDF 编辑 | `/pdf-editor` | 删除/插入/重排页面 |
| 12 | 调整 PDF | `/pdf-tools` | PDF 转文本 + 压缩 + 页码页眉页脚（三 Tab） |
| 13 | PDF 合并 | `/pdf-merge` | 多 PDF 合并，拖拽排序 |
| 14 | 使用统计 | `/status` | 模块调用量 + 访客统计 + ECharts 可视化 |

---

## 三、设计系统 (SynTime Royal Blue)

### 配色 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-500` | `#4C7DF0` | 品牌主色 |
| `--color-brand-600` | `#3B63D8` | 悬停加深 |
| `--color-brand-700` | `#2F4FB0` | 渐变终点/深色强调 |
| `--color-brand-800` | `#27408D` | 最深色 |
| `--color-brand-soft` | `rgba(76,125,240,0.10)` | 柔和底色（图标徽章等） |
| `--color-page` | `#EEF0F4` | 页面底色（navy-gray） |
| `--color-surface` | `#ffffff` | 卡片/面板白 |
| `--color-muted` | `#F4F6FA` | 次级区域 |
| `--color-text-primary` | `#1F2A44` | 正文（~12:1 对比度） |
| `--color-text-secondary` | `#56627A` | 辅助文字（~5.5:1） |
| `--color-text-tertiary` | `#6E7A93` | 提示/脚注（~4.5:1 WCAG AA） |
| `--color-border-default` | `#E3E8F0` | 默认边框 |
| `--color-border-subtle` | `#EEF0F4` | 细分隔线 |
| `--color-seal-red` | `#C0392B` | 印章红（品牌点缀） |

### 阴影与圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | `6px` | 按钮/标签 |
| `--radius-md` | `8px` | 面板/卡片 |
| `--radius-lg` | `12px` | 模态框/弹出层 |
| `--radius-xl` | `16px` | 侧边栏/大面板 |
| `--shadow-card` | `0 2px 6px rgba(26,43,79,0.05)` | 卡片阴影 |
| `--shadow-elevated` | `0 6px 14px -2px rgba(26,43,79,0.07)` | 弹出菜单/悬浮卡片 |
| `--shadow-sidebar` | `0 12px 22px -4px rgba(26,43,79,0.08)` | 侧边栏阴影 |

### 字体

- UI：**Plus Jakarta Sans** + PingFang SC / Microsoft YaHei / system-ui
- 标题：Plus Jakarta Sans 优先（字重 700），中西文混排
- 编辑区：JetBrains Mono / Fira Code
- 公文预览：仿宋_GB2312 / FangSong / 黑体 / 楷体

### 组件库

Nuxt UI v2（`UFormGroup`, `UButton`, `UInput`, `USelect`, `UTabs`, `UAlert`, `UProgress`, `UIcon`）。图标：Heroicons（`i-heroicons-*`，本地模式）。

### baseline-ui / WCAG 2.1 合规

- 所有标题 `text-balance`，正文 `text-pretty`
- 使用 `h-dvh` 替代 `h-screen`
- 图标按钮 `aria-label`（统一使用 `a11y.*` i18n 键）
- 表单错误 `aria-describedby`
- 拖拽元素提供 ▲/▼ 键盘替代 + `touch-action: manipulation`
- 固定元素 `safe-area-inset` 适配
- 全局 `:focus-visible` 轮廓（2px brand-700，offset 2px）
- 禁止硬编码颜色（仅 CSS 变量 / Tailwind token）、禁止 `transition: all`、禁止 `linear-gradient`（除非明确要求）
- `@media (prefers-reduced-motion: reduce)` 全局禁用动画（`animation/transition-duration: 0.01ms`）
- `@media (prefers-contrast: high)` 高低对比度模式
- 键盘用户 skip-to-content 跳转链接（`sr-only focus:not-sr-only`）
- 页面过渡：150ms opacity 淡入淡出（`mode="out-in"`，`prefers-reduced-motion` 自动跳过）
- 所有悬停状态统一 `duration-150` 过渡
- 最小触摸目标 44×44px（`min-h-[44px]`）
- 文本对比度 ≥ 4.5:1 WCAG AA（text-primary 16.6:1, text-secondary 6.3:1, text-tertiary 4.69:1）

### 布局

桌面端：深色极光渐变侧边导航（256px 展开 / 72px 收起）+ 右侧内容区。侧边栏背景 `linear-gradient(168deg, #2A2166, #23337A, #1E4E7E, #17646B, #4A3D20)`。移动端（<1024px）：侧栏悬浮叠加模式（汉堡按钮 `fixed top-4 left-4 z-50` + 半透明遮罩 `bg-black/30`），点击导航项或遮罩自动关闭。仪表盘为工具卡片网格（3 列）。侧栏状态通过 `localStorage("sidebar_collapsed")` 持久化。

### 仪表盘

工具卡片网格按功能分组展示（转换/PDF/Office/更多），每张卡片含图标徽章 + 标题 + 描述 + 悬停箭头指示。卡片使用 `.card.card-interactive` 全局样式，悬停时上浮 + 阴影加深 + 图标徽章反色。

---

## 四、后端架构（解耦）

```
backend/
├── __init__.py              # 包标记（Docker PYTHONPATH 导入必需）
├── app.py                  # Flask 工厂 (<70 行)
├── config.py               # 集中配置
├── errors.py               # ErrorCode 枚举 + ServiceResult + ServiceError
├── schemas.py              # Pydantic v2 请求 DTO (15+ Schema)
├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
├── json_logging.py         # JSON 结构化日志 (TimedRotatingFileHandler, 30 天)
├── models.py               # TaskRecord + OperationLog + BaseCRUD (原始 SQL)
├── cache.py                # Flask-Caching SimpleCache
├── celery_app.py           # Celery (Redis broker, 2 队列)
├── config_validators.py    # 启动时配置校验
├── gunicorn.conf.py        # 生产配置
├── blueprints/             # HTTP 路由层（每功能一个文件，共 18 个；实际路径均带 /api/v1 前缀）
│   ├── convert.py          # /api/convert, /api/preview, /api/stats (计数)
│   ├── download.py         # /api/download, /api/health, /api/tasks/*
│   ├── stats_bp.py         # /api/stats/overview, /api/stats/seed
│   ├── properties_bp.py    # /api/properties/*
│   ├── img2pdf_bp.py       # /api/img2pdf
│   ├── pdf2img_bp.py       # /api/pdf2img
│   ├── print_split_bp.py   # /api/print-split/*
│   ├── pdf_editor_bp.py    # /api/pdf-editor/*
│   ├── excel_merge_bp.py   # /api/excel-merge
│   ├── pdf_to_text_bp.py   # /api/pdf-to-text
│   ├── pdf_merge_bp.py     # /api/pdf-merge
│   ├── pdf_compress_bp.py  # /api/pdf-compress
│   ├── metadata_clean_bp.py # /api/metadata-clean
│   ├── page_decorate_bp.py # /api/page-decorate
│   ├── rss_detect_bp.py    # /api/rss-detect
│   ├── video_convert_bp.py # /api/video-convert
│   ├── watermark_bp.py     # /api/watermark（入口已下线，仅存接口）
│   └── company_lookup_bp.py # /api/company-lookup（入口已下线，仅存接口）
├── services/               # 业务逻辑层 (纯函数，零 Flask 依赖，全部返回 ServiceResult[T])
│   ├── converter.py        # MD → DOCX (Pandoc)
│   ├── formatter.py        # GB/T 9704-2012 格式化
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
│   ├── video.py            # pdf_queue: MP4 → WMV
│   └── maintenance.py      # office_queue: Beat 定时清理
├── utils/
│   ├── base/               # file_helpers / validators
│   ├── file_security.py    # 魔数校验 + 扩展名白名单 + 大小限制
│   ├── file_cleanup.py     # 定时文件清理
│   ├── rate_limit.py       # IP 级别 API 限流装饰器
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
| `GET` | `/api/stats` | 转换计数（全局累加器） |
| `GET` | `/api/stats/overview` | 使用统计仪表盘（按模块/日/访客聚合） |
| `POST` | `/api/stats/seed` | 生成测试数据 |
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
| `POST` | `/api/video-convert` | 视频转换 MP4→WMV |
| `GET` | `/api/tasks/<id>` | 任务状态轮询 |
| `GET` | `/api/tasks/<id>/stream` | 任务进度 SSE |

---

## 六、异步任务框架

### Celery 配置

- Broker: Redis（生产默认 `redis://127.0.0.1:6379/0`），`memory://` 仅开发用
- Result backend: Redis（`redis://127.0.0.1:6379/1`）
- 2 个队列：`pdf_queue`（视频转换） / `office_queue`（定时清理），由同一 Worker 容器消费
- 并发：容器内 `--concurrency=2`（`worker_concurrency=4` 仅为无 CLI 覆盖时的默认值），`task_acks_late=True` 防任务丢失
- Celery Beat: 每日凌晨 3 点清理 7 天前临时文件

### 任务追踪

`task_records` 表（SQLite）记录任务完整生命周期：`pending → started → progress → success/failure`。`operation_logs` 表记录操作审计（操作类型、资源 ID、文件大小、IP、耗时）。

### 进度推送

SSE（Server-Sent Events）：`GET /api/tasks/{id}/stream`。前端 `useTaskStream` composable 自动连接/断开，提供 `{ progress, status, message, result, error }` 响应式状态。轮询端点 `/api/tasks/{id}` 作为降级方案。

---

## 七、文件安全

### 三层校验

1. **大小限制**：单文件 ≤ 50MB（`file_security.MAX_FILE_SIZE`），Flask 层 `MAX_CONTENT_LENGTH=110MB` 兜底
2. **扩展名白名单**：`pdf/docx/xlsx/pptx/png/jpg/jpeg/tiff/tif/webp/csv/html/htm/md/markdown/txt`
3. **魔数签名**：校验文件头字节与扩展名匹配（防改扩展名攻击）；无签名的扩展名（webp/html/htm/csv/md/txt）跳过魔数校验

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
| `tools.config.ts` | 工具定义（ToolDef/ToolGroup）、侧栏分组、仪表盘卡片 |
| `useValidation` | Vuelidate 封装：`v$` 状态 + `errors` 字典 + `validate()` |
| `useTaskStream` | SSE 进度监听：`{ progress, status, message, result, error, connect, close }` |
| `useApi` | 通用 API 封装：`{ data, loading, pagination, fetchList }` + `useCache` |
| `useDownload` | Blob 下载封装 + 错误提取 |
| `useAi` | AI 功能封装（纠错/分类/去噪/文件名生成） |

### 原子组件 (`components/ui/`)

| 组件 | 说明 |
|------|------|
| `CardBase.vue` | 基础卡片（`.card` 全局工具类：边框 + 圆角 + 内边距） |
| `SkeletonBlock.vue` | 骨架屏占位块（可配置宽高，`animate-pulse`） |

### 全局 CSS 工具类

| 类名 | 说明 |
|------|------|
| `.card` | 卡片容器：`border + border-radius(var(--radius-lg)) + padding: 1.25rem`（定义于 `@layer components`） |
| `.card-interactive` | 可交互卡片：悬停上浮 + 阴影加深 + 图标徽章反色 |
| `.brand-title` | 品牌标题：Plus Jakarta Sans 700 + 字距 0.06em + 品牌蓝渐变（`brand-600`→`brand-800`） |
| `.icon-badge` | 图标徽章：圆形品牌色底色，悬停时反色（白底→蓝底白图标） |
| `.gradient-text` | 渐变文本：品牌蓝渐变文字 |

### 关键架构决策

- **Panel 去重**：`PdfToTextPanel` / `PdfCompressPanel` / `PageDecoratePanel` 是各自功能的唯一实现。独立页面（`pdf-to-text.vue` 等）和 Tab 页（`pdf-tools.vue`）共享同一 Panel 组件，消除逻辑重复。
- **懒加载**：Panel 组件通过 `defineAsyncComponent(() => import(...))` 按需加载。
- **已删除组件**：`AppHeader.vue`（未使用，功能由 Sidebar 覆盖）、`ButtonPrimary.vue`（由 Nuxt UI `<UButton>` 替代）、`ProgressBar.vue`（由 Nuxt UI `<UProgress>` 替代）。

### 命名规范

| 层级 | 规范 | 示例 |
|------|------|------|
| 组件 | PascalCase | `DigitalClock.vue`, `ProgressBar.vue` |
| composables | `useXxx.ts` | `useValidation.ts`, `useTaskStream.ts` |
| pages | kebab-case 路由路径 | `md-to-docx.vue`, `file-assembly.vue` |

---

## 九、部署

docStamp 使用 Docker Compose 部署，3 容器适配 2C2G 服务器：

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 构建并启动
docker compose up -d --build

# 3. 查看状态
docker compose ps
```

### 容器清单

| 容器 | 职责 | 端口 |
|------|------|:---:|
| `api` | Gunicorn gthread + 静态文件 | `127.0.0.1:5000` |
| `redis` | Celery broker + 结果后端 + 缓存（128MB） | 内部 |
| `celery` | 2 队列合并 + Beat 内嵌（concurrency=2） | — |

### 资源配置

| 组件 | 配置 |
|------|------|
| Redis | `maxmemory 128mb`, allkeys-lru |
| API | gunicorn `--workers 2` |
| Celery | 2 队列合并, `--concurrency=2`, Beat 内嵌 (`-B`) |
| Celery 内存限制 | `mem_limit: 512M` |
| 预估总内存 | ~800MB |

### 健康检查

所有容器均配置健康检查：Redis `redis-cli ping` → API `curl /api/health` → Celery `celery inspect ping`，通过 `condition: service_healthy` 确保依赖就绪后再启动。容器以非 root 用户 `docstamp` 运行，entrypoint 脚本处理 Docker volume 权限。

### 管理脚本

```bash
./manage.sh docker-up     # 构建并启动
./manage.sh docker-down   # 停止
./manage.sh start         # 本地开发模式（Flask + Nuxt）
./manage.sh stop          # 停止开发服务
```

### Gunicorn 配置

`gunicorn.conf.py`: `bind 0.0.0.0:5000`, `worker_class=gthread`, `threads=4`, `workers=2`, `timeout=120`, `max_requests=1000`（防内存泄漏）。日志输出到 `/var/log/docstamp/`。

### Nginx 反向代理

配置 nginx 将请求转发到 `127.0.0.1:5000`。注意 `/_nuxt/` 静态资源 location 需保留 `proxy_pass http://127.0.0.1:5000`（前端静态文件由 gunicorn 提供），同时设置 `expires 1y` + `Cache-Control: public, immutable`。

### 速率限制

双层防御：nginx 层粗粒度限流 + 应用层 `@rate_limit` 装饰器（IP 级别，基于 Flask-Caching）。上传接口按负载分级：轻量 20/min、标准 10/min、重量 5/min。超限返回 429。

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

### v3.7 (2026-09)

- **SynTime Royal Blue 品牌重塑**：全站配色从绿鹃品牌绿（`#008A3D`）迁移至 SynTime Royal Blue（`#4C7DF0`）。深色极光渐变侧边导航（`#2A2166`→`#4A3D20`），navy-gray 页面底色（`#EEF0F4`），印章红点缀（`#C0392B`）。侧栏尺寸调整为 256px 展开 / 72px 收起。完整设计 Token 体系见第三节
- **功能入口精简**：水印与公司官网查询两个工具从 16 个入口精简至 14 个——移除 `tools.config.ts` 注册、仪表盘卡片与侧栏入口。**未删除**的部分：后端蓝图/服务（`watermark_bp.py` / `watermark.py` / `company_lookup_bp.py` / `company_lookup.py`）仍在 `app.py` 注册并可调用，前端页面 `/watermark`、`/company-lookup` 仍会被 SSG 预渲染并可直链访问，i18n 键与 `test_company_lookup.py` 也保留。彻底清理见后续版本
- **文档标准化**：`CLAUDE.md` 迁移至 Qoder 标准的 `AGENTS.md`，冗余文档（`CODE_STANDARDS_ANALYSIS.md` / `IMPLEMENTATION_GUIDE.md`）归档，`SPEC.md` 全面更新为当前设计系统

### v3.6 (2026-06)

- **视频转换**：新增视频转换功能（MP4 → WMV），解决 PowerPoint 无法嵌入 MP4 的问题。上传后显示 MP4 源文件预览，异步转换（Celery `video_convert_async` task + SSE 进度推送 + `UProgress` 进度条），完成后提供 WMV 下载。后端 `services/video_converter.py` + `blueprints/video_convert_bp.py` + `tasks/video.py`，ffmpeg WMV2+WMA2 codec。文件限制 100MB（前端即时拦截 + 后端 `MAX_FILE_SIZE`），速率限制 5次/分钟。Dockerfile 新增 ffmpeg + libopenh264-7，视频格式跳过魔数校验。FileUploader 组件新增 `maxSize` prop 前端校验
- **使用统计补充**：`stats_bp.py` 新增 `video-convert` 和 `doc-to-md` 模块中文标签
- **侧栏优化**：仪表盘 → 首页，仪表盘页面去除标题文字。侧栏默认收起（64px 图标模式，展开偏好持久化 localStorage），移动端悬浮遮罩模式 + 0 占位。品牌 Logo 改用 Vite import 方式加载（`import logoUrl from "~/public/logo.svg"`），绕过 Nuxt 3.15 + Vite 6 `virtual:public` 模块 bug
- **移动端适配**：16 个页面统一响应式 padding（`px-4 sm:px-6 py-6 sm:py-8`），视频转换面板按钮移动端竖向堆叠（`flex-col sm:flex-row`），触摸目标 ≥ 44px（`min-h-[44px]`），FileUploader 组件新增 `maxSize` prop 前端拦截。
- **基础设施加固**：Celery `result_expire` 默认 12h（视频 6h），API 响应头 `X-API-Version: 3.6`，健康检查含 ffmpeg/pandoc 依赖探测，下载文件名 XSS 净化（`safe_download_name()`），`pyproject.toml` 补充 6 个缺失依赖
- **测试覆盖**：pytest 4 个 service（video_converter/pdf_merger/properties/metadata_cleaner），12 条测试。发现并修复 3 个未处理异常：`read_properties` 缺 FileNotFoundError、`clean_metadata` 缺 FileNotFoundError、`modify_properties` 缺 PackageNotFoundError
- **文档同步**：SPEC 定位描述"无 AI"→"可选 AI"，CLAUDE.md 删除 3 个已死组件引用，新增 `composables/useError.ts` 统一错误提取工具
- **PV/UV 统计**：新增 `/api/v1/track` beacon 端点 + `usePageView.ts` composable（`sendBeacon` 优先），layout 中 `watch(route.fullPath)` 自动追踪每次页面浏览。独立访客 IP 通过 `X-Forwarded-For` 头获取（nginx 代理后 `remote_addr` 始终为 127.0.0.1 的修复）
- **SEO 基础**：`robots.txt` + `/sitemap.xml`（14 个页面自动生成）+ Open Graph meta 标签（`og:title/description/type`）+ keywords
- **RSS 订阅探测器**：参考 [RSSHub-Radar](https://github.com/DIYgod/RSSHub-Radar) 规则引擎设计，三层模块化探测（HTML `<link>` 扫描 → 常见路径探测 → `rss_rules.json` 站点规则匹配）。规则通过 JSON 文件扩展，支持 `feeds`（直连）和 `path_rules`（`:param` 捕获）两种格式。后端 `services/rss_detector.py` + `blueprints/rss_detect_bp.py`，前端输入 URL → 显示订阅源列表（可复制/打开）。零新依赖（stdlib `html.parser`）

- **公司官网查询**：三阶梯查找策略 — ① 本地 SQLite 数据库（`company_records` 表，用户确认后缓存，秒级响应）→ ② AI 大模型直接查询（DeepSeek，从训练数据中回答，8s 超时）→ ③ AI 大模型 + 实时 Web 搜索（智谱 GLM-4 + web_search 工具，适用新增企业）。支持单次查询和批量查询（≤10 条同步即时返回，>10 条异步 Celery + SSE 进度）。本地数据库支持 CSV/JSON 批量导入导出（UTF-8 BOM，兼容 Excel）。公司名自动规范化（去括号注解、去公司后缀、去城市/"中国"前缀）。前端双 Tab 布局（单次 + 批量），结果表格含来源标识（本地库/搜索引擎）、确认/修正/一键确认功能。后端 `services/company_lookup.py` + `models.py:CompanyRecord` + `blueprints/company_lookup_bp.py`，42 个 pytest 测试覆盖全部路径。

### v3.5.2 (2026-06)

- **Code Review 全面修复**：FormatDocxTab 错误处理修复（JSON 端点误用 `.text()` + `JSON.parse` → 直读 `e.response.data.error`），`transition-all` 违规修复（3 组件 → 具体属性列表），CSS `--shadow-*` 变量与 Tailwind 配置同步为 `none`
- **Docker 本地构建编排**：新增 `docker-compose.local.yml`，本地 Dockerfile 构建，3 容器 Lite 模式，无需 ACR。适合自建服务器和无容器镜像仓库环境
- **Docker 启动修复**：`docker-compose.prod-lite.yml` gunicorn 入口 `backend.app:app` → `backend.wsgi:app`（app.py 为工厂函数，模块级无 `app` 属性）
- **Stats 模块名修复**：操作日志中间件 `parts[1]` → `parts[2]`，修复所有真实流量被记录为 `"v1"` 的 bug（路径 `/api/v1/convert` 解析错误）
- **下载可靠性修复**：`pdf-merge.vue` 下载补全 `document.body.appendChild(a)` + `setTimeout` 延迟回收（防止 Firefox/Safari 静默失败）
- **CORS 默认值更新**：`docker-compose.local.yml` 默认包含 `https://doc.sujx.net`
- **数据库持久化**：5 个 compose 文件新增 `db_data` 卷挂载 + `DOCSTAMP_TASK_DB` 环境变量，修复容器重启后操作日志/统计数据丢失。Dockerfile + entrypoint 预创建 `/opt/docstamp/backend/data` 目录确保非 root 用户可写
- **字体自托管**：Plus Jakarta Sans 从 Google Fonts CDN（国内 ~4.8s 延迟）改为本地 TTF 自托管（`public/fonts/`，256KB），`font-display: swap` 消除渲染阻塞
- **Docker 构建优化**：`publish.sh` 使用 `--build-arg BUST_FRONTEND=$(date +%s)` 精准破前端构建缓存（~2min），替代 `--no-cache` 全量重建（~8min）；Dockerfile `npm ci` 添加 ETXTBSY 重试
- **Nginx 部署要点**：`/_nuxt/` 静态资源 location 需保留 `proxy_pass http://127.0.0.1:5000`（否则 nginx 本地找文件 → 404），同时设置 `expires 1y` + `Cache-Control: public, immutable`
- **Sidebar 顺序调整**：格式规范移至文档转 MD 之后（order 12→4）
- **清理**：移除未使用的 a11y i18n 键（deletePage/insertPage/reorderPage），doc-to-md 遗留 CSS 变量转为 Tailwind 工具类

### v3.5.1 (2026-06)

- **UI/UX Pro Max — Flat Design 全面升级**：品牌标题去渐变（金绿渐变 → 品牌绿实色），全局阴影归零（`shadow-card/elevated/sidebar: none`，边框替代阴影视觉分隔），全局悬停过渡统一 `duration-150`
- **字体升级**：UI 字体栈新增 Plus Jakarta Sans 优先（Google Fonts，400/500/600/700），中西文混排
- **全局 `.card` 工具类**：`@layer components` 定义卡片容器（`border + radius-md + padding: 1.5rem`），消除 10+ 文件中的重复 scoped CSS
- **页面宽度标准化**：所有工具页面统一 `max-w-5xl`（原混用 3xl/4xl/5xl/6xl）
- **硬编码颜色清零**：全局替换 `#e8e6d8`/`#f4f2e4`/`#008a3d` 内联样式为 Tailwind token（`border-default`/`bg-muted`/`text-brand-700`），修复 CSS 变量名错误（`--color-bg-soft`→`--color-muted`）
- **死代码清理**：删除 `AppHeader.vue`（未导入）、`ButtonPrimary.vue`（`UButton` 替代）、`ProgressBar.vue`（`UProgress` 替代）；`CardBase.vue` 对齐全局 `.card` 模式
- **PageHeader 增强**：支持 `title`/`description` props 渲染，回退链接改用 `ULink` + 悬停态过渡
- **Panel 去重**：`pdf-to-text.vue` / `pdf-compress.vue` / `page-decorate.vue` 改为委托 Panel 组件（~150 行 → ~10 行），与 `pdf-tools.vue` Tab 页共享唯一实现
- **页面过渡**：`layouts/default.vue` 增加 `<Transition name="page-fade" mode="out-in">`（150ms opacity），`prefers-reduced-motion` 自动跳过
- **无障碍增强**：全局 `:focus-visible` 轮廓（2px brand-700 + 2px offset），所有图标按钮补 `aria-label`（统一 `a11y.*` i18n 键），新增骨架屏组件 `SkeletonBlock.vue`
- **AI 功能（DeepSeek v4 Flash）**：文本纠错（MD 转公文前自动纠正错别字和标点）、格式意图识别（自动检测正式公文并建议 GB/T 格式）、智能文件名生成、PDF 文本去噪（自动去除页眉页脚/水印残留）。Prompt 级缓存（SHA256, 1h TTL），未配 Key 时静默降级返回原文。
- **文档转 MD（MinerU API）**：新增「文档转MD」功能，支持 PDF/DOC/DOCX/PPT/PPTX/PNG/JPG → Markdown（vlm 模型 + OCR + 公式/表格识别），200MB/200 页限制。异步轮询 + ZIP 提取 + 24h 缓存。`DOCSTAMP_PUBLIC_URL` 配置公网文件访问地址。
- **功能重组**：元数据清理合并到属性修改（Tab 切换），PDF 转文本/压缩/页码合并为「调整PDF」三合一页面，图片处理功能删除，Office 工具组展开到侧栏顶层。
- **品牌定名**：鹊随金印，品牌蓝渐变标题（`#4C7DF0`→`#2F4FB0`）印章浮雕质感。
- **多厂商 AI 支持**：`AI_API_URL` + `AI_MODEL` 环境变量配置，支持 OpenAI / DeepSeek / Ollama 等任意兼容厂商。
- **Full/Lite 双模式**：Lite（3 容器/4 systemd 服务，~800MB）适配 2C2G ECS；Full（6 容器）高并发。统一部署脚本 `docker-deploy.sh`。
- **Valkey 支持**：RHEL 10 / RockyLinux 10 已用 Valkey 替代 Redis。`install.sh` 自动检测发行版选择对应包名（apt→redis，dnf→valkey），systemd 单元同时兼容两种服务名。
- **python-dotenv 自动加载**：`app.py` 启动时自动查找并加载 `.env`，不再依赖 shell 脚本手动 source。所有启动方式（gunicorn / python / systemd / Docker）统一。
- **构建 OOM 修复**：`install.sh` 根据 `/proc/meminfo` 自动设置 Node 堆大小（75% RAM），Dockerfile `ARG NODE_HEAP` 可覆盖，SSG 预渲染 `concurrency=1` 串行执行避免内存峰值。
- **ACR 发布流程**：`publish.sh` — 登录 → 构建 → 打标签（`:v3.5` + `:latest`）→ 推送到阿里云 ACR。密码从 `.env` 读取，脚本可安全提交。`docker-compose.prod.yml`（Full 6 容器）和 `docker-compose.prod-lite.yml`（Lite 3 容器）使用 Registry 镜像，ECS 上无需编译前端。
- **架构加固**：Celery broker 默认值 `memory://`→`redis://` 防静默故障，SQLite `atexit` 连接回收，SSG 预渲染 `failOnError=false` 防单页崩溃中止全量构建。

### v3.4 (2026-06)
- **Docker 生产加固**：6 容器全健康检查体系（Redis ping / API curl / Worker celery ping / Beat pgrep），`depends_on condition: service_healthy` 确保启动顺序正确
- **非 root 运行**：Dockerfile `USER docstamp` + entrypoint 确保 volume 权限 + gunicorn `--pid /tmp` 避免 `/var/run` 权限问题
- **关键修复**：Celery worker 任务注册缺失（`include` 配置 → 14 个任务正确注册），`PYTHONPATH` 导入解析（`from config import Config` 在 Gunicorn `backend.app:app` 模式下失效）
- **构建优化**：pip `--root-user-action=ignore` 消除警告，`procps` 支持健康检查，`.dockerignore` 递归排除 `backend/output`
- **Full/Lite 双模式部署**：Lite 模式（3 容器/4 systemd 服务）适配 2C2G 低配 ECS，Celery 3 队列合并 + concurrency=2 + Beat 内嵌，预估内存 ~800MB；Full 模式（6 容器）保持独立队列隔离，适用于 4GB+ 生产环境。统一部署脚本 `docker-deploy.sh`（build/up/down/ps/logs/clean）
- **品牌定名**：产品名定为「鹊随金印」，全站标题/侧栏/页头/页脚统一应用，`.brand-title` CSS 品牌蓝渐变（`#4C7DF0`→`#2F4FB0`）印章浮雕质感
- **UI/UX 审查 (UI/UX Pro Max)**：侧栏子菜单增加点击切换（修复触摸设备不可达），ToolCard `transition: all`→`transition-[box-shadow,transform]`，`--color-text-tertiary` #757265→#706d60（对比度 3.9:1→4.69:1 WCAG AA）
- **移动端适配**：侧栏 <1024px 悬浮叠加模式（汉堡按钮 + 遮罩 + 点击关闭），导航项 h-10→min-h-[44px] 触摸目标
- **无障碍增强**：skip-to-content 键盘跳转链接，`prefers-reduced-motion: reduce` 全局禁用动画，所有交互元素 `cursor-pointer`

### v3.3 (2026-06)
- **使用统计仪表盘**：新增 `/status` 页面 + `/api/stats/overview` + `/api/stats/seed`，ECharts 可视化（柱状图/饼图/折线图），按模块/日/访客聚合
- **视觉精细化**：全局阴影增强（卡片/弹出/侧栏），`--color-text-tertiary` #8c8a7a→#757265（WCAG AA 4.5:1），侧栏导航激活态改为圆角背景填充，摘要卡片品牌色顶部强调线
- **baseline-ui 合规**：Sidebar `transition-all`→`transition-[width]`，移除 `tracking-wide`，骨架屏加载态，空状态一键操作按钮
- **Docker 修复**：`node:22-alpine`→`node:24-alpine`（npm 锁文件兼容），`COPY backend/ ./`→`COPY backend/ ./backend/`（保留目录结构），gunicorn `-b 0.0.0.0:5000`（容器端口可达），补 `pdfminer.six`
- **操作日志中间件**：`@app.before_request` / `@app.after_request` 自动记录所有 `/api/*` 调用至 `operation_logs`

### v3.2 (2026-06)
- **生产加固**：Gunicorn gthread + 动态 worker 数 + CORS 白名单 + MAX_CONTENT_LENGTH 兜底
- **速率限制**：新增 `rate_limit.py` 装饰器，15 个 blueprint 21 个上传接口分级限流
- **Celery 生产化**：Redis broker/backend 替代 memory:// + task_acks_late + reject_on_worker_lost
- **文件安全收紧**：MAX_FILE_SIZE 100MB→50MB，扩展名白名单补 webp/html/htm
- **Docker 多容器**：6 容器编排（API + Redis + 3×Worker + Beat）+ Systemd 安全加固 12 项
- **修复**：孤儿文件清理 + 双白名单同步 + docstring 修正

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
