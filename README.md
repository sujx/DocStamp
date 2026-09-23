# 鹊随金印 (docStamp) — 文档处理工具箱

一站式文档处理 Web 应用：10 项文档工具 + 1 个使用统计页，中英双语，即开即用，无需注册。

## 功能

仪表盘（`/`）之外共 11 个页面，按下表顺序排列（与侧边导航一致）：

| # | 功能 | 路由 | 说明 |
|---|------|------|------|
| 1 | **MD 转公文** | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX |
| 2 | **格式规范** | `/format-docx` | DOCX 按 GB/T 9704-2012 格式化 |
| 3 | **RSS 探测** | `/rss-detect` | 输入 URL，自动发现 RSS/Atom 订阅地址 |
| 4 | **属性修改** | `/properties` | 元数据修改 + 清理（双 Tab） |
| 5 | **Excel 合并** | `/excel-merge` | 合并 .xlsx/.csv（同结构） |
| 6 | **文件组装** | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 7 | **打印分组** | `/print-split` | 按批次拆分 PDF |
| 8 | **PDF 编辑** | `/pdf-editor` | 删除/插入/重排页面 |
| 9 | **调整 PDF** | `/pdf-tools` | PDF 转文本 + 压缩 + 页码页眉页脚 |
| 10 | **PDF 合并** | `/pdf-merge` | 合并多个 PDF，拖拽排序 |
| 11 | **使用统计** | `/status` | 模块调用量 + 访客统计（ECharts） |

另有 4 个面板子页（page-decorate / pdf-compress / pdf-to-text / metadata-clean）被对应工具页内嵌引用。

## 技术栈

| 层 | 技术 |
|------|------|
| **后端框架** | Python 3.12 + Flask 3 + Pydantic v2 |
| **后端依赖** | Flask-CORS / Flask-Babel / Flask-Caching / python-docx / openpyxl / python-pptx / img2pdf / pypdf / Pillow / reportlab / WeasyPrint / markdown / bleach / pdfminer.six / requests / python-dotenv / cryptography |
| **文档工具链** | pandoc / poppler-utils（容器内已安装） |
| **前端框架** | Nuxt 3.15.4 (SPA) + Nuxt UI v2 + Tailwind CSS v3 |
| **国际化** | @nuxtjs/i18n v9（zh-CN / en） |
| **部署** | Docker Compose（单容器）+ Gunicorn gthread + Nginx 反代 |

## 快速开始

### 本地开发

```bash
# 安装后端依赖（或用 poetry install）
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    flask-caching python-docx openpyxl python-pptx img2pdf pypdf Pillow reportlab \
    gunicorn pydantic cryptography weasyprint markdown bleach pdfminer.six \
    requests python-dotenv

# 安装前端依赖
cd ../frontend && npm install

# 启动开发模式（Flask :5000 + Nuxt :8080 HMR）
cd .. && ./manage.sh start
```

### Docker 部署（单容器，2C2G 推荐）

```bash
# 1. 复制环境变量并填写配置
cp .env.example .env

# 2. 构建并启动
docker compose up -d --build

# 3. 查看状态
docker compose ps

# 4. 配置 nginx 反向代理到 127.0.0.1:5000
```

或使用管理脚本：

```bash
./manage.sh docker-up     # 构建并启动
./manage.sh docker-down   # 停止
```

### ACR 发布（可选）

```bash
./publish.sh          # 推送到阿里云 ACR
./publish.sh v3.6     # 指定版本号
```

## 项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂（蓝图注册 + SPA fallback）
│   ├── config.py               # 统一配置
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult[T] + ServiceError
│   ├── schemas.py              # Pydantic v2 请求 DTO（JSON body 端点）
│   ├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
│   ├── json_logging.py         # JSON 结构化日志（30 天轮转）
│   ├── models.py               # OperationLog 审计/统计（原始 SQL）
│   ├── cache.py                # Flask-Caching（限流 + 统计缓存）
│   ├── gunicorn.conf.py        # Gunicorn gthread 生产配置（含每日清理 on_starting）
│   ├── blueprints/             # HTTP 路由层（16 个，每个功能 1 文件）
│   ├── services/               # 业务逻辑层（纯函数，全返回 ServiceResult[T]）
│   └── utils/
│       ├── base/               # file_helpers
│       ├── file_security.py    # 三层文件校验（大小/扩展名/魔数）
│       ├── file_cleanup.py     # 每日临时文件清理（gunicorn 启动的守护线程）
│       ├── rate_limit.py       # IP 级别 API 限流装饰器
│       ├── retry.py            # @retry_on_failure 重试装饰器
│       └── crypto.py           # AES-256 Fernet 字段加密
├── frontend/                   # Nuxt 3 SPA
│   ├── composables/            # tools.config / useValidation / useApi / useDownload / useApiError
│   ├── components/             # 业务组件 + ui/ 原子组件
│   ├── pages/                  # 16 个路由页面
│   └── i18n/locales/           # zh-CN / en
├── docker-compose.yml          # 单容器编排（api）
├── Dockerfile                  # 多阶段构建（node:22-alpine + python:3.12-slim）
├── docker-entrypoint.sh        # Docker 入口（运行时目录 + volume 权限）
├── manage.sh                   # 开发/部署管理脚本
├── publish.sh                  # ACR 镜像发布
├── SPEC.md                     # 详细设计规范
└── AGENTS.md                   # AI 助手指令（Qoder 标准）
```

## 架构特点

- **分层解耦** — Blueprint (HTTP) → Service (业务) → Utils (通用)，Service 层零 Flask 依赖
- **全局异常拦截** — 所有异常 → 标准化 JSON `{code, msg, requestId}`
- **Pydantic v2 校验** — `@validate_request` 装饰器自动校验请求参数
- **ServiceResult[T]** — 所有 Service 函数强制 success/failure 分支处理
- **临时文件清理** — gunicorn `on_starting` 在 master 进程启动守护线程，每日清理 7 天以上的上传/产物文件
- **速率限制** — 双层防御（Nginx 粗粒度 + 应用层 `@rate_limit` IP 级），上传接口按负载分级限流
- **文件安全** — 三层校验（100MB 大小 / 扩展名白名单 / 魔数签名）+ 文件名 XSS 净化
- **API 版本化** — 全部响应带 `X-API-Version` 头
- **安全加固** — Docker 非 root 用户运行 + 容器健康检查 + 资源限制
- **操作审计** — OperationLog 全量记录
- **JSON 日志** — 结构化日志 + 每日轮转 + 30 天保留

## 部署模式

| 模式 | 命令 | 容器/进程 | 推荐配置 |
|------|------|:---:|:---:|
| 开发 | `./manage.sh start` | 2 进程 | 本地开发 |
| Docker | `docker compose up -d` | 1 容器 | 2C2G 服务器 |

## 系统要求

| 组件 | 要求 |
|------|:---:|
| 内存 | 2GB+ |
| CPU | 2 核 |
| Docker | 容器部署需要 |
| pandoc / poppler-utils | Dockerfile 内已安装；本地开发需自装 |
