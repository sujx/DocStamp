# docStamp 全面重构方案

## 一、概述

对 docStamp 进行全栈重构：升级为 Nuxt 3 架构，后端模块解耦，调整功能集。

**核心变更**：
- 框架降级：Nuxt 4 → Nuxt 3（稳定 LTS）
- 架构解耦：Flask Blueprint + 独立 Service 层
- 功能调整：去除电子书转换，增加 .doc 支持

---

## 二、技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Nuxt | 3.x（最新稳定版） |
| UI 组件 | @nuxt/ui | 2.x（兼容 Nuxt 3） |
| CSS | Tailwind CSS | v3 |
| 图标 | @nuxt/icon | 1.x |
| 国际化 | @nuxtjs/i18n | 8.x（兼容 Nuxt 3） |
| 后端框架 | Flask | 3.x |

---

## 三、功能模块（最终版）

| # | 模块 | 路由 | 说明 |
|---|------|------|------|
| 1 | MD 转公文 | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX，实时预览 |
| 2 | 属性修改 | `/properties` | .doc/.docx/.xlsx/.pptx 元数据修改 |
| 3 | 文件组装 | `/file-assembly` | 图片合并PDF + PDF拆解为图片 |
| 4 | 打印分组 | `/print-split` | PDF 批次拆分 |
| 5 | 水印管理 | `/watermark` | 添加/去除水印 |
| 6 | PDF 编辑 | `/pdf-editor` | 删除/插入/重排页面 |
| 7 | Excel 合并 | `/excel-merge` | .xlsx/.csv 合并 |
| 8 | 格式规范 | `/format-docx` | DOCX 按 GB/T 9704-2012 格式化 |
| 9 | 仪表盘 | `/` | 工具入口 |

**已移除**：
- ~~电子书转 MD~~ — 去除整个功能模块（前后端+路由）
- ~~format-docx 独立页面~~ — 合并到 MD 转公文流程中

**功能增强**：
- Office 属性修改增加 `.doc` 格式支持

---

## 四、解耦后的项目结构

```
docStamp/
├── backend/
│   ├── app.py                  # Flask 工厂 create_app()（<50行）
│   ├── config.py               # 统一配置
│   ├── blueprints/             # HTTP 路由层
│   │   ├── __init__.py
│   │   ├── convert.py          # /api/convert/*
│   │   ├── files.py            # /api/properties, /api/img2pdf, ...
│   │   └── download.py         # /api/download, /api/health
│   ├── services/               # 业务逻辑层（纯函数，零 Flask 依赖）
│   │   ├── __init__.py
│   │   ├── converter.py        # markdown→docx, pandoc 转换
│   │   ├── formatter.py        # GB/T 9704-2012 格式化
│   │   ├── watermark.py        # 水印添加/去除
│   │   ├── pdf_editor.py       # PDF 页面操作
│   │   ├── excel_merger.py     # Excel/CSV 合并
│   │   ├── img2pdf_handler.py  # 图片→PDF
│   │   ├── pdf_to_images.py    # PDF→图片
│   │   ├── print_split.py      # 打印分组
│   │   └── properties.py       # Office 属性（含 .doc 支持）
│   └── utils/
│       ├── __init__.py
│       └── file_helpers.py     # _validate_filename/_save_upload/_cleanup_files
├── frontend/                   # Nuxt 3 项目
│   ├── nuxt.config.ts
│   ├── app.config.ts
│   ├── assets/css/main.css     # Tailwind v3 配置
│   ├── plugins/
│   │   └── axios.client.ts
│   ├── composables/
│   │   └── useDownload.ts      # Blob 下载
│   ├── layouts/default.vue     # 侧边导航壳
│   ├── pages/                  # 9 个路由页面
│   ├── components/             # 15+ 组件
│   └── i18n/locales/           # zh-CN / en
├── manage.sh
├── Dockerfile
└── REFACTOR_PLAN.md（本文档）
```

---

## 五、Nuxt 3 → Nuxt 4 降级清单

| 配置项 | Nuxt 4（当前） | Nuxt 3（目标） |
|--------|--------------|--------------|
| `package.json` | `nuxt: ^4.4` | `nuxt: ^3.15` |
| | `@nuxt/ui: ^4.8` | `@nuxt/ui: ^2.21` |
| | `@nuxtjs/i18n: ^10.4` | `@nuxtjs/i18n: ^8.5` |
| | `@nuxt/icon: ^2.2` | `@nuxt/icon: ^1.10` |
| CSS | `@import "tailwindcss"` (v4) | `tailwind.config.ts` (v3) |
| 组件名 | `UFormField` | `UFormGroup` |
| 主题配置 | `app.config.ts` 自定义色阶 | Nuxt UI 2 默认色阶 + 覆盖 |
| `ui.fonts` | v4 特有 | 不存在，无需设置 |
| `icon.provider` | v4 特有 | 不存在，默认本地 |

### Nuxt 3 配置变更

**package.json**：
```json
"dependencies": {
  "nuxt": "^3.15",
  "@nuxt/ui": "^2.21",
  "@nuxtjs/i18n": "^8.5",
  "@nuxt/icon": "^1.10",
  "axios": "^1.7"
}
```

**nuxt.config.ts** 主要变化：
- 移除 `ui.fonts`（v3 不存在）
- 移除 `icon.provider`（v3 默认本地）
- 移除 `compatibilityDate`（v3 无此选项）
- `i18n` 配置格式：`langDir: "locales/"` → v3 默认从 `locales/` 读取

**tailwind.config.ts**（新建，v3 必须）：
```typescript
export default {
  content: [
    "./components/**/*.{vue,js,ts}",
    "./pages/**/*.{vue,js,ts}",
    "./layouts/**/*.{vue,js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        brand: { 50-950: [...], 700: "#008a3d" },
        page: "#f9f7e8",
        surface: "#ffffff",
        muted: "#f4f2e4",
      },
      textColor: {
        primary: "#1a1a1a",
        secondary: "#5c5c5c",
        tertiary: "#8c8a7a",
      },
      borderRadius: { sm: "6px", md: "10px", lg: "14px" },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)",
        elevated: "0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.03)",
      },
    },
  },
};
```

**app.config.ts**（Nuxt UI 2 格式）：
```typescript
export default defineAppConfig({
  ui: {
    primary: "green",
    gray: "cool",
  },
});
```

---

## 六、.doc 格式支持

在 Office 属性修改模块中增加 `.doc` 支持：

| 文件 | 变更 |
|------|------|
| `app.py:Config` | `OFFICE_EXTENSIONS` 增加 `"doc"` |
| `services/properties.py` | 新增 `_modify_doc()` 处理 .doc |
| 前端 | FileUploader accept 增加 `.doc` |

技术方案：`.doc` 文件通过 LibreOffice `--headless` 转换为 `.docx` → 修改属性 → 保留为 `.doc` 输出。

---

## 七、实施顺序

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 1 | Nuxt 4 → Nuxt 3 降级（package.json + 配置文件 + 组件 API 适配） | 2h |
| 2 | 后端解耦（拆分 Blueprint + Service + Utils） | 1.5h |
| 3 | 去除电子书转换功能（路由 + 组件 + i18n） | 0.5h |
| 4 | 增加 .doc 格式支持 | 0.5h |
| 5 | 验证 + 清理 | 0.5h |
