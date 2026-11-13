# ── Stage 1: Build Nuxt 3 frontend ──────────────────────────────────
FROM node:22-alpine AS frontend-build

# Alibaba Cloud npm mirror + upgrade npm (fixes tar@6.2.1 deprecation)
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g npm@latest

WORKDIR /app/frontend
# Lockfile ensures reproducible builds across machines.
# --legacy-peer-deps handles @vuelidate/core <-> vue2/3 peer conflict.
COPY frontend/package*.json ./
# retry once in case of ETXTBSY (esbuild binary write/exec race on overlay2)
RUN npm ci --legacy-peer-deps --no-audit --no-fund || \
    sleep 2 && npm ci --legacy-peer-deps --no-audit --no-fund
COPY frontend/ ./
# 2GB for build heap — Docker build usually has >2GB available.
# For constrained CI, override: docker build --build-arg NODE_HEAP=1536 .
ARG NODE_HEAP=2048
ENV NODE_OPTIONS="--max-old-space-size=${NODE_HEAP}"

# BUST_FRONTEND: pass --build-arg BUST_FRONTEND=$(date +%s) to force
# npm run build to re-execute while keeping npm ci + apt + uv cached.
# Must be referenced in the RUN command itself, not just declared as ARG.
ARG BUST_FRONTEND
RUN BUST_FRONTEND=${BUST_FRONTEND} npm run build

# ── Stage 2: Resolve Python dependencies with uv ─────────────────────
# Own stage so uv and its cache never reach the runtime image — Stage 3 copies
# the finished venv out. MUST use the same base as Stage 3: the venv's
# interpreter is a symlink to /usr/local/bin/python3.13.
FROM python:3.13-slim-bookworm AS backend-deps

# Both indexes point at the Aliyun mirror the old pip install used; this box
# and the ECS host sit behind the CN network where pypi.org crawls.
# uv itself is pinned because backend/uv.lock is written at lock revision 5.
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    UV_NO_CACHE=1
RUN pip install --no-cache-dir --break-system-packages uv==0.13.7

WORKDIR /opt/docstamp
# Lock and manifest only: this layer re-runs when dependencies change, not on
# every code edit. `package = false` means uv never needs the source tree.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# ── Stage 3: Python 3.13 runtime ─────────────────────────────────────
FROM python:3.13-slim-bookworm

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
    procps \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Runtime dependencies come from the uv-resolved venv, so there is no install
# list here to drift out of sync with backend/pyproject.toml any more.
# `gunicorn --version` also proves the venv is on PATH before anything else.
COPY --from=backend-deps /opt/docstamp/.venv /opt/docstamp/.venv
ENV PATH="/opt/docstamp/.venv/bin:${PATH}"
RUN gunicorn --version \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip \
    && rm -rf /usr/local/lib/python3.13/site-packages/setuptools \
    && find /usr/local/lib/python3.13 /opt/docstamp/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true \
    && find /usr/local/lib/python3.13 /opt/docstamp/.venv -type f -name "*.pyc" -delete 2>/dev/null; true \
    && find /opt/docstamp/.venv/lib/python3.13/site-packages/babel/locale-data -type f \
        ! -name "en*" ! -name "zh*" -delete 2>/dev/null; true

# Copy backend code
COPY backend/ ./backend/

# Python path — needed so that 'from config import Config' works inside the
# backend package when gunicorn imports 'backend.wsgi:app'
ENV PYTHONPATH=/opt/docstamp/backend

# Copy frontend static build
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public

# Entrypoint (copied before USER so root can chmod it)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Runtime directories (match UPLOAD_FOLDER default in backend/config.py)
RUN mkdir -p /var/log/docstamp /opt/docstamp/backend/output /opt/docstamp/backend/data \
    && chmod 755 /var/log/docstamp /opt/docstamp/backend/output /opt/docstamp/backend/data

# Non-root user for production security
RUN useradd --create-home --shell /bin/bash docstamp \
    && chown -R docstamp:docstamp /opt/docstamp /var/log/docstamp
USER docstamp

EXPOSE 5000

# -b 0.0.0.0:5000 overrides gunicorn.conf.py's 127.0.0.1 binding for Docker
# --pid /tmp/gunicorn.pid avoids /var/run permission issues with non-root user
# Uses wsgi.py (not app.py) to avoid module-level side effects on import
CMD ["gunicorn", "-c", "backend/gunicorn.conf.py", "-b", "0.0.0.0:5000", \
     "--pid", "/tmp/gunicorn.pid", "backend.wsgi:app"]
