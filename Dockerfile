# ── Stage 1: Build Nuxt frontend ───────────────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ────────────────────────────────────────
FROM python:3.12-slim-bookworm
WORKDIR /opt/docstamp

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry -i https://mirrors.aliyun.com/pypi/simple/

# Install Python dependencies
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy backend code and frontend build
COPY backend/ ./
COPY --from=frontend-build /app/frontend/.output/public ./frontend/.output/public

# Create log directory
RUN mkdir -p /var/log/docstamp && chmod 755 /var/log/docstamp

# Create output directory
RUN mkdir -p /opt/docstamp/output

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
