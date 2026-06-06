# docStamp — 文档处理工具箱

一站式文档处理 Web 应用，集成 Markdown 转公文、属性修改、文件组装、PDF 编辑、水印管理、Excel 合并、电子书转换等 9 大功能。

## 功能

| # | 功能 | 路由 | 说明 |
|---|------|------|------|
| 1 | **MD 转公文** | `/md-to-docx` | Markdown → GB/T 9704-2012 DOCX，实时预览，语法高亮 |
| 2 | **属性修改** | `/properties` | 修改 `.docx/.xlsx/.pptx` 元数据，批量/统一时间 |
| 3 | **文件组装** | `/file-assembly` | 图片合并 PDF + PDF 拆解为图片 |
| 4 | **打印分组** | `/print-split` | PDF 按批次拆分，暂停/继续/终止 |
| 5 | **水印管理** | `/watermark` | 添加/去除文字和图片水印 |
| 6 | **PDF 编辑** | `/pdf-editor` | 删除/插入/重排页面，缩略图预览 |
| 7 | **Excel 合并** | `/excel-merge` | 合并 `.xlsx/.csv`，相同结构 |
| 8 | **电子书转 MD** | `/ebook-to-md` | Word/电子书 → Markdown |
| 9 | **格式规范** | `/format-docx` | DOCX 按 GB/T 9704-2012 格式化 |

## 技术栈

- **后端**: Python Flask + Pandoc + LibreOffice + Calibre + poppler-utils
- **前端**: Nuxt 4 + Nuxt UI v4 + Tailwind CSS v4 + Nuxt i18n
- **部署**: systemd / Docker Compose

## 快速开始

```bash
# 安装依赖
cd backend && pip3 install --break-system-packages flask flask-cors flask-babel \
    python-docx openpyxl python-pptx markdown bleach img2pdf pypdf Pillow reportlab gunicorn
cd ../frontend && npm install

# 开发环境
./manage.sh start

# 运行测试
./manage.sh test
```

## 生产部署

```bash
# systemd
sudo bash scripts/install.sh install

# Docker
sudo bash scripts/install.sh install --docker
```

## 项目结构

```
docStamp/
├── backend/                  # Flask API（9 模块 + 24 端点）
│   ├── app.py                # 主程序
│   ├── converter.py          # 文档转换引擎
│   ├── formatter.py          # GB/T 9704-2012 格式化
│   └── tests/                # 27 tests
├── frontend/                 # Nuxt 4 SPA（10 页面 + 15 组件）
│   ├── pages/                # 路由页面
│   ├── components/           # 组件
│   └── i18n/locales/         # zh-CN / en
├── manage.sh                 # 开发管理
├── Dockerfile
└── SPEC.md                   # 设计规范
```

## 系统要求

- Python 3.12+
- Node.js 22+
- Pandoc, LibreOffice (headless), Calibre, poppler-utils
