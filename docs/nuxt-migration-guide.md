# 前端框架迁移指南：传统 Vue UI → Nuxt + Nuxt UI + Tailwind CSS

> 基于 docStamp 项目从 Vue CLI + Buefy/Bulma 迁移到 Nuxt 4 + Nuxt UI v4 的实战经验总结。

---

## 一、前置评估

### 1.1 确认迁移收益

| 原框架 | 问题 | Nuxt 方案 |
|--------|------|-----------|
| Vue CLI + Webpack | 构建慢、配置复杂 | Vite 原生支持，开发秒启动 |
| Buefy / Bulma | 组件少、扩展难 | Nuxt UI v4 组件丰富 |
| 自写 CSS token | 维护成本高 | Tailwind v4 `@theme` 统一管理 |
| vue-i18n 独立安装 | 配置繁琐 | `@nuxtjs/i18n` 模块化集成 |
| MDI 图标 | 依赖 Google Fonts | Heroicons 本地 SVG，无外部依赖 |

### 1.2 评估工作量

| 因素 | 低 | 中 | 高 |
|------|:--:|:--:|:--:|
| 页面数量 | <5 | 5-15 | >15 |
| 组件复杂度 | 纯展示 | 表单交互 | 拖拽/Canvas/富文本 |
| 是否有自定义组件库 | 无 | 少量 | 大量封装 |
| 国际化程度 | 单语言 | 双语 | 多语言 |
| **docStamp 实际** | — | **15 组件、10 页面、双语** | **拖拽排序、Canvas 预览** |

**docStamp 耗时参考**：约 4-6 小时（含调试），实际修改约 20 个文件。

---

## 二、迁移步骤

### 阶段 1：环境搭建（约 30 分钟）

#### Step 1.1：初始化 Nuxt 项目

不要用 `npx nuxi init`（会覆盖现有目录）。在原前端目录内手动创建：

```bash
# 保留需要迁移的资产
mkdir -p /tmp/project-save
cp -r src/i18n/locales /tmp/project-save/
cp public/logo.svg public/favicon.ico /tmp/project-save/

# 清理旧项目文件（保留 node_modules 可加速）
rm -rf src/ public/ babel.config.js vue.config.js
```

#### Step 1.2：更新 package.json

```json
{
  "type": "module",
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt generate"
  },
  "dependencies": {
    "nuxt": "^4.4",
    "@nuxt/ui": "^4.8",
    "@nuxt/icon": "^2.2",
    "@nuxtjs/i18n": "^10.4",
    "axios": "^1.7"
  }
}
```

> **⚠️ 注意**：务必先查 npm 确认最新版本号。`@nuxtjs/i18n` v10 匹配 Nuxt 4，v8 匹配 Nuxt 3。

#### Step 1.3：安装并验证

```bash
rm -rf node_modules package-lock.json  # 全新安装
npm install
npx nuxt build  # 空项目应成功
```

#### Step 1.4：创建目录结构

```
frontend/
├── nuxt.config.ts
├── app.config.ts
├── assets/css/main.css          # Tailwind 入口
├── plugins/axios.client.ts      # API 代理
├── composables/useDownload.ts   # 共用逻辑
├── layouts/default.vue          # 页面壳
├── pages/                       # 路由页面
├── components/                  # 组件
├── i18n/locales/                # 翻译文件
└── public/                      # 静态资源
```

---

### 阶段 2：配置文件（约 20 分钟）

#### Step 2.1：nuxt.config.ts

```ts
export default defineNuxtConfig({
  modules: ["@nuxt/ui", "@nuxtjs/i18n", "@nuxt/icon"],

  ssr: false,  // SPA 模式（Flask 托管静态文件）

  devServer: { port: 8080, host: "0.0.0.0" },

  // 开发代理（可选 — 建议用 plugins/axios 直连）
  vite: {
    server: {
      proxy: { "/api": { target: "http://localhost:5000", changeOrigin: true } }
    }
  },

  // 图标本地化（避免 Google Fonts 被墙）
  icon: { provider: "iconify" },

  // 禁用 Google Fonts（unifont → fontless → @nuxt/ui）
  ui: { fonts: false },

  // i18n 配置
  i18n: {
    strategy: "no_prefix",
    defaultLocale: "zh-CN",
    locales: [
      { code: "zh-CN", file: "zh-CN.json" },
      { code: "en", file: "en.json" },
    ],
    lazy: true,
    detectBrowserLanguage: { useCookie: true, fallbackLocale: "zh-CN" },
  },
});
```

> **⚠️ 重点关注**：
> - `ui.fonts: false` — **必须设置**。中国大陆无法访问 Google Fonts，不关闭会导致构建超时
> - `icon.provider: "iconify"` — 使用本地图标 API，避免外部下载
> - `ssr: false` — 如果用 Flask/Django 托管，设为 SPA 模式

#### Step 2.2：app.config.ts（Nuxt UI 主题色）

```ts
export default defineAppConfig({
  ui: {
    primary: "brand",     // 自定义品牌色名
    gray: "neutral",
    colors: {
      brand: {
        50: "#f0fdf4", 100: "#dcfce7", ..., 700: "#008a3d", 800: "#00662b"
      }
    }
  }
});
```

> **⚠️**：Nuxt UI v4 中 `color="primary"` 映射到 `app.config.ts` 的 `primary` 字段。必须定义完整的 50-950 色阶。

#### Step 2.3：assets/css/main.css（设计 Token）

```css
@import "tailwindcss";
@import "@nuxt/ui";

@theme {
  --color-page: #f9f7e8;
  --color-surface: #ffffff;
  --color-muted: #f4f2e4;
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #5c5c5c;
  --color-text-tertiary: #8c8a7a;
  --color-border-default: #e8e6d8;
  --shadow-card: 0 1px 3px rgba(0,0,0,.04);
}

body {
  background-color: var(--color-page);
  color: var(--color-text-primary);
}
```

> **⚠️**：Tailwind v4 使用 `@theme` 而不是 `tailwind.config.ts`。所有设计 Token 在此集中定义。

#### Step 2.4：API 代理插件

```ts
// plugins/axios.client.ts
import axios from "axios";

export default defineNuxtPlugin(() => {
  if (import.meta.dev) {
    axios.defaults.baseURL = "http://localhost:5000";  // 直连后端
  }
});
```

> **⚠️ 重点问题**：Nuxt 4 的 `nitro.devProxy` 和 `vite.server.proxy` 在部分环境下**不可靠**。最稳妥的方案是 axios 插件直连后端。文件名用 `.client.ts` 后缀确保仅在客户端加载。

---

### 阶段 3：组件迁移（核心工作，约 2-4 小时）

#### Step 3.1：组件映射表

| Buefy / Bulma | Nuxt UI v4 |
|---------------|------------|
| `b-button` | `UButton`（props: `color`, `variant`, `size`, `block`） |
| `b-input` | `UInput` |
| `b-select` | `USelect`（`:options` 数组格式 `[{value,label}]`） |
| `b-tabs` / `b-tab-item` | `UTabs`（`:items` 数组） |
| `b-field` | `UFormField` |
| `b-upload` | 原生 `<input type="file">` + Tailwind 样式 |
| `b-icon` | `UIcon`（`name="i-heroicons-*"`） |
| `b-message` | `UAlert` |
| `b-progress` | `UProgress` |
| `b-radio` | `URadioGroup` + `URadio` |
| `b-numberinput` | `UInput type="number"` |
| `b-datetimepicker` | `UInput type="datetime-local"` |
| `b-tag` | 自定义 `<span>` 或 `UBadge` |
| `$buefy.toast.open()` | `useToast().add()` |
| `columns` / `column` | `grid grid-cols-2 gap-4` |
| `mt-4` / `p-4` 等 | Tailwind 同名工具类 |
| `is-primary` / `is-success` | `color="primary"` / `color="success"` |

#### Step 3.2：图标迁移

```bash
# Buefy/MDI → Heroicons 对照表
file-document-edit-outline → i-heroicons-document-text
image-multiple-outline     → i-heroicons-photo
printer                    → i-heroicons-printer
water                      → i-heroicons-beaker
file-pdf-box               → i-heroicons-document
file-excel-outline         → i-heroicons-table-cells
upload / cloud-upload      → i-heroicons-arrow-up-tray
chevron-up / chevron-down  → i-heroicons-chevron-up / down
close                      → i-heroicons-x-mark
drag                       → i-heroicons-arrows-pointing-out
check-circle               → i-heroicons-check-circle
```

#### Step 3.3：CSS 迁移模式

```html
<!-- ❌ 旧：Buefy/Bulma 硬编码 -->
<div class="columns">
  <div class="column is-half">
    <b-field label="标题">
      <b-input v-model="val" />
    </b-field>
  </div>
</div>
<p style="color: #666; background: #fff;">文字</p>

<!-- ✅ 新：Tailwind + CSS 变量 -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
  <UFormField label="标题">
    <UInput v-model="val" />
  </UFormField>
</div>
<p class="text-[var(--color-text-secondary)] bg-[var(--color-surface)]">文字</p>
```

> **⚠️ 规则**：**禁止** `style="color: #666"` 硬编码。所有颜色必须通过 CSS 变量引用，便于主题切换。

#### Step 3.4：i18n 迁移

```json
// ✅ locale 文件格式不变，直接复用
{
  "common": {
    "upload": "上传文件",
    "download": "下载",
    "reset": "重新选择"
  }
}
```

```ts
// ❌ 旧：vue-i18n standalone
import { useI18n } from "vue-i18n";
const { t } = useI18n();

// ✅ 新：@nuxtjs/i18n（API 完全兼容）
const { t } = useI18n();   // 完全相同
$t("common.upload")        // 模板中完全相同
```

> **⚠️**：Nuxt i18n 模块默认从 `i18n/locales/` 读取（不是 `src/i18n/locales/`）。注意调整目录。

---

### 阶段 4：架构变更（约 1 小时）

#### Step 4.1：单页标签 → 多页面路由

```
❌ 旧架构：单页 Tabs
pages/index.vue  ← 所有标签在里面

✅ 新架构：多页面 + 侧边导航
pages/index.vue          ← 仪表盘
pages/properties.vue     ← 属性修改
pages/file-assembly.vue  ← 文件组装
...
layouts/default.vue      ← 侧边导航壳
```

#### Step 4.2：创建路由页面

```vue
<!-- pages/properties.vue -->
<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <PageHeader />          <!-- 返回仪表盘链接 -->
    <PropertiesTab />       <!-- 迁移后的功能组件 -->
  </div>
</template>
```

#### Step 4.3：可复用组件提取

```ts
// composables/useDownload.ts  — 所有组件的 Blob 下载逻辑
export function useDownload() {
  function downloadBlob(data, filename, msg) { ... }
  function showError(e) { ... }
  return { downloadBlob, showError };
}
```

---

### 阶段 5：部署适配（约 30 分钟）

#### Step 5.1：构建命令变更

```bash
# ❌ 旧
npm run build       # vue-cli-service build → dist/

# ✅ 新
npx nuxt generate   # → .output/public/
```

#### Step 5.2：后端静态路径

```python
# ❌ 旧：app.py
STATIC_FOLDER = "../frontend/dist"

# ✅ 新
STATIC_FOLDER = "../frontend/.output/public"
```

#### Step 5.3：Dockerfile

```dockerfile
# ❌ 旧
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# ✅ 新
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public
```

#### Step 5.4：manage.sh

```bash
# ❌ 旧
npm run serve    # vue-cli-service serve

# ✅ 新
npm run dev      # nuxt dev
```

---

## 三、常见坑与解决方案

### 🔴 严重问题

| 问题 | 现象 | 解决 |
|------|------|------|
| **Google Fonts 被墙** | 构建超时，`unifont` 重试 `fonts.google.com` 失败 | `ui: { fonts: false }` |
| **Nuxt 代理不生效** | `GET /api/xxx` 返回 HTML 而非 JSON | `plugins/axios.client.ts` 直连 `localhost:5000` |
| **动态 import 预览失败** | `import("marked")` 在浏览器返回 undefined | 改为顶层静态 `import { marked } from "marked"` |
| **npx 解析错误目录** | `npx nuxt build` 报 `@nuxt/kit` 找不到 | `cd frontend && npx nuxt build`，确保在项目根执行 |
| **版本不匹配** | `@nuxtjs/i18n@^5` 不存在 | `@nuxtjs/i18n@^10` 匹配 Nuxt 4 |
| **UFormGroup 不存在** | `Failed to resolve component: UFormGroup` | Nuxt UI v4 改为 `UFormField` |

### 🟡 中等问题

| 问题 | 解决 |
|------|------|
| 图标名称差异（MDI → Heroicons） | 建立对照表，批量替换 |
| `b-upload` 无直接等价物 | 用原生 `<input type="file">` + Tailwind 手写拖放区 |
| SSR 水合错误 | `ssr: false` 全局关闭 |
| `useToast()` 在服务端无上下文 | `if (import.meta.client)` 守卫 |
| Bulma 工具类 `mt-4`/`p-4` | Tailwind 有同名类，基本兼容，但 `columns` 需改为 `grid` |
| 中文环境 `node_modules/.bin/nuxt` 缺失 | `npx nuxt` 代替 |

### 🟢 优化建议

| 建议 | 说明 |
|------|------|
| 优先迁移简单组件 | AppHeader → AppFooter → FileUploader → 再迁移复杂组件 |
| 先用服务端预览 | 客户端 marked/dompurify 模块加载复杂，先用 `/api/preview` 验证基础功能 |
| 保留原项目备份 | 不确定时并行运行新旧版本对比 |
| 渐进式替换 | 不必一次性全部迁移，新功能用 Nuxt，旧模块逐步替换 |

---

## 四、验证清单

- [ ] `npm run dev` 启动无报错
- [ ] `npx nuxt generate` 构建成功
- [ ] 所有路由页面可访问
- [ ] 侧边导航切换正常
- [ ] 每个功能：上传 → 配置 → 处理 → 下载
- [ ] 语言切换（中/英）各页面翻译正常
- [ ] 后端测试全部通过
- [ ] Chrome DevTools 无红色报错
- [ ] 移动端响应式布局正常

---

## 五、docStamp 实际迁移数据

| 指标 | 数值 |
|------|------|
| 迁移组件数 | 15 |
| 新建页面数 | 10 |
| 修改配置数 | 4（nuxt.config, app.config, main.css, package.json） |
| 删除文件数 | 8（vue.config, babel.config, SkeletonTab, 旧 wrapper） |
| 新增依赖 | 6（nuxt, @nuxt/ui, @nuxt/icon, @nuxtjs/i18n, marked, dompurify） |
| 耗时 | ~5 小时 |
| 构建体积 | 5.3 MB → 2.6 MB（gzip 1.2 MB → 662 KB） |

---

## 六、baseline-ui 合规清单

迁移完成后，使用 `/baseline-ui` 审查并修复常见的 UI 问题。以下是实际修复经验总结：

### 6.1 Critical（无障碍 + 安全 — 必须修）

| 约束 | 常见违规 | 修复方法 |
|------|---------|---------|
| `h-screen` → `h-dvh` | `layouts/default.vue` 等布局文件使用 `min-h-screen` | 全局替换为 `min-h-dvh`（避免移动浏览器地址栏遮挡） |
| `aria-label` 图标按钮 | `<UButton icon="..." />` 无标签 | 添加 `:aria-label="$t('common.removeFile')"` |
| `safe-area-inset` | 固定定位元素（Sidebar、Header）无安全区 | 添加 `pt-[env(safe-area-inset-top)]`、`pl-[env(safe-area-inset-left)]` 等 |

```bash
# 批量修复 safe-area
sed -i 's/class="fixed top-0/class="fixed top-0 pt-[env(safe-area-inset-top)]"/' components/*.vue
```

### 6.2 Pervasive（全项目 — 批量处理）

| 约束 | 影响范围 | 批量命令 |
|------|---------|---------|
| `text-balance` 标题 | 所有 h1/h2/h3 | `sed -i 's/class="text-2xl font-bold/class="text-2xl font-bold text-balance"/' **/*.vue` |
| `text-pretty` 段落 | 所有描述 `<p>` | `sed -i 's/class="text-sm mb-5/class="text-sm mb-5 text-pretty"/' **/*.vue` |
| 硬编码颜色 | 22 处 `#666`/`#333`/`#e8e6d8` | 替换为 `var(--color-*-)`，保留 Python 脚本批量处理 |

```python
# 批量颜色替换脚本
replacements = [
    ("style=\"color: #666;\"", ":style=\"{ color: 'var(--color-text-secondary)' }\""),
    ("style=\"background: #fff;\"", ":style=\"{ backgroundColor: 'var(--color-surface)' }\""),
    ("style=\"border-color: #e8e6d8;\"", ":style=\"{ borderColor: 'var(--color-border-default)' }\""),
    ("style=\"color: #008a3d;\"", ":style=\"{ color: 'var(--color-brand-700)' }\""),
]
```

### 6.3 单点修复

| 文件 | 问题 | 修复 |
|------|------|------|
| `MdToDocxTab.vue` | `z-index: 5` 不在 Tailwind 档位 | `sed -i 's/z-index: 5/z-index: 10/'` |
| `MdToDocxTab.vue` | `linear-gradient` 纸纹理 | `sed -i '/linear-gradient/d'` |
| `MdToDocxTab.vue` | 预览空状态无可操作按钮 | 添加"加载示例"按钮在空状态内 |
| `ToolCard.vue` | hover 图标用 raw `#fff` | 改为 `var(--color-surface)` |

### 6.4 Nuxt UI 特定注意事项

| 问题 | 解决 |
|------|------|
| `ui.fonts: false` | 禁用 Google Fonts 下载（中国大陆必须），避免 unifont 超时 |
| `icon.provider: "iconify"` | 使用本地图标 API，不依赖外部 CDN |
| `@nuxt/icon` v2 默认 | Heroicons 是本地 SVG，无需网络请求 |
| `UFormField` 替代 `UFormGroup` | Nuxt UI v4 重命名了此组件 |
| `UTabs` 的 items 格式 | `[{ label: "..." }]` 数组，不再用 slot |
| `useToast` 需 `import.meta.client` 守卫 | 服务端无 DOM 上下文 |
