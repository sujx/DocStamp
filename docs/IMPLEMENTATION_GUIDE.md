# 全栈开发实施指南：Python Flask + Nuxt 3 + Docker

基于鹊随金印 (docStamp) v3.5 项目实际实践提炼。适用于单体工具类 Web 应用的架构设计、开发实施和生产部署。

---

## 1. 项目结构

```
myapp/
├── backend/
│   ├── app.py                  # Flask 工厂（蓝图注册 + SPA fallback + dotenv）
│   ├── config.py               # 集中配置（环境变量驱动）
│   ├── errors.py               # ErrorCode 枚举 + ServiceResult[T] + ServiceError
│   ├── schemas.py              # Pydantic v2 请求校验 DTO
│   ├── error_handler.py        # 全局异常拦截 + @validate_request + requestId
│   ├── json_logging.py         # JSON 结构化日志（TimedRotatingFileHandler）
│   ├── models.py               # 原始 SQL + WAL 模式 + schema_version
│   ├── cache.py                # Flask-Caching SimpleCache
│   ├── celery_app.py           # Celery 实例 + 3 队列 + Beat schedule
│   ├── gunicorn.conf.py        # 生产 WSGI 配置（gthread）
│   ├── ai.py                   # AI 功能（DeepSeek/OpenAI 兼容）
│   ├── mineru_bp.py            # 文档转 MD（MinerU API）
│   ├── blueprints/             # HTTP 路由层（每功能一个文件，~17 个）
│   ├── services/               # 业务逻辑层（纯函数，零 Flask 依赖）
│   ├── tasks/                  # Celery 异步任务（convert/pdf/office/maintenance）
│   ├── utils/
│   │   ├── base/file_helpers   # 文件操作工具
│   │   ├── file_security.py    # 上传校验（魔数+扩展名+大小）
│   │   ├── file_cleanup.py     # 7 天定时清理
│   │   ├── rate_limit.py       # IP 级限流
│   │   ├── retry.py            # 指数退避重试
│   │   └── crypto.py           # AES-256 Fernet 加密
│   └── tests/
├── frontend/
│   ├── nuxt.config.ts          # Nuxt 3 SSG + i18n + Nuxt UI v2
│   ├── tailwind.config.ts      # Tailwind v3 品牌色阶
│   ├── app.config.ts           # Nuxt UI v2 主题（primary: green）
│   ├── assets/css/main.css     # CSS 变量 + 品牌标题渐变
│   ├── composables/            # useApi / useTaskStream / useValidation / useAi / tools.config.ts
│   ├── api/modules/            # convert / pdf / office / watermark / tasks
│   ├── components/             # 业务组件（PascalCase）+ ui/ 原子组件
│   ├── layouts/default.vue     # 侧边导航壳
│   ├── pages/                  # 12 个路由页面（kebab-case）
│   └── i18n/locales/           # zh-CN.json / en.json
├── docker-compose.yml          # Full 模式 6 容器
├── docker-compose.lite.yml     # Lite 模式 3 容器
├── docker-compose.prod.yml     # Full 生产（ACR 镜像）
├── docker-compose.prod-lite.yml # Lite 生产（ACR 镜像）
├── Dockerfile                  # 多阶段构建
├── docker-deploy.sh            # Docker 统一管理脚本
├── docker-entrypoint.sh        # 容器入口
├── scripts/install.sh          # 裸机安装（--lite / --docker）
├── manage.sh                   # 开发管理
├── prod-start.sh               # 生产启动（含 .env 加载）
├── publish.sh                  # ACR 发布
├── SPEC.md                     # 设计规范
└── CLAUDE.md                   # AI 助手指令
```

### 分层原则

| 层 | 职责 | 约束 |
|----|------|------|
| **Blueprint** | HTTP 请求/响应 | ≤ 20 行，只做参数提取 → 调 service → 返回响应 |
| **Service** | 纯业务逻辑 | 零 Flask 依赖，全部返回 ServiceResult[T] |
| **Utils** | 通用基础设施 | 可被任意层引用 |
| **Tasks** | Celery 异步任务 | 更新 TaskRecord 进度 + SSE 推送 |

---

## 2. 后端架构 (Flask)

### 2.1 Flask 工厂 + dotenv 自动加载

```python
# app.py
import os

# 启动时自动加载 .env —— 无论怎么启动都有效
for _dotenv_path in (".env", "../.env"):
    if os.path.isfile(_dotenv_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(_dotenv_path)
        except ImportError:
            pass
        break

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    Babel(app, locale_selector=get_locale)
    CORS(app, origins=os.environ.get("CORS_ORIGINS", "localhost:8080").split(","))

    setup_json_logging(app)
    register_error_handlers(app)
    init_cache(app)
    init_db(app.config["TASK_DB_PATH"])
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 注册蓝图
    from blueprints.convert import convert_bp
    app.register_blueprint(convert_bp)
    # ... 17 个蓝图

    # SPA fallback（生产模式提供前端静态文件）
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path): ...

    return app
```

### 2.2 延迟导入——裸机部署的关键

**规则**：第三方包不在模块顶层 `import`。函数体内按需导入。

```python
# ❌ 顶层 — 裸机没装 requests 就崩
import requests

def call_api():
    requests.post(...)

# ✅ 函数内 — 不调这个端点就不需要 requests
def call_api():
    import requests
    requests.post(...)
```

`ai.py` 和 `mineru_bp.py` 均采用此模式。`python-dotenv` 用 try/except 容错。

### 2.3 环境变量始终从 Config 读

```python
# ❌ 模块级 os.environ —— 只在 import 时读一次
API_KEY = os.environ.get("DOCSTAMP_MINERU_API_KEY", "")

# ✅ 从 Config 类读 —— 每请求读一次
from config import Config
key = Config.MINERU_API_KEY
```

### 2.4 @validate_request 行为

`@validate_request(body=Schema)` 把校验后的 Pydantic 对象作为 `body=` 关键字传入函数——**不是 `request.parsed_body`**。

```python
@ai_bp.route("/api/v1/ai/correct", methods=["POST"])
@validate_request(body=AiTextSchema)
def ai_correct(body: AiTextSchema):
    text = body.text  # ✅ 正确
```

### 2.5 ServiceResult[T]

所有 Service 函数返回 `ServiceResult[T]`：

```python
def convert(path: str) -> ServiceResult[dict]:
    try:
        data = do_work(path)
        return ServiceResult.ok(data)
    except ValueError as e:
        return ServiceResult.fail(ErrorCode.VALIDATION_ERROR, str(e))
```

需要中断调用栈时抛 `ServiceError(code, msg, status)`——全局 handler 自动转为 JSON。

### 2.6 配置管理

```python
# config.py
class Config:
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "output"))
    MAX_CONTENT_LENGTH = 110 * 1024 * 1024
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Celery — 生产默认 Redis，不是 memory://
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")

    # AI
    AI_API_KEY = os.environ.get("DOCSTAMP_DEEPSEEK_API_KEY", "")
    AI_API_URL = os.environ.get("AI_API_URL", "https://api.deepseek.com/chat/completions")
    AI_MODEL = os.environ.get("AI_MODEL", "deepseek-v4-flash")
    MINERU_API_KEY = os.environ.get("DOCSTAMP_MINERU_API_KEY", "")
```

### 2.7 AI 功能集成

通过环境变量配置厂商，不配 Key 时静默降级：

```python
# ai.py
API_KEY = Config.AI_API_KEY
API_URL = Config.AI_API_URL
API_MODEL = Config.AI_MODEL

def _call(prompt, system="", temperature=0) -> str | None:
    if not API_KEY:
        return None                        # 降级
    cache_key = f"ai:{sha256_hash(prompt)}"
    cached = cache.get(cache_key)
    if cached:
        return cached                       # 1h 缓存

    import requests
    resp = requests.post(API_URL, json={
        "model": API_MODEL,
        "messages": [{"role":"system","content":system}, {"role":"user","content":prompt}],
    })
    result = resp.json()["choices"][0]["message"]["content"]
    cache.set(cache_key, result, timeout=3600)
    return result
```

支持 OpenAI / DeepSeek / Ollama / 硅基流动等所有兼容厂商。

### 2.8 MinerU 文档转 MD

异步提交 → 轮询 → 下载 ZIP → 提取 .md：

```python
@mineru_bp.route("/api/v1/doc-to-md", methods=["POST"])
def doc_to_md():
    # 1. 保存上传文件
    _, filepath = save_upload(file, ALLOWED_EXTS, Config.UPLOAD_FOLDER)

    # 2. 构建公网 URL（DOCSTAMP_PUBLIC_URL > host_url）
    public_base = os.environ.get("DOCSTAMP_PUBLIC_URL", request.host_url)
    file_url = f"{public_base}/api/v1/download/{filename}"

    # 3. 提交 MinerU → 轮询 → 提取
    import requests
    task = requests.post(MINERU_URL, json={"url": file_url, "model_version": "vlm"}).json()
    task_id = task["data"]["task_id"]

    for _ in range(60):
        time.sleep(3)
        status = requests.get(f"{MINERU_URL}/{task_id}").json()
        if status["data"]["state"] == "done":
            zip_url = status["data"]["full_zip_url"]
            md = extract_md_from_zip(requests.get(zip_url).content)
            cache.set(cache_key, md, timeout=86400)
            return jsonify({"data": {"markdown": md}})
```

---

## 3. 前端架构 (Nuxt 3)

### 3.1 Nuxt 配置 —— SSG 已启用

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [["@nuxt/ui", { safelistColors: ["green"] }], "@nuxtjs/i18n", "@nuxt/icon"],
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  devServer: { port: 8080, host: "0.0.0.0" },

  runtimeConfig: { public: { apiBase: "/api/v1" } },

  ssr: true,  // SSG 已启用（从 v3.4 开始，之前为 false）

  nitro: {
    prerender: {
      crawlLinks: true, concurrency: 1,    // 2GB 机器安全设置
      failOnError: false,                   // 单页失败不中止构建
    },
  },

  i18n: {
    strategy: "no_prefix", defaultLocale: "zh-CN",
    lazy: false,
    bundle: { optimizeTranslationDirective: false },
    detectBrowserLanguage: { useCookie: true, cookieKey: "docstamp_lang", fallbackLocale: "zh-CN" },
  },
});
```

### 3.2 Tailwind CSS 设计系统

颜色、阴影、圆角全部在 `tailwind.config.ts` 中定义为 Tailwind token。`<style scoped>` 中的 CSS 变量仅用于动态场景（hover 切换、computed values）。组件模板中优先用 Tailwind 类。

```typescript
// tailwind.config.ts
colors: {
  primary: { 700: "#008a3d", ... },  // Nuxt UI v2 primary 别名
  brand: { 700: "#008a3d", soft: "rgba(0,138,61,0.08)", ... },
  page: "#f9f7e8", surface: "#ffffff", muted: "#f4f2e4",
},
textColor: { primary: "#1a1a1a", secondary: "#5c5c5c", tertiary: "#706d60" },
borderColor: { default: "#e8e6d8", subtle: "#f0efe5" },
boxShadow: { card: "...", elevated: "...", sidebar: "..." },
```

**品牌标题**：CSS 渐变类 `.brand-title`（gold→green 金绿渐变 + 双方向 text-shadow 浮雕效果）。

### 3.3 工具配置单一数据源

`composables/tools.config.ts` 是所有工具定义的唯一来源。Sidebar 和 Dashboard 从此读取，新增工具只改这一个文件：

```typescript
export const TOOLS: ToolDef[] = [
  { key: "md2docx", to: "/md-to-docx", icon: "i-heroicons-arrow-down-tray",
    label: "tabs.md2docx", desc: "md2docx.description", order: 2 },
  { key: "doc-to-md", to: "/doc-to-md", icon: "i-heroicons-document-arrow-down",
    label: "tabs.docToMd", desc: "docToMd.description", order: 3 },
  // ... 12 tools total
]
```

### 3.4 布局系统

侧栏 (240px ↔ 64px) + 右侧内容区。移动端 (<1024px) 悬浮叠加模式（汉堡按钮 + 遮罩 + 点击关闭）。状态通过 `localStorage("sidebar_collapsed")` 持久化。`provide("sidebarWidth")` 控制内容区 margin。

### 3.5 Nuxt UI v2 组件用法

```html
<!-- UTabs -->
<UTabs :items="tabs">
  <template #slot1><ComponentA /></template>
  <template #slot2><ComponentB /></template>
</UTabs>

<!-- UFormGroup + UInput -->
<UFormGroup :label="$t('label')">
  <UInput v-model="value" size="sm" />
</UFormGroup>

<!-- UButton -->
<UButton color="primary" :loading="loading" @click="submit">
  <UIcon name="i-heroicons-sparkles" class="w-4 h-4 mr-1.5" />
  {{ $t("submit") }}
</UButton>
```

### 3.6 Composables

| Composable | 功能 |
|-----------|------|
| `useAi` | AI 纠错/分类/文件名/去噪 |
| `useTaskStream` | SSE 进度监听 |
| `useValidation` | Vuelidate 封装 |
| `useApi` | 通用 API 封装 |
| `useDownload` | Blob 下载 |

### 3.7 关键规范

- 禁用 `transition: all`，必须列出具体属性
- SVG 图标使用 Heroicons（`i-heroicons-*`），禁止 emoji
- 所有 UI 文本使用 `$t()`，禁止硬编码
- 触摸目标 ≥ 44px（`min-h-[44px]`）
- Sidebar 子菜单同时支持 hover + click（触摸设备兼容）
- `prefers-reduced-motion: reduce` 全局禁用动画

---

## 4. Docker 部署

### 4.1 一镜像多容器

同一镜像通过不同 `command:` 启动不同容器：

```
registry.cn-wulanchabu.aliyuncs.com/grepsu/docstamp:latest
  ├── api:         gunicorn ...
  ├── celery-convert: celery -Q convert_queue
  ├── celery-pdf:     celery -Q pdf_queue
  ├── celery-office:  celery -Q office_queue
  └── celery-beat:    celery beat

Lite 模式（3 容器）：
  ├── api:      gunicorn --workers 2
  └── celery:   celery -Q all -B
```

### 4.2 四套 Compose

| 文件 | 用途 | 镜像来源 |
|------|------|------|
| `docker-compose.yml` | 本地开发 Full | `build: .` |
| `docker-compose.lite.yml` | 本地开发 Lite | `build: .` |
| `docker-compose.prod.yml` | ECS 生产 Full | ACR 镜像 |
| `docker-compose.prod-lite.yml` | ECS 生产 Lite | ACR 镜像 |

### 4.3 ACR 发布流程

```bash
./publish.sh          # 构建 → 打标签 → 推送
# ECS 上
scp docker-compose.prod.yml .env root@ECS:/opt/docstamp/
ssh root@ECS 'cd /opt/docstamp && docker compose -f docker-compose.prod.yml pull && up -d'
```

密码从 `.env` 读取，脚本本身可安全提交。

### 4.4 关键 Dockerfile 决策

- `node:22-alpine` 构建前端，`python:3.12-slim-bookworm` 运行时
- `npm ci --legacy-peer-deps`（处理 @vuelidate/core vu2/3 冲突）
- `--no-install-recommends` + `apt-get autoremove` 减小镜像
- `NODE_OPTIONS` 通过 `ARG NODE_HEAP` 按需设置（默认 2GB）
- 非 root 用户 `docstamp` + entrypoint 处理 volume 权限
- HEALTHCHECK 不在 Dockerfile 中统一定义（API 的 curl 对 Celery 无效），在 compose 中分 service 设置

---

## 5. 裸机部署

### 5.1 install.sh 四种模式

```bash
sudo bash scripts/install.sh install           # 仅 API systemd 服务
sudo bash scripts/install.sh install --lite    # API + Celery + Beat（2C2G）
sudo bash scripts/install.sh install --docker  # Docker Full
sudo bash scripts/install.sh install --docker-lite  # Docker Lite
```

### 5.2 消息代理自动检测

```bash
_install_broker() {
    case "$PKG_MGR" in
        apt) apt-get install -y redis ;;       # Debian/Ubuntu
        dnf|yum) $PKG_MGR install -y valkey ;; # RHEL 10+ / RockyLinux 10
    esac
    systemctl enable --now "$broker"
}
```

### 5.3 三种启动路径的环境变量

| 路径 | 来源 |
|------|------|
| Docker | compose `${VAR}` 注入 |
| `./manage.sh prod` | prod-start.sh `source .env` + python-dotenv |
| systemd | `EnvironmentFile=/etc/docstamp/env.conf` + python-dotenv |

`python-dotenv` 在 `app.py` 启动时自动加载是最后兜底。

### 5.4 构建 OOM 防护

`install.sh` 自动检测内存并设 Node 堆为 75% RAM（下限 1.5GB）。`Dockerfile` 通过 `ARG NODE_HEAP` 可覆盖。SSG 预渲染 `concurrency=1` 串行避免峰值。

---

## 6. 开发工作流

### 6.1 manage.sh

```bash
./manage.sh start      # Flask :5000 + Nuxt :8080
./manage.sh prod       # Gunicorn 单端口 + 静态文件
./manage.sh test       # pytest
./manage.sh lite       # Docker Lite 一键启动
```

### 6.2 测试策略

每个 API 端点 4 类测试：200 / 缺参数 400 / 类型错误 422 / 不存在 404。

---

## 7. 已知模式与反模式

| ✅ 做 | ❌ 不做 |
|------|--------|
| `from config import Config` 读环境变量 | 模块级 `os.environ.get()` |
| 第三方包函数内延迟导入 | 模块顶层 `import requests` |
| 中文 prompt 用单引号字符串 | prompt 用双引号——中文引号 `"` 冲突 |
| `.env` 不提交，`.env.example` 提交 | `.env` 提交到 git |
| Celery broker 默认 Redis | broker 默认 `memory://` |
| `@validate_request(body=Schema)` 接受 `body` 参数 | 用 `request.parsed_body` |
| 一个镜像多容器（command 覆盖） | 每个容器单独构建 |
| `tools.config.ts` 单一数据源 | 侧栏/仪表盘各自硬编码导航 |
| npm ci + lockfile 同步 | lockfile 不同步导致 Docker 构建失败 |

---

## 参考

- [docStamp SPEC.md](../SPEC.md) — 完整设计规范
- [docStamp CODE_STANDARDS_ANALYSIS.md](CODE_STANDARDS_ANALYSIS.md) — 项目最佳实践
- [Nuxt 3 官方文档](https://nuxt.com/docs)
- [DeepSeek API 文档](https://api-docs.deepseek.com)
- [MinerU API 文档](https://mineru.net/apiManage/docs)
