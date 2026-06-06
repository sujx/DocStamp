# docStamp 开发难点与实现重点

> 记录开发过程中反复出现的错误模式和关键实现要点，避免踩坑。

---

## 一、后端开发难点

### 1. 代码修改后不生效（最高频问题）

**现象**：修改 `app.py` 后功能未变化，或出现 `NameError` 变量未定义。

**原因**：Flask 进程未重启。`python3 app.py &` 启动的进程不会自动重载代码。

**解决**：
```bash
# 方法 1：使用 manage.sh（已内置强制端口清理）
./manage.sh restart

# 方法 2：手动强制重启
fuser -k 5000/tcp && sleep 1 && cd backend && python3 app.py &

# 方法 3：开发时使用 Flask debug 模式（文件变更自动重载）
# 已默认开启 debug=True
```

**教训**：每次修改后端代码后必须重启。`./manage.sh restart` 现在会自动清理端口残留进程。

### 2. 变量名不匹配导致 500 错误

**现象**：API 返回 `500`，错误日志显示 `NameError: name 'xxx' is not defined`。

**根因**：批量替换代码时只改了定义处，没改引用处。

**案例**（format-docx 功能）：
```python
# ❌ 错误：变量名不一致
title = file.filename.rsplit(".", 1)[0]     # 定义 title
return jsonify({"title": original_name})     # 引用 original_name（不存在）

# ✅ 正确
title = file.filename.rsplit(".", 1)[0]
return jsonify({"title": title})
```

**防御**：修改涉及 JSON 响应的代码后，运行全文搜索检查变量名一致性：
```bash
grep -n '"title":\|"filename":' app.py
```

### 3. Pandoc 转换文件名问题

**现象**：MD 转 DOCX 输出文件名为 `None.docx`。

**原因**：`md_to_docx()` 函数原无返回值，`title = md_to_docx(...)` 得到 `None`。

**修复**：在 `converter.py` 中增加 `_extract_title()` 函数，从 MD 文件首行 `# 标题` 提取文件名。

### 4. GB/T 9704-2012 格式化字体不生效

**现象**：格式化后的 DOCX 中文字体未变化。

**原因**：`python-docx` 的 `run.font.name` 只设置西文字体，East-Asian 字体需通过 `w:rFonts` XML 元素设置 `w:eastAsia` 属性。

**关键代码**（`formatter.py:_set_run_font()`）：
```python
rFonts.set(qn("w:eastAsia"), font_name)   # 中文字体
rFonts.set(qn("w:ascii"), "Times New Roman")  # 西文字体
```

**验证方法**：不要相信 `run.font.name`（只返回西文字体），需要直接读 XML：
```python
rFonts = rPr.find(qn("w:rFonts"))
east_asia = rFonts.get(qn("w:eastAsia"))
```

### 5. Flask-CORS 与文件下载

**现象**：OPTIONS preflight 返回 200，但实际 POST 返回 405。

**原因**：旧版 Flask 进程未重启，路由定义未更新。

**教训**：修改路由定义（如新增 `methods=["POST"]`）后必须重启。

### 6. `send_file` + `@after_this_request` 文件清理时序

**关键**：`@after_this_request` 在响应完全发送后执行。不要在 `try` 块结尾提前清理文件 — 让 `after_this_request` 处理。

```python
# ✅ 正确：after_this_request 处理清理
@after_this_request
def _cleanup(response):
    _cleanup_files(filepath, output_path)
    return response

# ❌ 错误：在 finally 中清理（可能在发送前删除文件）
finally:
    _cleanup_files(filepath, output_path)
```

---

## 二、前端开发难点

### 1. Nuxt 代理不生效（最高频）

**现象**：前端请求 `/api/*` 返回 HTML 而非 JSON。

**根因**：Nuxt 4 的 `nitro.devProxy` 和 `vite.server.proxy` 在不同环境下行为不一致。

**最终解决方案**：不使用任何代理，前端直连后端。

```typescript
// plugins/axios.client.ts
import axios from "axios";
export default defineNuxtPlugin(() => {
  if (import.meta.dev) {
    axios.defaults.baseURL = "http://localhost:5000";
  }
});
```

**组件中使用 `fetch` 替代 `axios`（更可靠）**：
```typescript
const API = "http://localhost:5000";
const resp = await fetch(`${API}/api/convert/format-docx`, { method: "POST", body: fd });
```

### 2. 动态 import 在浏览器中失败（预览功能）

**现象**：`import("marked")` 返回 `undefined` 或无响应。

**原因**：Nuxt/Vite 生产构建时动态 import 的模块解析与开发环境不同。

**解决方案**：改为顶层静态 import：
```typescript
// ❌ 动态（不可靠）
const { marked } = await import("marked");

// ✅ 静态（可靠）
import { marked } from "marked";
```

### 3. 预览功能调试流程

**步骤化诊断**：
1. 先确认后端 `/api/preview` 是否正常（curl 测试）
2. 确认前端网络请求发送到了正确端口
3. 确认 JS 模块 import 成功（检查浏览器 Console 错误）
4. 用简化测试：`previewHtml = content`（跳过 marked）验证数据绑定正常
5. 逐步加回 marked → DOMPurify → highlight.js

### 4. 程序化下载不触发

**现象**：点击下载按钮无反应，无错误提示。

**原因**：`document.createElement("a")` 在部分浏览器中，若未添加到 DOM 则 `.click()` 不生效。

**必须的下载模式**：
```javascript
const a = document.createElement("a");
a.href = url;
a.download = filename;
document.body.appendChild(a);   // 必须：添加到 DOM
a.click();
setTimeout(() => {               // 延迟：确保下载开始后再清理
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}, 100);
```

### 5. `npx nuxt` 路径错误

**现象**：`Cannot resolve module "@nuxt/kit"`。

**原因**：当前工作目录不是 `frontend/`，`npx` 从项目根目录查找不到配置。

**解决**：始终在 frontend 目录执行 Nuxt 命令：
```bash
cd /home/sujx/Project/docStamp/frontend && npx nuxt generate
```

### 6. Google Fonts 被墙导致构建超时

**现象**：构建时反复重试 `fonts.google.com`，每次超时 10 秒。

**原因**：`@nuxt/ui` 依赖 `fontless` → `unifont`，后者尝试下载 Google Fonts 元数据。

**解决**（`nuxt.config.ts`）：
```typescript
export default defineNuxtConfig({
  ui: { fonts: false },     // 禁用 Google Fonts
  icon: { provider: "iconify" },  // 本地图标
});
```

### 7. `computed()` 在 `<script setup>` 外使用

**现象**：`useHead()` 或 `useI18n()` 报 "called without provide context"。

**原因**：在模块顶层（非 setup 上下文）调用了需要 Vue 上下文的 composable。

**修复**：用 `import.meta.client` 守卫：
```typescript
if (import.meta.client) {
  useHead({ ... });
}
```

### 8. UFormGroup 不存在

**现象**：`Failed to resolve component: UFormGroup`。

**原因**：Nuxt UI v4 将 `UFormGroup` 重命名为 `UFormField`。

**批量修复**：
```bash
sed -i 's/UFormGroup/UFormField/g' components/*.vue
```

---

## 三、部署与运维

### 1. systemd 服务文件需要正确的 WorkingDirectory

**关键**：Gunicorn 启动时必须在 backend 目录下，否则找不到模块。

```
[Service]
WorkingDirectory=/opt/docstamp/backend
ExecStart=/usr/bin/gunicorn -c gunicorn.conf.py app:app
```

### 2. 日志目录权限

**现象**：启动时 `Permission denied: '/var/log/docstamp/app.log'`。

**解决**：
```bash
mkdir -p /var/log/docstamp && chown docstamp:docstamp /var/log/docstamp
```

### 3. `./manage.sh restart` 可靠性（已修复）

**问题**：旧进程的 PID 文件和端口可能残留。

**修复内容**：
- `_start_backend()`：检查 PID 文件有效性（进程是否真的存在），清理僵死 PID
- `_stop_all()`：增加 `fuser -k 5000/tcp` 强制清理端口
- `_start_backend()`：启动前先 `_force_stop_port 5000`
- `_start_frontend()`：同样清理僵死 PID

---

## 四、baseline-ui 合规清单

### 必须修复（无障碍 + 安全）

| 约束 | 修复 |
|------|------|
| `h-screen` → `h-dvh` | 避免移动浏览器地址栏遮挡 |
| 图标按钮加 `aria-label` | 屏幕阅读器可访问 |
| 固定元素加 `safe-area-inset` | 刘海屏适配 |

### 批量修复（全项目）

| 约束 | 批量命令 |
|------|---------|
| 标题加 `text-balance` | `sed -i 's/class="text-2xl font-bold/class="text-2xl font-bold text-balance"/' **/*.vue` |
| 段落加 `text-pretty` | 同上，替换 `class="text-sm` |
| 硬编码颜色 → CSS 变量 | `#666` → `var(--color-text-secondary)` 等 |

### 禁止项

- 禁止 `transition: all` — 必须列出具体属性
- 禁止硬编码 `style="color: #xxx"` — 必须用 CSS 变量
- 禁止 `linear-gradient`（除非明确要求）
- 禁止修改 `letter-spacing`

---

## 五、快速诊断命令

```bash
# 后端端口占用检查
fuser 5000/tcp
lsof -i :5000

# 前端端口占用检查
lsof -i :8080

# 查看后端日志
tail -f /tmp/backend.log

# 后端手动测试
cd backend && python3 -c "
from app import app
with app.test_client() as c:
    r = c.get('/api/health')
    print(r.status_code, r.json)
"

# 前端构建验证
cd frontend && npx nuxt generate

# 清理所有缓存
find . -name "__pycache__" -exec rm -rf {} +
rm -rf frontend/.nuxt frontend/.output
```
