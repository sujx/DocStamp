#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# docStamp 安装脚本
#
# Usage:
#   sudo bash scripts/install.sh install          # 本地 systemd 部署
#   sudo bash scripts/install.sh update           # 更新
#   sudo bash scripts/install.sh uninstall        # 卸载
#   sudo bash scripts/install.sh install --docker # Docker 部署
# ───────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_USER="docstamp"
APP_DIR="/opt/docstamp"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="/var/log/docstamp"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
log_info()  { echo -e "${GREEN}[install]${NC} $*"; }
log_error() { echo -e "${RED}[install]${NC} $*"; }

_install_system_deps() {
    log_info "安装系统依赖..."
    if command -v apt-get &>/dev/null; then
        apt-get update
        apt-get install -y python3 python3-venv python3-pip \
            nodejs npm curl fonts-noto-cjk libreoffice-core
        # Install Poetry
        if ! command -v poetry &>/dev/null; then
            curl -sSL https://install.python-poetry.org | python3 -
        fi
    elif command -v dnf &>/dev/null; then
        dnf install -y python3 python3-pip nodejs npm curl google-noto-cjk-fonts
        if ! command -v poetry &>/dev/null; then
            curl -sSL https://install.python-poetry.org | python3 -
        fi
    else
        log_error "不支持的操作系统"
        exit 1
    fi
}

_create_user() {
    if ! id -u "$APP_USER" &>/dev/null; then
        log_info "创建系统用户: $APP_USER"
        useradd -r -s /usr/sbin/nologin -d "$APP_DIR" "$APP_USER"
    fi
}

_setup_dirs() {
    log_info "创建目录结构..."
    mkdir -p "$APP_DIR" "$LOG_DIR" "$APP_DIR/backend/output"
    chown -R "$APP_USER:$APP_USER" "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    touch /var/run/docstamp.pid
    chown "$APP_USER:$APP_USER" /var/run/docstamp.pid
}

_install_venv() {
    log_info "创建虚拟环境并安装依赖..."
    python3 -m venv "$VENV_DIR"
    # Install Poetry in venv
    "$VENV_DIR/bin/pip" install poetry
    cd "$BACKEND_DIR"
    "$VENV_DIR/bin/poetry" config virtualenvs.create false
    "$VENV_DIR/bin/poetry" install --no-dev --no-interaction --no-ansi
    cd "$PROJECT_DIR"
}

_build_frontend() {
    log_info "构建前端..."
    cd "$FRONTEND_DIR"
    npm install --registry=https://registry.npmmirror.com
    npm run build
    cd "$PROJECT_DIR"
}

_install_redis() {
    log_info "安装 Redis..."
    if command -v apt-get &>/dev/null; then
        apt-get install -y redis
    elif command -v dnf &>/dev/null; then
        dnf install -y redis
    fi
    # Tune for low memory
    sed -i 's/^# maxmemory .*/maxmemory 128mb/' /etc/redis/redis.conf 2>/dev/null || true
    sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf 2>/dev/null || true
    systemctl enable --now redis
}

_install_systemd() {
    log_info "安装 systemd 服务..."
    cp "$PROJECT_DIR/deploy/docstamp.service" /etc/systemd/system/docstamp.service
    systemctl daemon-reload
    systemctl enable docstamp
    systemctl start docstamp
    log_info "docStamp 服务已启动"
}

_install_systemd_lite() {
    log_info "安装 systemd 服务 (lite: API + Celery + Beat)..."
    cp "$PROJECT_DIR/deploy/docstamp.service" /etc/systemd/system/docstamp.service
    cp "$PROJECT_DIR/deploy/docstamp-celery.service" /etc/systemd/system/docstamp-celery.service
    cp "$PROJECT_DIR/deploy/docstamp-beat.service" /etc/systemd/system/docstamp-beat.service
    systemctl daemon-reload
    systemctl enable docstamp docstamp-celery docstamp-beat
    systemctl start docstamp docstamp-celery docstamp-beat
    log_info "docStamp (lite) 3 个服务已启动"
}

_install_logrotate() {
    log_info "安装 logrotate 配置..."
    cp "$PROJECT_DIR/logrotate.conf" /etc/logrotate.d/docstamp
}

_install_docker_full() {
    log_info "使用 Docker Compose (full: 6 容器) 部署..."
    cd "$PROJECT_DIR"
    docker compose up -d --build
    log_info "Docker (full) 部署完成 → http://localhost:5000"
    docker compose ps
}

_install_docker_lite() {
    log_info "使用 Docker Compose (lite: 3 容器) 部署..."
    cd "$PROJECT_DIR"
    docker compose -f docker-compose.lite.yml up -d --build
    log_info "Docker (lite) 部署完成 → http://localhost:5000"
    docker compose -f docker-compose.lite.yml ps
}

_update_local() {
    local mode="${1:-full}"
    log_info "更新 docStamp (${mode})..."
    if [[ "$mode" == "lite" ]]; then
        systemctl stop docstamp docstamp-celery docstamp-beat 2>/dev/null || true
    else
        systemctl stop docstamp || true
    fi
    cp -r "$PROJECT_DIR/backend"/*.py "$BACKEND_DIR/"
    cp "$PROJECT_DIR/backend/pyproject.toml" "$BACKEND_DIR/"
    "$VENV_DIR/bin/pip" install --no-cache-dir \
        flask flask-cors flask-babel flask-caching \
        python-docx openpyxl python-pptx markdown bleach \
        img2pdf pypdf Pillow reportlab gunicorn pydantic \
        celery redis cryptography weasyprint pdfminer.six
    cp -r "$PROJECT_DIR/frontend"/* "$FRONTEND_DIR/"
    cd "$FRONTEND_DIR" && npm install && npm run build && cd "$PROJECT_DIR"
    if [[ "$mode" == "lite" ]]; then
        systemctl start docstamp docstamp-celery docstamp-beat
    else
        systemctl start docstamp
    fi
    log_info "更新完成"
}

_uninstall_local() {
    log_info "卸载 docStamp..."
    systemctl stop docstamp docstamp-celery docstamp-beat 2>/dev/null || true
    systemctl disable docstamp docstamp-celery docstamp-beat 2>/dev/null || true
    rm -f /etc/systemd/system/docstamp.service
    rm -f /etc/systemd/system/docstamp-celery.service
    rm -f /etc/systemd/system/docstamp-beat.service
    rm -f /etc/logrotate.d/docstamp
    systemctl daemon-reload
    rm -rf "$APP_DIR"
    rm -f /var/run/docstamp.pid
    log_info "删除日志目录? (y/N)"
    read -r ans
    if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
        rm -rf "$LOG_DIR"
    fi
    userdel "$APP_USER" 2>/dev/null || true
    log_info "卸载完成"
}

case "${1:-}" in
    install)
        if [[ "${2:-}" == "--docker" ]]; then
            _install_docker_full
        elif [[ "${2:-}" == "--docker-lite" ]]; then
            _install_docker_lite
        elif [[ "${2:-}" == "--lite" ]]; then
            _install_system_deps
            _install_redis
            _create_user
            _setup_dirs
            cp -r "$PROJECT_DIR/backend" "$APP_DIR/"
            cp -r "$PROJECT_DIR/frontend" "$APP_DIR/"
            _install_venv
            _build_frontend
            _install_logrotate
            _install_systemd_lite
            log_info "══════ 安装完成 (lite) ══════"
            log_info "API:     http://localhost:5000"
            log_info "服务:     systemctl status docstamp docstamp-celery docstamp-beat"
        else
            _install_system_deps
            _install_redis
            _create_user
            _setup_dirs
            cp -r "$PROJECT_DIR/backend" "$APP_DIR/"
            cp -r "$PROJECT_DIR/frontend" "$APP_DIR/"
            _install_venv
            _build_frontend
            _install_logrotate
            _install_systemd
            log_info "══════ 安装完成 (full) ══════"
            log_info "API:     http://localhost:5000"
            log_info "提示:     生产环境需额外部署 Celery Worker 容器或 systemd 服务"
        fi
        ;;
    update)
        if [[ "${2:-}" == "--docker" ]]; then
            cd "$PROJECT_DIR" && docker compose up -d --build
        elif [[ "${2:-}" == "--docker-lite" ]]; then
            cd "$PROJECT_DIR" && docker compose -f docker-compose.lite.yml up -d --build
        elif [[ "${2:-}" == "--lite" ]]; then
            _update_local lite
        else
            _update_local full
        fi
        ;;
    uninstall)
        if [[ "${2:-}" == "--docker" ]]; then
            cd "$PROJECT_DIR" && docker compose down -v
        elif [[ "${2:-}" == "--docker-lite" ]]; then
            cd "$PROJECT_DIR" && docker compose -f docker-compose.lite.yml down -v
        else
            _uninstall_local
        fi
        ;;
    *)
        echo "用法: $0 <install|update|uninstall> [--docker|--docker-lite|--lite]"
        echo ""
        echo "模式:"
        echo "  (默认)        裸机 full — API systemd 服务"
        echo "  --lite        裸机 lite — API + Celery + Beat systemd 服务 (2C2G)"
        echo "  --docker      Docker full — 6 容器 (4GB+)"
        echo "  --docker-lite Docker lite — 3 容器 (2C2G)"
        exit 1
        ;;
esac
