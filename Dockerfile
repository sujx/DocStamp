# ── Stage 1: Build Nuxt 3 frontend ──────────────────────────────────
FROM node:22-alpine AS frontend-build

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
    gunicorn pydantic celery cryptography

# Copy backend code
COPY backend/ ./

# Copy frontend static build
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public

# Runtime directories
RUN mkdir -p /var/log/docstamp /opt/docstamp/output \
    && chmod 755 /var/log/docstamp /opt/docstamp/output

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
