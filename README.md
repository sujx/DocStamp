# docStamp — 文档处理工具箱

一站式文档处理 Web 应用，集成 Markdown 转公文、PDF 编辑、水印管理、格式互转、图片处理、元数据清理等 15 大功能。

## 功能

| # | 功能 | 路由 | 说明 |
|---|------|------|------|
| 1 | **MD 转公文** | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX，实时预览 |
| 2 | **属性修改** | `/properties` | 修改 `.docx/.xlsx/.pptx` 元数据，批量/统一时间 |
| 3 | **文件组装** | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 4 | **打印分组** | `/print-split` | PDF 按批次拆分，暂停/继续/终止 |
| 5 | **水印管理** | `/watermark` | 添加/去除文字和图片水印 |
| 6 | **PDF 编辑** | `/pdf-editor` | 删除/插入/重排页面，缩略图预览 |
| 7 | **Excel 合并** | `/excel-merge` | 合并 `.xlsx/.csv`，相同结构 |
| 8 | **格式规范** | `/format-docx` | DOCX 按 GB/T 9704-2012 格式化 |
| 9 | **PDF 转文本** | `/pdf-to-text` | 提取 PDF 文本内容 |
| 10 | **PDF 合并** | `/pdf-merge` | 合并多个 PDF，拖拽排序 |
| 11 | **PDF 压缩** | `/pdf-compress` | 三级压缩（轻度/中度/深度） |
| 12 | **格式互转** | `/format-convert` | DOCX/HTML → PDF |
| 13 | **元数据清理** | `/metadata-clean` | 清除文档元数据，保护隐私 |
| 14 | **页码页眉页脚** | `/page-decorate` | 添加页码/页眉/页脚到 PDF |
| 15 | **图片处理** | `/image-process` | 缩放/裁剪/格式转换/压缩图片 |

## 技术栈

- **后端**: Python Flask + Pydantic v2 + Celery + pypdf + Pillow + reportlab + pdfminer + Pandoc + poppler-utils + LibreOffice + WeasyPrint
- **前端**: Nuxt 3 + Nuxt UI v2 + Tailwind CSS v3 + @nuxtjs/i18n v9
- **部署**: Gunicorn (生产) / Flask dev server (开发) + Docker Compose

## 快速开始

```bash
# 安装后端依赖
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    python-docx openpyxl python-pptx markdown bleach img2pdf pypdf Pillow \
    reportlab gunicorn pydantic celery flask-caching cryptography weasyprint \
    pdfminer.six

# 安装前端依赖
cd ../frontend && npm install

# 开发模式（双端口）
cd .. && ./manage.sh start

# 生产模式（单端口 :5000）
./manage.sh prod

# 运行测试
./manage.sh test
```

## 项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂 (<70 行，仅蓝图注册)
│   ├── config.py               # 统一配置
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult + ServiceError
│   ├── schemas.py              # Pydantic v2 请求 DTO
│   ├── error_handler.py        # 全局异常拦截 + @validate_request
│   ├── json_logging.py         # JSON 结构化日志 (30 天轮转)
│   ├── models.py               # TaskRecord + OperationLog (原始 SQL)
│   ├── cache.py                # Flask-Caching SimpleCache
│   ├── cel.py                  # Celery (memory:// broker, 3 队列)
│   ├── config_validators.py    # 启动时配置校验
│   ├── gunicorn.conf.py        # Gunicorn 生产配置
│   ├── blueprints/             # HTTP 路由层（每功能一个文件，共 14 个）
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
│   ├── services/               # 业务逻辑层（全部返回 ServiceResult[T]）
│   │   ├── converter.py        # MD → DOCX (Pandoc)
│   │   ├── formatter.py        # GB/T 9704-2012 格式化
│   │   ├── watermark.py        # 水印添加/去除
│   │   ├── pdf_editor.py       # PDF 删除/插入/重排
│   │   ├── excel_merger.py     # Excel/CSV 合并
│   │   ├── img2pdf_handler.py  # 图片 → PDF
│   │   ├── pdf_to_images.py    # PDF → 图片 (pdftoppm)
│   │   ├── pdf_to_text.py      # PDF → 文本 (pdfminer)
│   │   ├── print_split.py      # 打印分组
│   │   ├── properties.py       # Office 属性读写
│   │   ├── pdf_merger.py       # PDF 合并 (pypdf)
│   │   ├── pdf_compressor.py   # PDF 压缩
│   │   ├── metadata_cleaner.py # 元数据清理
│   │   ├── format_converter.py # 格式互转 (LibreOffice/WeasyPrint)
│   │   ├── page_decorator.py   # 页码页眉页脚 (reportlab)
│   │   └── image_processor.py  # 图片处理 (Pillow)
│   ├── tasks/                  # Celery 异步任务
│   │   ├── convert.py          # convert_queue
│   │   ├── pdf.py              # pdf_queue
│   │   ├── office.py           # office_queue
│   │   └── maintenance.py      # 定时清理
│   ├── utils/                  # 通用工具
│   │   ├── base/               # 文件处理、校验
│   │   ├── file_security.py    # 魔数校验、大小限制
│   │   ├── file_cleanup.py     # 定时文件清理
│   │   ├── retry.py            # 重试装饰器
│   │   └── crypto.py           # AES-256 字段加密
│   └── tests/
├── frontend/                   # Nuxt 3 SPA
│   ├── nuxt.config.ts          # splitChunks: true
│   ├── tailwind.config.ts      # Tailwind v3 品牌色阶
│   ├── app.config.ts           # Nuxt UI v2 主题
│   ├── assets/css/main.css     # CSS 变量 (品牌 token)
│   ├── composables/            # useValidation / useTaskStream / useApi / useDownload
│   ├── components/ui/          # 原子组件 (ButtonPrimary / CardBase / ProgressBar)
│   ├── layouts/default.vue     # 侧边导航壳
│   ├── pages/                  # 16 个路由页面（仪表盘 + 15 工具）
│   ├── components/             # 15+ 业务组件
│   └── locales/                # zh-CN / en
├── docs/
│   └── vireolens-ui-spec.css   # VireoLens 通用 UI 设计规范
├── manage.sh                   # 开发/生产管理
├── prod-start.sh               # 生产一键启动
├── Dockerfile
├── SPEC.md                     # 设计规范
└── CLAUDE.md                   # AI 助手指令
```

## 开发/生产模式

| 模式 | 命令 | 端口 | 说明 |
|------|------|------|------|
| 开发 | `./manage.sh start` | :5000 + :8080 | Flask dev + Nuxt dev (HMR) |
| 生产 | `./manage.sh prod` | :5000 (单端口) | Gunicorn 4 workers + 前端静态 |

生产模式通过 Flask 的 SPA fallback 路由直接提供 Nuxt 构建输出，无需独立 Node.js 进程。

## 架构特点

- **分层解耦**: Blueprint (HTTP) → Service (业务) → Utils (通用)
- **全局异常拦截**: 所有异常 → 标准化 JSON `{code, msg, requestId}`
- **Pydantic v2 校验**: 15+ Schema 覆盖全部请求参数
- **结构化返回**: `ServiceResult[T]` 强制 success/failure 分支处理
- **异步任务**: Celery 3 队列 (convert/pdf/office) + SSE 实时进度
- **文件安全**: 三层校验 (大小/扩展名白名单/魔数签名)
- **操作审计**: TaskRecord + OperationLog 全量记录
- **JSON 日志**: 结构化日志 + 每日轮转 + 30 天保留

## 系统要求

- Python 3.12+
- Node.js 22+
- Pandoc, poppler-utils, libreoffice-core (DOCX→PDF 转换)
