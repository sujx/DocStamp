# docStamp 项目蓝图

> 前端界面要求 & 功能实现逻辑完整导出

---

## 第一部分：项目架构

### 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Nuxt | 4.4 |
| UI 组件库 | @nuxt/ui | 4.8 |
| CSS | Tailwind CSS | v4 |
| 图标 | @nuxt/icon (Heroicons) | 2.2 |
| 国际化 | @nuxtjs/i18n | 10.4 |
| 后端框架 | Flask | 3.x |
| 后端 CORS | flask-cors | 5.x |
| 后端 i18n | flask-babel | 4.x |

### 项目结构

```
docStamp/
├── backend/                         # Flask API
│   ├── app.py                       # 主程序 + 24 个路由
│   ├── converter.py                 # 文档转换引擎
│   ├── formatter.py                 # GB/T 9704-2012 格式化
│   ├── properties.py                # Office 属性
│   ├── img2pdf_handler.py           # 图片 -> PDF
│   ├── pdf_to_images.py             # PDF -> 图片
│   ├── print_split.py               # 打印分组
│   ├── watermark.py                 # 水印添加/去除
│   ├── pdf_editor.py                # PDF 编辑
│   ├── excel_merger.py              # Excel 合并
│   └── gunicorn.conf.py
├── frontend/                        # Nuxt 4 SPA
│   ├── nuxt.config.ts               # 框架配置
│   ├── app.config.ts                # Nuxt UI 主题
│   ├── assets/css/main.css          # Tailwind @theme
│   ├── plugins/axios.client.ts      # 开发环境 API 直连
│   ├── composables/useDownload.ts   # Blob 下载 + Toast
│   ├── layouts/default.vue          # 侧边导航壳
│   ├── pages/                       # 10 个路由页面
│   │   ├── index.vue                # 仪表盘
│   │   ├── md-to-docx.vue
│   │   ├── properties.vue
│   │   ├── file-assembly.vue
│   │   ├── print-split.vue
│   │   ├── watermark.vue
│   │   ├── pdf-editor.vue
│   │   ├── excel-merge.vue
│   │   ├── ebook-to-md.vue
│   │   └── format-docx.vue
│   ├── components/                  # 15+ 组件
│   │   ├── Sidebar.vue              # 侧边导航
│   │   ├── PageHeader.vue           # 页面头（返回链接）
│   │   ├── ToolCard.vue             # 仪表盘工具卡片
│   │   ├── FileUploader.vue         # 可复用文件上传
│   │   ├── FileList.vue             # 文件列表
│   │   ├── EmptyState.vue           # 空状态
│   │   ├── AppHeader.vue / AppFooter.vue
│   │   ├── LanguageSwitcher.vue
│   │   ├── MdToDocxTab.vue          # MD -> 公文
│   │   ├── PropertiesTab.vue        # 属性修改
│   │   ├── FileAssembly.vue         # 文件组装（子功能卡片）
│   │   ├── Img2PdfTab.vue / PdfToImagesTab.vue
│   │   ├── PrintSplitTab.vue
│   │   ├── WatermarkManagement.vue  # 水印管理（子功能卡片）
│   │   ├── WatermarkTab.vue / RemoveWatermarkTab.vue
│   │   ├── PdfEditorTab.vue
│   │   ├── ExcelMergeTab.vue
│   │   ├── EbookToMdTab.vue
│   │   └── FormatDocxTab.vue
│   └── i18n/locales/                # zh-CN / en
├── manage.sh
├── Dockerfile
└── SPEC.md
```

---

## 第二部分：设计系统

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

### 布局规范

- 侧边导航 240px（可折叠至 64px）
- 内容最大宽度：`max-w-5xl`
- 圆角：6px / 10px / 14px
- 阴影：`shadow-sm`（卡片）、`shadow-md`（浮层）
- 过渡：150-200ms，仅 opacity/transform/border-color
- 所有标题使用 `text-balance`，正文使用 `text-pretty`
- 固定元素使用 `safe-area-inset` 适配刘海屏
- 使用 `h-dvh` 替代 `h-screen`
- 禁止硬编码颜色，必须通过 CSS 变量引用

---

## 第三部分：页面路由与导航

### 路由表

| 路由 | 页面 | 组件 |
|------|------|------|
| `/` | 仪表盘 | index.vue (ToolCard 网格) |
| `/md-to-docx` | MD 转公文 | MdToDocxTab.vue |
| `/properties` | 属性修改 | PropertiesTab.vue |
| `/file-assembly` | 文件组装 | FileAssembly.vue (子功能卡片) |
| `/print-split` | 打印分组 | PrintSplitTab.vue |
| `/watermark` | 水印管理 | WatermarkManagement.vue (子功能卡片) |
| `/pdf-editor` | PDF 编辑 | PdfEditorTab.vue |
| `/excel-merge` | Excel 合并 | ExcelMergeTab.vue |
| `/ebook-to-md` | 电子书转 MD | EbookToMdTab.vue |
| `/format-docx` | 格式规范 | FormatDocxTab.vue |

### 侧边导航

- 仪表盘（home 图标）
- MD 转公文（arrow-down-tray 图标）
- 属性修改（document-text 图标）
- 文件组装（arrows-right-left 图标）
- 打印分组（printer 图标）
- 水印管理（beaker 图标）
- PDF 编辑（document 图标）
- Excel 合并（table-cells 图标）
- 电子书转 MD（book-open 图标）
- 格式规范（document-check 图标）
- 底部：语言切换 + 折叠按钮

---

## 第四部分：功能实现逻辑

### 功能 1：MD 转公文

**路由**：`/md-to-docx`  
**组件**：`MdToDocxTab.vue`  
**API**：`POST /api/convert` | `GET /api/download/<id>` | `POST /api/preview` | `GET /api/stats`

**UI 要求**：
- 左右等宽分栏（`grid-cols-2`）
- 左栏：编辑器面板（工具栏 + 等宽字体 textarea）
- 右栏：预览面板（公文纸效果，模拟打印效果）
- 底部：转换按钮 + GB/T 9704-2012 规范链接
- 加载遮罩：SVG 旋转环 + 进度文字

**实现逻辑**：
1. 用户输入 Markdown 或上传 `.md` 文件
2. 编辑器每次输入触发 200ms debounce
3. 客户端 `marked.parse()` 渲染 HTML → DOMPurify 清理 → 注入预览区
4. 点击"开始转换" → POST Markdown 到 `/api/convert`
5. 后端：Pandoc MD→DOCX → python-docx 格式化（页边距/字体/行距/标题层级/页码）
6. 返回 download_id → GET `/api/download/<id>` → Blob 下载
7. 文件名自动提取自一级标题 `# 标题`

**关键代码路径**：
- 后端：`app.py:md_convert()` → `converter.py:md_to_docx()` → `formatter.py:format_docx()`
- 前端：`MdToDocxTab.vue:renderMarkdown()` → `formatFile()` → blob download

---

### 功能 2：Office 文档属性修改

**路由**：`/properties`  
**组件**：`PropertiesTab.vue`  
**API**：`POST /api/properties` | `POST /api/properties/info` | `POST /api/properties/batch`

**UI 要求**：
- 模式选择：单文件 / 批量上传（radio 切换）
- 时间模式：统一时间 / 分别设定
- 属性表单：创建人、修改人、创建时间、修改时间
- 文件列表（批量模式）：绿色标签 + 删除按钮

**实现逻辑**：
1. 单文件：FileUploader 选择 → 表单填写属性 → POST `/api/properties` → Blob 下载
2. 批量：选择多个文件 → 统一属性 → POST `/api/properties/batch` → ZIP 下载
3. 后端：`properties.py` — python-docx/openpyxl/python-pptx 修改 Dublin Core 元数据

---

### 功能 3：文件组装

**路由**：`/file-assembly`  
**组件**：`FileAssembly.vue`（子功能卡片切换）  
**子功能**：`Img2PdfTab.vue` | `PdfToImagesTab.vue`

#### 3a：图片合并 PDF

**UI 要求**：
- 多文件上传、拖拽排序
- 缩略图网格 + 上下移动按钮
- 页面尺寸选择（原始/A4/Letter）+ 自定义文件名

**实现逻辑**：
1. 选择多张图片 → 生成缩略图 → 拖拽/按钮调整顺序
2. POST `/api/img2pdf`（files + order + page_size + filename）
3. 后端：`img2pdf_handler.py` — 无损转换（img2pdf）或 reportlab 居中缩放

#### 3b：PDF 拆解为图片

**UI 要求**：
- 单文件上传（PDF）
- 格式选择（PNG/JPEG）+ DPI（72/150/200/300）+ 页码范围

**实现逻辑**：
1. POST `/api/pdf2img`（file + format + dpi + pages）
2. 后端：`pdf_to_images.py` — pdftoppm 渲染 → ZIP 打包
3. 前端接收 Blob → 下载 `pdf_images.zip`

---

### 功能 4：PDF 打印分组

**路由**：`/print-split`  
**组件**：`PrintSplitTab.vue`  
**API**：`POST /api/print-split` | `GET /api/print-split/<id>/batch/<n>`

**UI 要求**：
- FileUploader + 每批页数 + 间隔时间
- 进度条 + 已下载计数 + 倒计时
- 暂停/继续/终止按钮

**实现逻辑**：
1. POST `/api/print-split`（file + batch_size + interval）→ 获取 task_id + batch_count
2. 前端定时器自动循环下载每个批次
3. 暂停：清除定时器 + 保存倒计时状态
4. 继续：恢复定时器
5. 终止：清除任务
6. 后端：`print_split.py` — pypdf 拆分 PDF，每批次保存为独立文件

---

### 功能 5：水印管理

**路由**：`/watermark`  
**组件**：`WatermarkManagement.vue`（子功能卡片切换）  
**子功能**：`WatermarkTab.vue` | `RemoveWatermarkTab.vue`

#### 5a：添加水印

**UI 要求**：
- 文件上传（PDF/DOCX）
- 水印类型切换（文字/图片）
- 参数：字体、字号、颜色、透明度、旋转、位置（平铺/居中）
- Canvas 实时预览

**实现逻辑**：
1. 选择文件 → 配置水印参数 → Canvas 绘制预览
2. POST `/api/watermark`（file + params JSON + 可选 watermark_image）
3. 后端：`watermark.py:add_watermark()` → PDF 用 reportlab 叠加，DOCX 用 python-docx 页眉

#### 5b：去除水印

**UI 要求**：
- 文件上传（PDF/DOCX）
- 格式相关提示（DOCX 可靠 / PDF 尽力）
- 去除按钮

**实现逻辑**：
1. POST `/api/watermark/remove`（file）
2. 后端：DOCX 清除页眉段落；PDF 三层策略：
   - 压缩内容流
   - 删除 `/Annots`（注释类水印）
   - 删除 `/Resources/XObject`（图像类水印）

---

### 功能 6：PDF 页面编辑

**路由**：`/pdf-editor`  
**组件**：`PdfEditorTab.vue`  
**API**：`POST /api/pdf-editor/info` | `POST /api/pdf-editor/delete` | `POST /api/pdf-editor/insert` | `POST /api/pdf-editor/reorder`

**UI 要求**：
- 三种模式 radio 切换：删除、插入、重排
- 页面缩略图网格（pdftoppm 渲染）
- 点击选择（删除模式）、拖拽排序（重排模式）
- 选中态红色边框

**实现逻辑**：
1. 上传 PDF → POST `/api/pdf-editor/info` → 获取页数和缩略图 URL
2. 删除模式：点击选择页面 → POST `/api/pdf-editor/delete`（pages[]）
3. 插入模式：选择源文件 + 目标位置 → POST `/api/pdf-editor/insert`
4. 重排模式：拖拽/按钮调整顺序 → POST `/api/pdf-editor/reorder`（order[]）
5. 后端：`pdf_editor.py` — pypdf PdfReader/PdfWriter 操作

---

### 功能 7：Excel 合并

**路由**：`/excel-merge`  
**组件**：`ExcelMergeTab.vue`  
**API**：`POST /api/excel-merge`

**UI 要求**：
- 多文件上传（.xlsx/.csv）
- 文件列表（名称 + 行数）
- 输出文件名 + 合并按钮
- 小于 2 个文件时警告

**实现逻辑**：
1. 选择多个文件 → 前端验证至少 2 个
2. POST `/api/excel-merge`（files[] + filename）
3. 后端：`excel_merger.py` — 验证所有文件列标题一致 → openpyxl 逐行追加 → 输出 .xlsx
4. CSV 文件：csv.reader 读取，utf-8-sig 编码

---

### 功能 8：电子书转 MD

**路由**：`/ebook-to-md`  
**组件**：`EbookToMdTab.vue`  
**API**：`POST /api/convert/doc2md`

**UI 要求**：
- 拖拽上传区（.doc/.docx/.azw/.mobi/.epub/.txt）
- 转换中 loading 状态
- 成功后显示文件名 + 下载按钮

**实现逻辑**：
1. 选择文件 → POST `/api/convert/doc2md`（file）
2. 后端：`converter.py:convert_to_md()` 按扩展名分发：
   - `.docx` → Pandoc
   - `.doc` → LibreOffice headless → Pandoc
   - `.epub` → Pandoc
   - `.azw/.mobi` → Calibre ebook-convert → Pandoc（fallback: mobiunpack）
3. 返回 Markdown 文本 → 前端生成 Blob → 下载 `.md`

---

### 功能 9：格式规范

**路由**：`/format-docx`  
**组件**：`FormatDocxTab.vue`  
**API**：`POST /api/convert/format-docx` | `GET /api/download/<id>`

**UI 要求**：
- 拖拽上传区（.docx）
- 文件选择后显示文件名 + 操作按钮
- 下载格式化的文档

**实现逻辑**：
1. 选择 DOCX → POST `/api/convert/format-docx`（file）
2. 后端：`formatter.py:format_docx()` 应用 GB/T 9704-2012：
   - 页边距：上 3.7cm 下 3.5cm 左 2.8cm 右 2.6cm
   - 标题：方正小标宋 22pt（二号）居中
   - 一级标题：黑体 16pt（三号）加粗
   - 二级标题：楷体 16pt 加粗
   - 正文：仿宋 16pt
   - 行距：28.6pt 固定值
   - 偶数/奇数页页脚：— PAGE —
3. 返回 download_id → GET `/api/download/<id>` → Blob 下载
4. 输出文件名与输入文件名一致

---

## 第五部分：通用组件规范

### FileUploader

**Props**：`icon`, `hint`, `accept`  
**Emits**：`file-selected`, `reset`  
**状态**：default / dragover / has-file  
**样式**：虚线边框（`border-2 border-dashed`），拖入时绿色高亮

### PageHeader

**Props**：`title`（已废弃）、`backTo`（默认 `/`）  
**渲染**：仅返回链接 `← 返回`（标题由侧边导航标识）

### ToolCard

**Props**：`icon`, `title`, `description`, `to`  
**交互**：hover 上浮 2px + 绿色边框 + 图标反色（绿底白图标）

### FileList

**Props**：`files: FileItem[]`  
**Emits**：`remove(idx)`, `clear`  
**FileItem**：`{ id, name, icon?, meta? }`

### EmptyState

**Props**：`icon`, `title`, `description`, `actionLabel?`, `actionTo?`  
**渲染**：图标 + 标题 + 描述 + 可选操作按钮

---

## 第六部分：API 端点全集

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/stats` | MD 转换计数 |
| `POST` | `/api/preview` | MD → HTML 预览 |
| `POST` | `/api/convert` | MD → DOCX |
| `POST` | `/api/convert/doc2md` | Word/电子书 → MD |
| `POST` | `/api/convert/format-docx` | DOCX 格式化 |
| `GET` | `/api/download/<id>` | 下载文件（后自动删除） |
| `POST` | `/api/properties` | 修改 Office 属性 |
| `POST` | `/api/properties/info` | 读取属性 |
| `POST` | `/api/properties/batch` | 批量修改 |
| `POST` | `/api/img2pdf` | 图片合并 PDF |
| `POST` | `/api/pdf2img` | PDF → 图片 ZIP |
| `POST` | `/api/print-split` | PDF 打印分组 |
| `GET` | `/api/print-split/<id>/batch/<n>` | 下载批次 |
| `POST` | `/api/watermark` | 添加水印 |
| `POST` | `/api/watermark/remove` | 去除水印 |
| `POST` | `/api/pdf-editor/info` | PDF 页面信息 |
| `GET` | `/api/pdf-editor/thumb/...` | 页面缩略图 |
| `POST` | `/api/pdf-editor/delete` | 删除页面 |
| `POST` | `/api/pdf-editor/insert` | 插入页面 |
| `POST` | `/api/pdf-editor/reorder` | 重排页面 |
| `POST` | `/api/excel-merge` | Excel/CSV 合并 |

---

## 第七部分：配置要点

### nuxt.config.ts

- `ssr: false` — SPA 模式
- `ui.fonts: false` — 禁用 Google Fonts（中国大陆必备）
- `icon.provider: "iconify"` — 本地图标
- `vite.server.proxy` — 开发代理 /api → :5000

### 开发环境

```bash
# 后端
cd backend && python3 app.py                    # :5000

# 前端
cd frontend && npm run dev                      # :8080

# 一键
./manage.sh start
```

### 生产构建

```bash
cd frontend && npm run build                    # nuxt generate
# 输出: .output/public/
# Flask STATIC_FOLDER 指向此目录
```
