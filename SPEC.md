# docStamp — 设计规范与开发指南

## 一、项目概述

docStamp 是一站式文档处理工具箱。采用 Nuxt 4 + Nuxt UI v4 + Tailwind CSS v4 前端，Flask REST API 后端。绿鹃品牌色系（`#008A3D` + 米黄底 `#F9F7E8`），仪表盘 + 侧边导航 + 多页面路由架构。

**i18n**：支持中英文双语，当前重点维护中文，英文入口保留。

---

## 二、功能模块

### 现有功能（8 个，归为 4 组）

**侧栏导航结构**：

```
MD 转公文        → /md-to-docx
水印管理          → /watermark       (子功能：添加/去除水印)
Office 工具 ▸     → 悬浮子菜单:
  ├─ 属性修改     → /properties
  ├─ Excel 合并   → /excel-merge
  └─ 格式规范     → /format-docx
PDF 工具 ▸        → 悬浮子菜单:
  ├─ 文件组装     → /file-assembly   (子功能：图片合并PDF + PDF拆解为图片，拆解显示百分比进度)
  ├─ 打印分组     → /print-split
  └─ PDF 编辑     → /pdf-editor
```

| # | 模块 | 路由 | 分组 | 说明 |
|---|------|------|------|------|
| 1 | MD 转公文 | `/md-to-docx` | — | Markdown → DOCX，实时预览 |
| 2 | 水印管理 | `/watermark` | — | 添加/去除水印 |
| 3 | 属性修改 | `/properties` | Office | .docx/.xlsx/.pptx 元数据 |
| 4 | Excel 合并 | `/excel-merge` | Office | .xlsx/.csv 合并 |
| 5 | 格式规范 | `/format-docx` | Office | GB/T 9704-2012 格式化 |
| 6 | 文件组装 | `/file-assembly` | PDF | 图片合并 + 拆解（百分比进度） |
| 7 | 打印分组 | `/print-split` | PDF | 批次拆分、暂停/继续/终止 |
| 8 | PDF 编辑 | `/pdf-editor` | PDF | 删除/插入/重排页面 |

### 悬浮子菜单交互

- Office工具 / PDF工具 为父级菜单项，不路由跳转
- 鼠标悬停或点击时，向右弹出子菜单浮层
- 子菜单背景白色卡片 + 阴影，8px 圆角
- 当前激活的子项绿色高亮
- 移动端：点击展开/折叠子菜单

---

## 三、设计系统

### 配色 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-700` | `#008a3d` | 品牌主色 |
| `--color-brand-800` | `#00662b` | 悬停加深 |
| `--color-brand-soft` | `rgba(0,138,61,0.08)` | 柔和底色 |
| `--color-page` | `#f9f7e8` | 米黄页面底 |
| `--color-surface` | `#ffffff` | 卡片/面板白 |
| `--color-muted` | `#f4f2e4` | 次级区域 |
| `--color-text-primary` | `#1a1a1a` | 正文 |
| `--color-text-secondary` | `#5c5c5c` | 辅助文字 |
| `--color-text-tertiary` | `#8c8a7a` | 提示/脚注 |
| `--color-border-default` | `#e8e6d8` | 默认边框 |
| `--color-border-subtle` | `#f0efe5` | 细分隔线 |

### 字体

- UI：PingFang SC / Microsoft YaHei / system-ui
- 编辑区：JetBrains Mono / Fira Code
- 公文预览：仿宋_GB2312 / FangSong / 黑体 / 楷体

### 组件库

Nuxt UI v4（UButton, UInput, USelect, UTabs, UFormField, UAlert, UProgress, UIcon）

### baseline-ui 合规

- 所有标题使用 `text-balance`，正文使用 `text-pretty`
- 使用 `h-dvh` 替代 `h-screen`
- 图标按钮必须添加 `aria-label`
- 固定元素添加 `safe-area-inset` 适配
- 禁止硬编码颜色（必须通过 CSS 变量引用）
- 禁止 `transition: all`（必须列出具体属性）
- 禁止 `linear-gradient`（除非明确要求）
- 禁止修改 `letter-spacing`

### 布局

侧边导航（240px，可折叠至 64px）+ 右侧内容区。仪表盘首页为数字时钟 + 工具卡片网格（3 列），每个工具独立路由页面。统一 PageHeader（返回链接）+ 内容区结构。子功能（文件组装/水印管理）使用卡片式模式切换。

**侧栏状态**：折叠状态通过 `localStorage("sidebar_collapsed")` 持久化，Layout 通过 `provide/inject` 共享状态，`margin-left` 动态响应（展开 240px / 折叠 64px）。

---

### 仪表盘数字时钟

仪表盘首页使用 7 段数码管 LED 时钟，替代原站点标题区域。

#### 组件：`DigitalClock.vue`

```
┌────────────────────────────────┐
│  ┌──┐┌──┐   ┌──┐┌──┐   ┌──┐┌──┐│
│  │  ││  │ : │  ││  │ : │  ││  ││  ← 白色卡片底
│  └──┘└──┘   └──┘└──┘   └──┘└──┘│
│   HH   MM   SS                   │
└────────────────────────────────┘
```

**7 段数码管定义**：每段编号 1-7（上横、右上竖、右下竖、下横、左下竖、左上竖、中横）

```typescript
const patterns: Record<number, number[]> = {
  0: [1,2,3,4,5,6],  1: [2,3],  2: [1,2,7,5,4],
  3: [1,2,7,3,4],    4: [6,7,2,3],  5: [1,6,7,3,4],
  6: [1,3,4,5,6,7],  7: [1,2,3],  8: [1,2,3,4,5,6,7],
  9: [1,2,3,4,6,7],
};
```

**配色（暖纸主题）**：

| 元素 | 值 | 说明 |
|------|-----|------|
| 面板背景 | `var(--color-surface)` | 白色卡片 (#ffffff) |
| 面板阴影 | `var(--shadow-card)` | 暖色卡片阴影 |
| 未激活段 | `var(--color-border-default)` | 暖米色 #e8e6d8，50% 透明度 |
| 激活段 | `var(--color-brand-700)` | 品牌绿 #008a3d |
| 激活辉光 | `rgba(0,138,61,0.25)` | 柔和绿色辉光 |
| 冒号点 | `var(--color-brand-700)` | 品牌绿，1s blink 动画 |

**尺寸**：每位数 54×96px，面板圆角 14px，内边距 14×28px。

**Props**：

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `digitColor` | string | `var(--color-brand-700)` | 激活段颜色 |
| `offColor` | string | `var(--color-border-default)` | 未激活段颜色 |
| `glowColor` | string | `rgba(0,138,61,0.25)` | 激活段辉光 |

**功能**：纯时钟显示（HH:MM:SS），无倒计时/计时器。每秒通过 `setInterval` 更新，卸载时清除定时器。

---

## 四、后端架构

```
backend/
├── app.py                  # Flask 工厂 create_app()
├── config.py               # 统一配置
├── blueprints/             # HTTP 路由层
│   ├── convert.py          # /api/convert/*
│   ├── files.py            # /api/properties, /api/img2pdf, ...
│   └── download.py         # /api/download, /api/health
├── services/               # 业务逻辑层（纯函数）
│   ├── converter.py
│   ├── formatter.py
│   ├── watermark.py
│   └── ...
└── utils/
    └── file_helpers.py
```

---

## 五、API 端点全集

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/stats` | 转换计数 |
| `POST` | `/api/preview` | MD → HTML 预览 |
| `POST` | `/api/convert` | MD → DOCX |
| `POST` | `/api/convert/format-docx` | DOCX 格式化 |
| `GET` | `/api/download/<id>` | 下载文件 |
| `POST` | `/api/properties` | 修改属性 |
| `POST` | `/api/properties/info` | 读取属性 |
| `POST` | `/api/properties/batch` | 批量修改 |
| `POST` | `/api/img2pdf` | 图片合并 PDF |
| `POST` | `/api/pdf2img` | PDF 拆解为图片 |
| `POST` | `/api/print-split` | 打印分组 |
| `GET` | `/api/print-split/<id>/batch/<n>` | 下载批次 |
| `POST` | `/api/watermark` | 添加水印 |
| `POST` | `/api/watermark/remove` | 去除水印 |
| `POST` | `/api/pdf-editor/info` | 页面信息 |
| `GET` | `/api/pdf-editor/thumb/...` | 页面缩略图 |
| `POST` | `/api/pdf-editor/delete` | 删除页面 |
| `POST` | `/api/pdf-editor/insert` | 插入页面 |
| `POST` | `/api/pdf-editor/reorder` | 重排页面 |
| `POST` | `/api/excel-merge` | Excel 合并 |

---

## 六、开发难点与经验

### 后端

| 问题 | 原因 | 解决 |
|------|------|------|
| 代码修改后不生效 | Flask 进程未重启 | `./manage.sh restart`（已内置 fuser -k 强制清理端口） |
| 变量名不匹配 500 | 批量替换只改定义未改引用 | 修改后 grep 检查 JSON 响应中的变量一致性 |
| 中文字体不生效 | `run.font.name` 只读西文字体 | 读 XML `w:rFonts/w:eastAsia` 验证 |
| Pandoc 标题蓝色残留 | Pandoc Heading 样式自带颜色 | 移除段落 `w:pStyle` 后重新设置字体 |
| send_file 清理时序 | finally 可能提前删文件 | 用 `@after_this_request` 延迟清理 |

### 前端

| 问题 | 原因 | 解决 |
|------|------|------|
| Nuxt 代理不生效 | nitro.devProxy 环境不一致 | 组件直连 `http://localhost:5000` 用 fetch |
| 预览不工作 | 动态 `import("marked")` 在浏览器失败 | 改为顶层静态 `import { marked } from "marked"` |
| 下载无反应 | `<a>.click()` 未添加到 DOM | `appendChild(a)` → `click()` → `removeChild(a)` |
| `npx nuxt` 路径错误 | 工作目录不在 frontend/ | 始终 `cd frontend && npx nuxt <cmd>` |
| Google Fonts 超时 | unifont 被墙 | `ui.fonts: false` + `icon.provider: "iconify"` |
| UFormGroup 不存在 | Nuxt UI v4 改名 | 全局替换为 `UFormField` |
| `computed()` 上下文错误 | 模块顶层调用 composable | 用 `import.meta.client` 守卫 |

### 部署

| 问题 | 解决 |
|------|------|
| 旧进程占用端口 | `manage.sh` 已内置 `fuser -k 5000/tcp` |
| 日志权限 | `mkdir -p /var/log/docstamp && chown docstamp:docstamp` |
| 僵死 PID 文件 | `_start_backend()` 启动前检查 PID 有效性 |

---

## 七、版本历史

### v2.3 (2026-06)
- 侧栏重构：分组悬浮子菜单（Office 工具 / PDF 工具）
- 仪表盘数字时钟（7 段数码管 LED，暖纸主题配色）
- 侧栏状态持久化（localStorage + provide/inject + 动态 margin-left）
- PdfToImagesTab 增加页面数显示 + 进度条
- 仪表盘去除站点标题/子标题

### v2.2 (2026-06)
- 移除电子书转 MD 功能
- 后端 converter.py 清理
- SPEC.md 与 DEV_GUIDE.md 合并

### v2.1 (2026-06)
- PDF 水印去除增强：三层策略
- baseline-ui 合规审查（55 处违规修复）
- 新增《前端框架迁移指南》

### v2.0 (2026-06)
- 架构升级：Buefy → Nuxt 4 + Nuxt UI v4
- 新功能：MD 转公文、电子书转 MD、格式规范、Excel/CSV 合并
- UI 重构：仪表盘 + 侧边导航 + 多页面路由

### v1.0 (2026-06)
- 5 大核心功能、Buefy 前端 + Flask 后端
