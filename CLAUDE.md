# CLAUDE.md — docStamp 项目规范

## 项目概述

docStamp 是一站式文档处理工具箱，15 大功能模块。Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 前端，Flask REST API 后端。绿鹃品牌色系（`#008A3D` + `#F9F7E8`），仪表盘 + 侧边导航 + 多页面路由，中英文双语。

**单体工具定位**：无用户系统、无认证、无 AI — 即开即用，随用随走。

## 项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂 (<70 行，仅蓝图注册 + SPA fallback)
│   ├── config.py               # 集中配置
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult[T] + ServiceError
│   ├── schemas.py              # Pydantic v2 请求 DTO (15+ Schema)
│   ├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
│   ├── json_logging.py         # JSON 结构化日志 + TimedRotatingFileHandler (30天)
│   ├── models.py               # TaskRecord + OperationLog + BaseCRUD (原始 SQL)
│   ├── cache.py                # Flask-Caching SimpleCache
│   ├── cel.py                  # Celery (memory:// broker, 3 队列: convert/pdf/office)
│   ├── config_validators.py    # 配置校验 (URL/端口/CORS)
│   ├── gunicorn.conf.py        # 生产: bind 0.0.0.0:5000, workers=4
│   ├── blueprints/             # HTTP 路由层 (只做请求/响应，每功能一个文件)
│   │   ├── convert.py          # /api/convert, /api/preview, /api/stats
│   │   ├── download.py         # /api/download, /api/health, /api/tasks/*
│   │   ├── properties_bp.py    # /api/properties/*
│   │   ├── img2pdf_bp.py       # /api/img2pdf
│   │   ├── pdf2img_bp.py       # /api/pdf2img
│   │   ├── print_split_bp.py   # /api/print-split/*
│   │   ├── watermark_bp.py     # /api/watermark/*
│   │   ├── pdf_editor_bp.py    # /api/pdf-editor/*
│   │   ├── excel_merge_bp.py   # /api/excel-merge
│   │   ├── pdf_to_text_bp.py   # /api/pdf-to-text
│   │   ├── pdf_merge_bp.py     # /api/pdf-merge
│   │   ├── pdf_compress_bp.py  # /api/pdf-compress
│   │   ├── metadata_clean_bp.py # /api/metadata-clean
│   │   ├── format_convert_bp.py # /api/convert/format
│   │   ├── page_decorate_bp.py # /api/page-decorate
│   │   └── image_process_bp.py # /api/image-process
│   ├── services/               # 业务逻辑层 (纯函数，全部返回 ServiceResult[T])
│   │   ├── converter.py        # MD → DOCX (Pandoc)
│   │   ├── formatter.py        # GB/T 9704-2012 格式化
│   │   ├── watermark.py        # 水印添加/去除
│   │   ├── pdf_editor.py       # PDF 删除/插入/重排
│   │   ├── excel_merger.py     # Excel/CSV 合并
│   │   ├── img2pdf_handler.py  # 图片 → PDF
│   │   ├── pdf_to_images.py    # PDF → 图片 (pdftoppm)
│   │   ├── pdf_to_text.py      # PDF → 文本 (pdfminer)
│   │   ├── print_split.py      # PDF 打印分组
│   │   ├── properties.py       # Office 属性读写
│   │   ├── pdf_merger.py       # PDF 合并 (pypdf)
│   │   ├── pdf_compressor.py   # PDF 压缩
│   │   ├── metadata_cleaner.py # 元数据清理
│   │   ├── format_converter.py # 格式互转 (LibreOffice/WeasyPrint)
│   │   ├── page_decorator.py   # 页码页眉页脚 (reportlab)
│   │   └── image_processor.py  # 图片处理 (Pillow)
│   ├── tasks/                  # Celery 异步任务
│   │   ├── convert.py          # convert_queue
│   │   ├── pdf.py              # pdf_queue (8 tasks)
│   │   ├── office.py           # office_queue (3 tasks)
│   │   └── maintenance.py      # Beat: 定时清理临时文件
│   ├── utils/                  # 通用工具
│   │   ├── base/               # file_helpers / validators
│   │   ├── file_security.py    # 魔数校验 + 大小限制 + 扩展名白名单
│   │   ├── file_cleanup.py     # 7 天定时清理
│   │   ├── retry.py            # @retry_on_failure (2 次重试 → 降级)
│   │   └── crypto.py           # AES-256 Fernet 字段加密
│   └── tests/
├── frontend/                   # Nuxt 3 SPA
│   ├── nuxt.config.ts          # splitChunks:true, @nuxtjs/i18n v9, ssr:false
│   ├── tailwind.config.ts      # Tailwind v3 品牌色阶
│   ├── app.config.ts           # Nuxt UI v2: primary:green, gray:cool
│   ├── assets/css/main.css     # CSS 变量 (品牌 token)
│   ├── composables/            # useValidation / useTaskStream / useApi / useDownload
│   ├── components/ui/          # 原子组件 (ButtonPrimary / CardBase / ProgressBar)
│   ├── layouts/default.vue     # 侧边导航壳
│   ├── pages/                  # 16 页面 (仪表盘 + 15 工具)
│   ├── components/             # 15+ 业务组件
│   └── locales/                # zh-CN / en
├── docs/
│   └── vireolens-ui-spec.css   # VireoLens 通用 UI 设计参考
├── manage.sh                   # dev/prod 管理 (start/stop/restart/prod/test)
├── prod-start.sh               # 生产一键启动
├── Dockerfile
└── SPEC.md
```

## 开发环境

### 启动

```bash
# 开发模式 (Flask :5000 + Nuxt :8080)
./manage.sh start

# 生产模式 (Gunicorn :5000 单端口，含前端静态)
./manage.sh prod

# 停止
./manage.sh stop
```

### 测试

```bash
./manage.sh test              # 后端 pytest
cd frontend && npm run build  # 前端构建验证
```

## 核心规范

### Service 层规范

所有 Service 函数必须返回 `ServiceResult[T]`，禁止裸 raise：

```python
from errors import ServiceResult, ErrorCode

def my_service(path: str) -> ServiceResult[dict]:
    try:
        data = do_work(path)
        return ServiceResult.ok(data)
    except ValueError as e:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, str(e))
```

**错误码**: 使用 `ErrorCode` 枚举（20+ 预定义错误码），不硬编码字符串。
**异常**: 需要中断流程时 raise `ServiceError(code, msg, status)`，由全局 handler 自动捕获。

### API 层规范

- Blueprint 函数不超过 15 行，只做参数提取 → 调用 service → 返回响应
- 所有请求参数通过 Pydantic Schema 校验：`@validate_request(body=MdConvertSchema)`
- 全局异常拦截器自动处理所有异常 → 标准化 JSON: `{code, msg, requestId}`
- 每个请求自动分配 `requestId`（12 位 hex），通过 `X-Request-Id` 响应头返回

### 前端规范

- UI 组件：Nuxt UI v2 (`UFormGroup`, `UButton`, `UInput`, `USelect`, `UTabs`)
- 图标：Heroicons (`i-heroicons-*`)，本地模式
- 所有 UI 文本用 `$t()`，禁止硬编码
- 颜色统一通过 CSS 变量（`var(--color-*)`），禁止 inline hex
- 禁止 `transition: all`，仅对 opacity/transform/border-color 过渡
- 表单校验：Vuelidate (`useFormValidation` composable)
- 异步进度：SSE (`useTaskStream` composable)
- 数字时钟：rem/vw/clamp 响应式，`role="timer"` + `aria-label`

### 设计 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-700` | `#008a3d` | 品牌主色 |
| `--color-page` | `#f9f7e8` | 页面底色 |
| `--color-surface` | `#ffffff` | 卡片白色 |
| `--color-text-primary` | `#1a1a1a` | 正文 |
| `--color-text-secondary` | `#5c5c5c` | 辅助 |
| `--color-border-default` | `#e8e6d8` | 默认边框 |

### 命名规范

| 层级 | 规范 | 示例 |
|------|------|------|
| 后端 Blueprint | `<feature>_bp.py` | `convert.py`, `watermark_bp.py` |
| 后端 Service | 单数 + `_service` (或原名) | `converter.py`, `watermark.py` |
| 后端 Model | 小写 | `models.py` |
| 前端组件 | PascalCase | `DigitalClock.vue`, `ProgressBar.vue` |
| 前端 composables | `useXxx.ts` | `useValidation.ts`, `useTaskStream.ts` |
| 前端 pages | kebab-case 路由 | `md-to-docx.vue`, `file-assembly.vue` |

## 版本信息

| 组件 | 版本 | 备注 |
|------|------|------|
| Nuxt | 3.15.4 | 锁死版本 |
| @nuxt/ui | ^2.21 | Nuxt UI v2 |
| @nuxtjs/i18n | ^9.5 | i18n v9 |
| @nuxt/icon | ^1.10 | Icon v1 |
| Tailwind CSS | v3 | tailwind.config.ts |
| Flask | ^3.1 | — |
| Pydantic | ^2.13 | 参数校验 |
| Celery | ^5.6 | 异步任务 (dev: memory://) |

## 常见命令

```bash
# 清理
find . -name "__pycache__" -exec rm -rf {} +
rm -rf frontend/.nuxt frontend/.output

# 依赖安装
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    python-docx openpyxl python-pptx markdown bleach img2pdf pypdf Pillow \
    reportlab gunicorn pydantic celery flask-caching cryptography weasyprint \
    pdfminer.six
cd ../frontend && npm install

# 前端 lint
cd frontend && npm run lint && npm run format
```
