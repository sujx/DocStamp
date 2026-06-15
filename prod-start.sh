#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# docStamp 生产模式启动脚本
# 单端口 :5000 — Gunicorn 同时提供 API + 前端静态文件
# ───────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PORT=5000

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'

log_info()  { echo -e "${GREEN}[prod]${NC} $*"; }
log_error() { echo -e "${RED}[prod]${NC} $*"; }

# ── Stop existing processes ────────────────────────────────────────
log_info "清理旧进程..."
fuser -k "$BACKEND_PORT/tcp" 2>/dev/null || true
sleep 1

# ── Build frontend if needed ───────────────────────────────────────
if [[ ! -f "$FRONTEND_DIR/.output/public/index.html" ]]; then
    log_info "构建前端..."
    cd "$FRONTEND_DIR" && npm install && npm run build && cd "$PROJECT_DIR"
else
    log_info "前端已构建，跳过 build"
fi

# ── Load environment ───────────────────────────────────────────────
# Priority: /etc/docstamp/env.conf > project .env > shell env
for f in /etc/docstamp/env.conf "$PROJECT_DIR/.env"; do
  if [[ -f "$f" ]]; then
    set -a; source "$f"; set +a
    log_info "已加载环境变量: $f"
  fi
done

# ── Start Gunicorn ─────────────────────────────────────────────────
# Prefer venv gunicorn (has all deps). Fall back to system gunicorn.
if [[ -x "$BACKEND_DIR/.venv/bin/gunicorn" ]]; then
    GUNICORN="$BACKEND_DIR/.venv/bin/gunicorn"
    log_info "使用 venv gunicorn"
else
    GUNICORN="gunicorn"
fi
log_info "启动 Gunicorn (4 workers, :$BACKEND_PORT)..."
cd "$BACKEND_DIR"
"$GUNICORN" -c gunicorn.conf.py wsgi:app &
GUNICORN_PID=$!
cd "$PROJECT_DIR"

echo "$GUNICORN_PID" > "$PROJECT_DIR/.pids/backend.pid"

# ── Health check ───────────────────────────────────────────────────
log_info "等待服务就绪..."
for i in $(seq 1 15); do
    if curl -s -o /dev/null "http://localhost:$BACKEND_PORT/api/health" 2>/dev/null; then
        log_info "═══════════════════════════════════════"
        log_info "  生产模式已启动"
        log_info "  API:    http://0.0.0.0:$BACKEND_PORT/api/health"
        log_info "  前端:    http://0.0.0.0:$BACKEND_PORT/"
        log_info "  PID:    $GUNICORN_PID"
        log_info "═══════════════════════════════════════"
        exit 0
    fi
    sleep 0.5
done

log_error "启动超时，请查看日志"
exit 1
