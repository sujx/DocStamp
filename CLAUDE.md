# CLAUDE.md — docStamp 项目规范

## 项目概述

docStamp 是一站式文档处理工具箱，9 大功能模块。Nuxt 4 + Nuxt UI v4 + Tailwind CSS v4 前端，Flask REST API 后端。绿鹃品牌色系（`#008A3D` + `#F9F7E8`），仪表盘 + 侧边导航 + 多页面路由，中英文双语。

## 项目结构

```
docStamp/
├── backend/                    # Flask API（9 模块 + 24 端点）
│   ├── app.py                  # 工厂模式 create_app() + _register_routes()
│   ├── converter.py            # Pandoc/LibreOffice/Calibre 文档转换
│   ├── formatter.py            # GB/T 9704-2012 DOCX 格式化
│   ├── properties.py           # Office 属性读写
│   ├── img2pdf_handler.py      # 图片 → PDF
│   ├── pdf_to_images.py        # PDF → 图片（pdftoppm）
│   ├── print_split.py          # PDF 打印分组
│   ├── watermark.py            # 水印添加 + 去除
│   ├── pdf_editor.py           # PDF 页面编辑
│   ├── excel_merger.py         # Excel/CSV 合并
│   ├── gunicorn.conf.py        # Gunicorn 配置
│   └── tests/                  # 27 tests
├── frontend/                   # Nuxt 4 SPA
│   ├── nuxt.config.ts          # 模块、代理、i18n、图标
│   ├── app.config.ts           # Nuxt UI brand 主题
│   ├── assets/css/main.css     # Tailwind @theme + CSS 变量
│   ├── plugins/axios.client.ts # 开发模式 API 直连 :5000
│   ├── composables/useDownload.ts
│   ├── layouts/default.vue     # 侧边导航 + 内容区
│   ├── pages/                  # 10 个路由页面（仪表盘 + 9 工具）
│   ├── components/             # 15+ 组件
│   └── i18n/locales/           # zh-CN / en
├── manage.sh                   # 开发管理
├── Dockerfile
└── SPEC.md
```

## 开发环境

### 启动

```bash
# 启动后端
cd backend && python3 app.py                    # :5000

# 启动前端
cd frontend && npm run dev                      # :8080

# 一键启动
./manage.sh start
```

### 代理

`plugins/axios.client.ts` 在开发模式下将 API 请求直连 `localhost:5000`。生产环境通过 Flask 服务 Nuxt 静态输出。

### 测试

```bash
./manage.sh test                # 27 tests, <0.5s
cd frontend && npm run build    # 构建验证
```

## 设计规范

### 颜色 Token（Tailwind @theme）

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-brand-700` | `#008a3d` | 主色 |
| `--color-page` | `#f9f7e8` | 页面底 |
| `--color-surface` | `#ffffff` | 卡片白 |
| `--color-text-primary` | `#1a1a1a` | 正文 |
| `--color-text-secondary` | `#5c5c5c` | 辅助 |
| `--color-text-tertiary` | `#8c8a7a` | 提示 |
| `--color-border-default` | `#e8e6d8` | 边框 |

### 组件规范

- UI 组件库：Nuxt UI v4（UButton, UInput, USelect, UTabs, UFormField, UAlert, UProgress, UIcon）
- 图标：Heroicons（`i-heroicons-*`）
- 禁用 `transition: all`，仅对 opacity/transform/border-color 过渡
- 所有 UI 文本用 `$t()`，禁止硬编码
- 颜色统一通过 CSS 变量，禁止 inline style 硬编码色值

### 布局模式

- 工具页面：`<PageHeader />` + 功能组件
- 子功能（文件组装/水印管理）：卡片式模式切换（grid 2 列）
- 新增工具：pages/ 创建路由 + Sidebar 添加导航 + Dashboard 添加卡片 + i18n 添加键

## 参考文档

- [前端框架迁移指南](docs/nuxt-migration-guide.md) — Buefy → Nuxt UI 迁移方法、步骤、注意事项

## 常见命令

```bash
# 清理
find . -name "__pycache__" -exec rm -rf {} +
rm -rf frontend/.nuxt frontend/.output

# 安装前端依赖
cd frontend && npm install

# 安装后端依赖
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    python-docx openpyxl python-pptx markdown bleach img2pdf pypdf Pillow reportlab gunicorn
```
