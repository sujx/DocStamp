# ── Stage 1: Build Nuxt 3 frontend ──────────────────────────────────
FROM node:24-alpine AS frontend-build

# Alibaba Cloud npm mirror
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python 3.12 runtime ────────────────────────────────────
FROM python:3.12-slim-bookworm

# Alibaba Cloud Debian mirror
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

WORKDIR /opt/docstamp

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    poppler-utils \
    libreoffice-core \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-noto-cjk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Alibaba Cloud PyPI mirror
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# Install Python dependencies
COPY backend/pyproject.toml ./
RUN pip install --break-system-packages --no-cache-dir \
    flask flask-cors flask-babel flask-caching \
    python-docx openpyxl python-pptx \
    markdown bleach img2pdf pypdf Pillow reportlab \
    gunicorn pydantic celery redis cryptography weasyprint pdfminer.six

# Copy backend code
COPY backend/ ./backend/

# Copy frontend static build
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public

# Runtime directories (match UPLOAD_FOLDER default in backend/config.py)
RUN mkdir -p /var/log/docstamp /opt/docstamp/backend/output \
    && chmod 755 /var/log/docstamp /opt/docstamp/backend/output

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:5000/api/health || exit 1

# -b 0.0.0.0:5000 overrides gunicorn.conf.py's 127.0.0.1 binding for Docker
CMD ["gunicorn", "-c", "backend/gunicorn.conf.py", "-b", "0.0.0.0:5000", "backend.app:app"]
