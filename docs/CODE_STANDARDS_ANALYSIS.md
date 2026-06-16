# docStamp 最佳实践（2026-06 积累）

基于项目实际开发过程中踩过的坑和形成的一致性约定，非外部规范套用。

---

## 一、后端

### 1.1 延迟导入——裸机部署的前提

**规则**：第三方包不要放在模块顶层 `import`。在函数体内按需导入。

```python
# ❌ 模块顶层 — 裸机没装 requests 就崩
import requests

def call_api():
    requests.post(...)

# ✅ 函数内延迟 — 不调用这个端点不需要这个包
def call_api():
    import requests
    requests.post(...)
```

**背景**：Docker 镜像装全了依赖，但 `./manage.sh prod` 用的是系统 Python。`ai.py` 和 `mineru_bp.py` 都踩过这个坑。

### 1.2 环境变量从 Config 读，不从 os.environ 读

```python
# ❌ 模块级 os.environ — 只在 import 时读一次
API_KEY = os.environ.get("DOCSTAMP_MINERU_API_KEY", "")

# ✅ 从 Config 类读 — 每次调用时读
from config import Config
key = Config.MINERU_API_KEY
```

**背景**：`mineru_bp.py` 最初用 `os.environ` 读 Key，Docker 容器重建后 `.env` 变量变了但模块已加载，Key 死活读不到。

### 1.3 Blueprint 函数接受 Pydantic Schema 参数

```python
# ✅ @validate_request(body=Schema) 自动传入解析后的 body 参数
@ai_bp.route("/api/v1/ai/correct", methods=["POST"])
@validate_request(body=AiTextSchema)
def ai_correct(body: AiTextSchema):
    text = body.text  # 不是 request.parsed_body
```

**背景**：最初用 `request.parsed_body`，但 `@validate_request` 的实际行为是把 Pydantic 对象作为 `body=` 关键字参数传入函数。

### 1.4 ServiceResult 可以简化

当前的 `ServiceResult.ok()` / `ServiceResult.fail()` 包装可以通过全局异常处理器进一步精简。如果异常处理器已经覆盖了 `ServiceError`，service 层可以直接抛异常，不必每个函数自己 try/except 包装。

### 1.5 Prompt 设计——单引号字符串避免转义

DeepSeek/MinerU 的 prompt 中文引号 `"` 和 Python 字符串定界符 `"` 冲突。用单引号字符串：

```python
# ✅ 单引号 — 中文引号不需要转义
system = (
    '你是 PDF 文本清理专家。去除以下噪音：\n'
    '1. 页眉（如"第 X 页"）\n'
    '2. 页脚（如"© 2025 xxx"）\n'
)
```

---

## 二、前端

### 2.1 工具配置单一数据源

`composables/tools.config.ts` 是唯一工具注册表。新增工具只改这一个文件，Sidebar 和 Dashboard 自动同步。

```ts
// tools.config.ts — 加一行即可
{ key: "new-tool", to: "/new-tool", icon: "i-heroicons-sparkles",
  label: "tabs.newTool", desc: "newTool.description", order: 5 },
```

### 2.2 禁用 `transition: all`

项目 CLAUDE.md 明确禁止。用具体属性列表：

```html
<!-- ❌ -->
class="transition-all duration-200"

<!-- ✅ -->
class="transition-[box-shadow,transform] duration-200"
```

### 2.3 禁用 emoji 做图标

全部用 Heroicons（`i-heroicons-*`），通过 `@nuxt/icon` 本地模式加载。

### 2.4 移动端侧栏——hover 不靠谱

Sidebar 子菜单 `@mouseenter`/`@mouseleave` 在触摸设备不可用。必须同时支持 `@click` 切换。

### 2.5 UTabs 组件用法（Nuxt UI v2）

```html
<UTabs :items="tabs">
  <template #slot1><ComponentA /></template>
  <template #slot2><ComponentB /></template>
</UTabs>
```

每个 tab 内容放在对应的 `#slotName` 中。slot 名在 `items` 数组的 `slot` 字段定义。

### 2.6 构建 OOM——不要硬编码堆大小

```bash
# ❌ 写死 4GB — 2GB 机器上被内核 kill
NODE_OPTIONS="--max-old-space-size=4096"

# ✅ 根据实际内存动态设置（install.sh 已实现）
heap_mb=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 * 3 / 4 ))
```

---

## 三、Docker

### 3.1 一个镜像，多容器——command 覆盖

Full 和 Lite 模式**共享同一个镜像**。区别在 compose 文件的 `command:` 字段，不是 Dockerfile。

```
docker-compose.prod.yml:    6 个容器 = 1 api + 1 redis + 3 celery + 1 beat
docker-compose.prod-lite.yml: 3 个容器 = 1 api + 1 redis + 1 celery(all)
```

### 3.2 .env 不进镜像

`.env` 只在 `docker-compose.yml` 中通过 `${VAR:-default}` 注入容器。不要把 `.env` COPY 进镜像。

### 3.3 npm ci 需要 lockfile 同步

Docker 内 `npm ci` 要求 `package-lock.json` 和 `package.json` 完全一致。本地改过 `package.json` 后，先 `npm install --legacy-peer-deps` 更新 lockfile，再提交。

### 3.4 HEALTHCHECK 分别定义

Dockerfile 里不放通用 HEALTHCHECK——API 的 `curl /health` 对 Celery 容器无效。在 `docker-compose.yml` 里每个 service 单独设置。

---

## 四、部署

### 4.1 三种启动路径要一致

| 路径 | 环境变量来源 |
|------|------------|
| Docker | compose `${VAR}` 注入 |
| `./manage.sh prod` | `prod-start.sh` source `.env` + python-dotenv |
| systemd | `EnvironmentFile=/etc/docstamp/env.conf` + python-dotenv |

`python-dotenv` 在 `app.py` 启动时自动加载，是最后兜底。

### 4.2 Valkey 替代 Redis（RHEL 10+）

`install.sh` 自动检测发行版：apt→redis，dnf→valkey。Celery broker URL 不变（都走 6379 端口）。

### 4.3 publish.sh 流程

```
本地构建 → docker tag → docker push → ECS scp compose + .env → docker compose pull → up -d
```

密码从 `.env` 读取，脚本本身可安全提交。

---

## 五、SPEC.md 维护约定

- 版本条目格式：`### vX.Y (YYYY-MM)` → 每条改动以 `- **关键词**：说明` 开头
- 功能表 13 项，每次增删工具同步更新
- 设计 Token 表不动——CSS 变量在 `<style scoped>` 中仍然合法
