# 鹊随金印 (docStamp) — 文档处理工具箱

一站式文档处理 Web 应用，13 大功能模块。即开即用，无需注册。

## 功能

| # | 功能 | 路由 | 说明 |
|---|------|------|------|
| 1 | **MD 转公文** | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX + AI 纠错 |
| 2 | **文档转 MD** | `/doc-to-md` | PDF/Word/PPT/图片 → Markdown（MinerU）|
| 3 | **水印管理** | `/watermark` | 添加/去除文字和图片水印 |
| 4 | **属性修改** | `/properties` | 元数据修改 + 清理（双 Tab） |
| 5 | **Excel 合并** | `/excel-merge` | 合并 .xlsx/.csv（同结构） |
| 6 | **格式规范** | `/format-docx` | DOCX 按 GB/T 9704-2012 格式化 |
| 7 | **文件组装** | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 8 | **打印分组** | `/print-split` | 按批次拆分 PDF |
| 9 | **PDF 编辑** | `/pdf-editor` | 删除/插入/重排页面 |
| 10 | **调整 PDF** | `/pdf-tools` | PDF 转文本 + 压缩 + 页码页眉页脚 |
| 11 | **PDF 合并** | `/pdf-merge` | 合并多个 PDF，拖拽排序 |
| 12 | **使用统计** | `/status` | 模块调用量 + 访客统计（ECharts） |

### AI 功能

| 功能 | 说明 | 接入方式 |
|------|------|------|
| 文本纠错 | MD 转公文前自动纠正错别字和标点 | DeepSeek v4 Flash |
| 格式识别 | 自动检测正式公文，建议 GB/T 格式 | DeepSeek v4 Flash |
| 智能文件名 | 根据文档内容生成中文文件名 | DeepSeek v4 Flash |
| PDF 去噪 | 自动去除页眉页脚、水印残留 | DeepSeek v4 Flash |
| 文档转 MD | PDF/Word/PPT → Markdown | MinerU API |

配置 `DOCSTAMP_DEEPSEEK_API_KEY` + `DOCSTAMP_MINERU_API_KEY` 即可启用。
支持 OpenAI / Ollama / 硅基流动等任何兼容 API（`AI_API_URL` + `AI_MODEL`）。

## 技术栈

| 层 | 技术 |
|------|------|
| **后端框架** | Python Flask + Pydantic v2 + Flask-CORS + Flask-Babel + Flask-Caching |
| **异步任务** | Celery（Redis broker）+ 3 队列 + SSE 进度推送 |
| **文档处理** | pandoc / pypdf / Pillow / reportlab / pdfminer.six / python-docx / openpyxl |
| **AI** | DeepSeek v4 Flash + MinerU API（可选，不配 Key 自动降级） |
| **前端框架** | Nuxt 3.15.4 (SPA) + Nuxt UI v2 + Tailwind CSS v3 + Flat Design + Plus Jakarta Sans |
| **国际化** | @nuxtjs/i18n v9（zh-CN / en） |
| **部署** | Gunicorn gthread + Nginx + Docker Compose + Systemd |

## 快速开始

### 本地开发

```bash
# 安装后端依赖
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    flask-caching python-docx openpyxl python-pptx markdown bleach img2pdf \
    pypdf Pillow reportlab gunicorn pydantic celery redis cryptography \
    pdfminer.six

# 安装前端依赖
cd ../frontend && npm install

# 启动开发模式（Flask :5000 + Nuxt :8080 HMR）
cd .. && ./manage.sh start
```

### Docker 本地构建部署（无需 ACR）

```bash
# Lite 模式 — 本地 Dockerfile 构建，3 容器，适合单服务器
docker compose -f docker-compose.local.yml up -d

# 查看状态
docker compose -f docker-compose.local.yml ps
```

### Docker 生产部署（ACR 镜像）

```bash
# Full 模式（6 容器，4GB+ 推荐）
./docker-deploy.sh up

# Lite 模式（3 容器，2C2G 推荐）
./docker-deploy.sh up --lite

# 查看状态 + 健康检查
./docker-deploy.sh ps --lite
```

### 裸机 Systemd 部署

```bash
# Lite 模式（2C2G ECS 推荐）— 消息代理 + API + Celery + Beat 一键安装
sudo bash scripts/install.sh install --lite

# Full 模式 — 仅 API，Celery 需额外部署
sudo bash scripts/install.sh install
```

> **RHEL 10 / RockyLinux 10**：Redis 已被 Valkey 替代，install.sh 自动检测并安装对应包。

### ACR 发布（推荐生产部署）

```bash
# 本地构建 → 推送 → ECS 拉取（ECS 无需编译前端）
./publish.sh          # 推送到阿里云 ACR（密码从 .env 读取）
./publish.sh v3.6     # 指定版本号

# ECS 上
scp docker-compose.prod.yml .env root@你的ECS:/opt/docstamp/
ssh root@你的ECS 'cd /opt/docstamp && docker compose -f docker-compose.prod.yml up -d'
```

## 项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂（蓝图注册 + SPA fallback）
│   ├── config.py               # 统一配置
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult[T] + ServiceError
│   ├── schemas.py              # Pydantic v2 请求 DTO（15+ Schema）
│   ├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
│   ├── json_logging.py         # JSON 结构化日志（30 天轮转）
│   ├── models.py               # TaskRecord + OperationLog（原始 SQL）
│   ├── cache.py                # Flask-Caching（限流 + 统计缓存）
│   ├── celery_app.py           # Celery（Redis broker，3 队列）
│   ├── gunicorn.conf.py        # Gunicorn gthread 生产配置
│   ├── blueprints/             # HTTP 路由层（15 个功能 × 1 文件）
│   ├── services/               # 业务逻辑层（纯函数，全返回 ServiceResult[T]）
│   ├── tasks/                  # Celery 异步任务（convert / pdf / office / maintenance）
│   └── utils/
│       ├── base/               # file_helpers / validators
│       ├── file_security.py    # 三层文件校验（大小/扩展名/魔数）
│       ├── rate_limit.py       # IP 级别 API 限流装饰器
│       ├── retry.py            # @retry_on_failure 重试装饰器
│       └── crypto.py           # AES-256 Fernet 字段加密
├── frontend/                   # Nuxt 3 SPA
│   ├── composables/            # tools.config / useValidation / useTaskStream / useApi / useDownload / useAi
│   ├── components/ui/          # 原子组件（CardBase / SkeletonBlock）
│   ├── pages/                  # 16 个路由页面（仪表盘 + 15 工具）
│   └── locales/                # zh-CN / en
├── deploy/
│   ├── docstamp.service        # Systemd 服务（12 项安全加固）
│   └── env.conf                # 生产环境变量模板
├── docker-compose.local.yml    # 3 容器 Lite 编排（本地构建，无需 ACR）
├── docker-compose.prod-lite.yml # 3 容器 Lite 编排（ACR 镜像）
├── docker-compose.prod.yml     # 6 容器 Full 编排（ACR 镜像）
├── docker-compose.yml          # 6 容器 Full 编排（本地构建）
├── Dockerfile                  # 多阶段构建（node:24-alpine + python:3.12-slim）
├── docker-entrypoint.sh        # Docker 入口（运行时目录 + volume 权限）
├── manage.sh                   # 开发/生产管理脚本
├── prod-start.sh               # 生产一键启动
├── SPEC.md                     # 详细设计规范
└── CLAUDE.md                   # AI 助手指令
```

## 架构特点

- **分层解耦** — Blueprint (HTTP) → Service (业务) → Utils (通用)，Service 层零 Flask 依赖
- **全局异常拦截** — 所有异常 → 标准化 JSON `{code, msg, requestId}`
- **Pydantic v2 校验** — `@validate_request` 装饰器自动校验请求参数
- **ServiceResult[T]** — 所有 Service 函数强制 success/failure 分支处理
- **异步任务** — Celery 3 队列 + TaskRecord 生命周期追踪 + SSE 实时进度
- **速率限制** — 双层防御（Nginx 粗粒度 + 应用层 `@rate_limit` IP 级），上传接口按负载分级限流
- **文件安全** — 三层校验（50MB 大小 / 扩展名白名单 / 魔数签名）+ 定时清理
- **安全加固** — Systemd `NoNewPrivileges` + `ProtectSystem=strict` + `PrivateTmp` 等 12 项
- **操作审计** — TaskRecord + OperationLog 全量记录
- **JSON 日志** — 结构化日志 + 每日轮转 + 30 天保留

## 部署模式对比

| 模式 | 命令 | 容器/进程 | 推荐配置 |
|------|------|:---:|:---:|
| 开发 | `./manage.sh start` | 2 进程 | 本地开发 |
| Docker Local | `docker compose -f docker-compose.local.yml up -d` | 3 容器 | 单服务器，无需 ACR |
| Docker Full | `docker compose up -d` | 6 容器 | 4GB+ 服务器 |
| Docker Lite | `docker compose -f docker-compose.lite.yml up -d` | 3 容器 | 2C2G ECS |
| Docker Prod Lite | `docker compose -f docker-compose.prod-lite.yml up -d` | 3 容器 | 2C2G ECS（ACR 镜像）|
| 裸机 Lite | `sudo bash scripts/install.sh install --lite` | 4 systemd 服务 | 2C2G ECS |
| 裸机 Prod | `./manage.sh prod` | 1 进程 | 已有外部 Redis/Celery |

## 系统要求

| 组件 | Full 模式 | Lite 模式 |
|------|:---:|:---:|
| 内存 | 4GB+ | 2GB |
| CPU | 4 核+ | 2 核 |
| Redis | 需要 | 需要 |
| pandoc / poppler-utils | 需要 | 需要 |
| Docker (可选) | 推荐 | 推荐 |
