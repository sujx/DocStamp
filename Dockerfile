# ── Stage 1: Build Nuxt 3 frontend ──────────────────────────────────
FROM node:24-alpine AS frontend-build

# Alibaba Cloud npm mirror
RUN npm config set registry https://registry.npmmirror.com

# Update npm for latest dependency resolution and security fixes
RUN npm install -g npm@latest

WORKDIR /app/frontend
# Only copy package.json — fresh resolution each build within semver ranges.
# --legacy-peer-deps handles @vuelidate/core <-> vue2/3 peer conflict.
COPY frontend/package.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund
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
    libreoffice-writer \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-noto-cjk \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Alibaba Cloud PyPI mirror
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# Install Python dependencies
COPY backend/pyproject.toml ./
RUN pip install --break-system-packages --no-cache-dir --root-user-action=ignore \
    flask flask-cors flask-babel flask-caching \
    python-docx openpyxl python-pptx \
    markdown bleach img2pdf pypdf Pillow reportlab \
    gunicorn pydantic celery redis cryptography weasyprint pdfminer.six

# Copy backend code
COPY backend/ ./backend/

# Python path — needed so that 'from config import Config' works inside the
# backend package when gunicorn imports 'backend.app:app'
ENV PYTHONPATH=/opt/docstamp/backend

# Copy frontend static build
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public

# Entrypoint (copied before USER so root can chmod it)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Runtime directories (match UPLOAD_FOLDER default in backend/config.py)
RUN mkdir -p /var/log/docstamp /opt/docstamp/backend/output \
    && chmod 755 /var/log/docstamp /opt/docstamp/backend/output

# Non-root user for production security
RUN useradd --create-home --shell /bin/bash docstamp \
    && chown -R docstamp:docstamp /opt/docstamp /var/log/docstamp
USER docstamp

EXPOSE 5000

# -b 0.0.0.0:5000 overrides gunicorn.conf.py's 127.0.0.1 binding for Docker
# --pid /tmp/gunicorn.pid avoids /var/run permission issues with non-root user
CMD ["gunicorn", "-c", "backend/gunicorn.conf.py", "-b", "0.0.0.0:5000", \
     "--pid", "/tmp/gunicorn.pid", "backend.app:app"]
