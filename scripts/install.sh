#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# 鹊随金印 (docStamp) 安装 / 更新 / 卸载脚本
#
# Usage:
#   sudo bash install.sh install              # 裸机 full（仅 API systemd 服务）
#   sudo bash install.sh install --lite       # 裸机 lite（API + Celery + Beat，2C2G）
#   sudo bash install.sh install --docker     # Docker full（6 容器，4GB+）
#   sudo bash install.sh install --docker-lite # Docker lite（3 容器，2C2G）
#   sudo bash install.sh update [--lite]      # 更新
#   sudo bash install.sh uninstall            # 卸载
# ───────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_USER="docstamp"
APP_DIR="/opt/docstamp"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="/var/log/docstamp"
OUTPUT_DIR="$APP_DIR/output"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_info()  { echo -e "${GREEN}[docStamp]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[docStamp]${NC} $*"; }
log_error() { echo -e "${RED}[docStamp]${NC} $*"; }

# ── Detect package manager ──────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v yum &>/dev/null; then
    PKG_MGR="yum"
else
    log_error "不支持的操作系统（需要 apt / dnf / yum）"
    exit 1
fi

# ── System dependencies ─────────────────────────────────────────────
_install_system_deps() {
    log_info "安装系统依赖..."

    case "$PKG_MGR" in
        apt)
            apt-get update -qq
            apt-get install -y --no-install-recommends \
                python3 python3-venv python3-pip python3-dev \
                pandoc poppler-utils curl procps \
                fonts-noto-cjk
            # Node.js — use NodeSource for up-to-date version
            if ! command -v node &>/dev/null; then
                curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
                apt-get install -y nodejs
            fi
            ;;
        dnf|yum)
            $PKG_MGR install -y epel-release 2>/dev/null || true
            $PKG_MGR install -y \
                python3 python3-pip python3-devel \
                pandoc poppler-utils curl procps-ng \
                google-noto-cjk-fonts
            # Node.js
            if ! command -v node &>/dev/null; then
                curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
                $PKG_MGR install -y nodejs
            fi
            ;;
    esac

    log_info "系统依赖安装完成"
}

# ── Message broker (Redis / Valkey) ──────────────────────────────────
_install_broker() {
    local broker="redis"
    local broker_conf=""

    if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet valkey 2>/dev/null; then
        log_info "消息代理已在运行，跳过安装"
        return 0
    fi

    case "$PKG_MGR" in
        apt)
            broker="redis"
            log_info "安装 Redis..."
            apt-get install -y redis
            broker_conf="/etc/redis/redis.conf"
            ;;
        dnf|yum)
            broker="valkey"
            log_info "安装 Valkey（RHEL 10+ 的 Redis 替代）..."
            $PKG_MGR install -y valkey
            broker_conf="/etc/valkey/valkey.conf"
            ;;
    esac

    # Low-memory tuning
    if [[ -n "$broker_conf" && -f "$broker_conf" ]]; then
        grep -q '^maxmemory ' "$broker_conf" 2>/dev/null \
            && sed -i 's/^maxmemory .*/maxmemory 128mb/' "$broker_conf" \
            || echo "maxmemory 128mb" >> "$broker_conf"
        grep -q '^maxmemory-policy ' "$broker_conf" 2>/dev/null \
            && sed -i 's/^maxmemory-policy .*/maxmemory-policy allkeys-lru/' "$broker_conf" \
            || echo "maxmemory-policy allkeys-lru" >> "$broker_conf"
    fi

    systemctl enable --now "$broker"
    log_info "$broker 已启动"
}

# ── App user & directories ──────────────────────────────────────────
_create_user() {
    if id -u "$APP_USER" &>/dev/null; then
        log_info "用户 $APP_USER 已存在"
    else
        useradd -r -s /usr/sbin/nologin -d "$APP_DIR" "$APP_USER"
        log_info "已创建系统用户: $APP_USER"
    fi
}

_setup_dirs() {
    log_info "创建目录..."
    mkdir -p "$APP_DIR" "$LOG_DIR" "$OUTPUT_DIR"
    chown -R "$APP_USER:$APP_USER" "$LOG_DIR" "$OUTPUT_DIR" 2>/dev/null || true
    chmod 755 "$LOG_DIR" "$OUTPUT_DIR"
}

# ── Python virtualenv ───────────────────────────────────────────────
_install_venv() {
    log_info "创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip -q

    log_info "安装 Python 依赖..."
    "$VENV_DIR/bin/pip" install --no-cache-dir \
        flask flask-cors flask-babel flask-caching \
        python-docx openpyxl python-pptx \
        markdown bleach img2pdf pypdf Pillow reportlab \
        gunicorn pydantic celery redis cryptography \
        pdfminer.six requests python-dotenv

    log_info "Python 依赖安装完成"
}

# ── Frontend build ──────────────────────────────────────────────────
_build_frontend() {
    log_info "构建前端..."
    cd "$FRONTEND_DIR"

    # Prevent OOM during Vite/esbuild transform (echarts, mermaid are heavy)
    export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=4096"

    # Set npm mirror for faster install in China
    npm config set registry https://registry.npmmirror.com 2>/dev/null || true
    npm install
    npm run build

    cd "$PROJECT_DIR"
    log_info "前端构建完成"
}

# ── Copy app files ──────────────────────────────────────────────────
_copy_app() {
    log_info "部署应用文件到 $APP_DIR ..."

    # Backend: exclude venv, cache, tests, output
    rsync -a --delete \
        --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.pytest_cache' --exclude='tests/' \
        --exclude='output/*' --exclude='tasks.db*' \
        "$PROJECT_DIR/backend/" "$BACKEND_DIR/"

    # Frontend: exclude node_modules, build cache
    rsync -a --delete \
        --exclude='node_modules' --exclude='.nuxt' --exclude='.output' \
        "$PROJECT_DIR/frontend/" "$FRONTEND_DIR/"

    # Deploy configs
    cp "$PROJECT_DIR/deploy/env.conf" /etc/docstamp/env.conf 2>/dev/null || true

    # Fix ownership
    chown -R "$APP_USER:$APP_USER" "$APP_DIR" 2>/dev/null || true

    log_info "应用文件部署完成"
}

# ── Systemd services ────────────────────────────────────────────────
_install_systemd() {
    log_info "安装 systemd 服务 (full: 仅 API)..."
    cp "$PROJECT_DIR/deploy/docstamp.service" /etc/systemd/system/docstamp.service
    systemctl daemon-reload
    systemctl enable docstamp
    systemctl start docstamp
    log_info "docStamp API 已启动 → http://localhost:5000"
}

_install_systemd_lite() {
    log_info "安装 systemd 服务 (lite: API + Celery + Beat)..."
    cp "$PROJECT_DIR/deploy/docstamp.service" /etc/systemd/system/docstamp.service
    cp "$PROJECT_DIR/deploy/docstamp-celery.service" /etc/systemd/system/docstamp-celery.service
    cp "$PROJECT_DIR/deploy/docstamp-beat.service" /etc/systemd/system/docstamp-beat.service
    systemctl daemon-reload
    systemctl enable docstamp docstamp-celery docstamp-beat
    systemctl start docstamp docstamp-celery docstamp-beat
    log_info "docStamp (lite) 已启动 → http://localhost:5000"
}

# ── Logrotate ───────────────────────────────────────────────────────
_install_logrotate() {
    if [[ -f "$PROJECT_DIR/deploy/logrotate.conf" ]]; then
        cp "$PROJECT_DIR/deploy/logrotate.conf" /etc/logrotate.d/docstamp
        log_info "logrotate 已配置"
    else
        # Generate default
        cat > /etc/logrotate.d/docstamp <<'EOF'
/var/log/docstamp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
        log_info "logrotate 已配置（默认）"
    fi
}

# ── Docker ──────────────────────────────────────────────────────────
_install_docker_full() {
    log_info "Docker Compose (full: 6 容器) 部署..."
    cd "$PROJECT_DIR"
    docker compose up -d --build
    echo ""
    docker compose ps
    log_info "Docker (full) 部署完成 → http://localhost:5000"
}

_install_docker_lite() {
    log_info "Docker Compose (lite: 3 容器) 部署..."
    cd "$PROJECT_DIR"
    docker compose -f docker-compose.lite.yml up -d --build
    echo ""
    docker compose -f docker-compose.lite.yml ps
    log_info "Docker (lite) 部署完成 → http://localhost:5000"
}

# ── Update ──────────────────────────────────────────────────────────
_update_local() {
    local mode="${1:-full}"
    log_info "更新 docStamp (${mode})..."

    if [[ "$mode" == "lite" ]]; then
        systemctl stop docstamp docstamp-celery docstamp-beat 2>/dev/null || true
    else
        systemctl stop docstamp 2>/dev/null || true
    fi

    # Re-deploy code
    rsync -a --delete \
        --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.pytest_cache' --exclude='tests/' \
        --exclude='output/*' --exclude='tasks.db*' \
        "$PROJECT_DIR/backend/" "$BACKEND_DIR/"

    rsync -a --delete \
        --exclude='node_modules' --exclude='.nuxt' --exclude='.output' \
        "$PROJECT_DIR/frontend/" "$FRONTEND_DIR/"

    # Re-install deps
    "$VENV_DIR/bin/pip" install --no-cache-dir --upgrade \
        flask flask-cors flask-babel flask-caching \
        python-docx openpyxl python-pptx markdown bleach \
        img2pdf pypdf Pillow reportlab gunicorn pydantic \
        celery redis cryptography pdfminer.six requests

    # Rebuild frontend
    export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=4096"
    cd "$FRONTEND_DIR"
    npm install --registry=https://registry.npmmirror.com
    npm run build
    cd "$PROJECT_DIR"

    # Restart
    if [[ "$mode" == "lite" ]]; then
        systemctl start docstamp docstamp-celery docstamp-beat
    else
        systemctl start docstamp
    fi

    log_info "更新完成"
}

# ── Uninstall ───────────────────────────────────────────────────────
_uninstall_local() {
    log_info "卸载 docStamp..."

    # Stop & remove services
    for svc in docstamp docstamp-celery docstamp-beat; do
        systemctl stop "$svc" 2>/dev/null || true
        systemctl disable "$svc" 2>/dev/null || true
        rm -f "/etc/systemd/system/${svc}.service"
    done
    rm -f /etc/logrotate.d/docstamp
    systemctl daemon-reload

    # Remove app files
    rm -rf "$APP_DIR"

    # Remove user
    userdel "$APP_USER" 2>/dev/null || true

    # Optionally remove logs
    echo ""
    log_warn "删除日志目录 $LOG_DIR ? (y/N)"
    read -r ans
    if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
        rm -rf "$LOG_DIR"
    fi

    log_info "卸载完成"
}

# ── Show usage ──────────────────────────────────────────────────────
_usage() {
    echo ""
    echo "鹊随金印 (docStamp) 安装脚本"
    echo ""
    echo "用法: $0 <command> [flag]"
    echo ""
    echo "命令:"
    echo "  install         安装（默认 full 模式）"
    echo "  update          更新已有安装"
    echo "  uninstall       卸载"
    echo ""
    echo "标志:"
    echo "  --lite          精简模式（2C2G ECS，Redis + API + Celery + Beat）"
    echo "  --docker        Docker Full（6 容器，4GB+ 推荐）"
    echo "  --docker-lite   Docker Lite（3 容器，2C2G 推荐）"
    echo ""
    echo "示例:"
    echo "  sudo bash install.sh install --lite       # 2C2G ECS 一键部署"
    echo "  sudo bash install.sh install --docker-lite # Docker 精简部署"
    echo "  sudo bash install.sh update --lite         # 更新精简模式"
    echo "  sudo bash install.sh uninstall             # 卸载"
    echo ""
}

# ── Main ────────────────────────────────────────────────────────────

# Must run as root
if [[ $EUID -ne 0 ]]; then
    log_error "请使用 sudo 运行"
    exit 1
fi

case "${1:-}" in
    install)
        case "${2:-}" in
            --docker)
                _install_docker_full
                ;;
            --docker-lite)
                _install_docker_lite
                ;;
            --lite)
                _install_system_deps
                _install_broker
                _create_user
                _setup_dirs
                _copy_app
                _install_venv
                _build_frontend
                _install_logrotate
                _install_systemd_lite
                echo ""
                log_info "══════ 安装完成 (lite) ══════"
                log_info "API:     http://localhost:5000/api/health"
                log_info "前端:     http://localhost:5000"
                log_info "服务:     systemctl status docstamp docstamp-celery docstamp-beat"
                echo ""
                ;;
            *)
                _install_system_deps
                _install_broker
                _create_user
                _setup_dirs
                _copy_app
                _install_venv
                _build_frontend
                _install_logrotate
                _install_systemd
                echo ""
                log_info "══════ 安装完成 (full) ══════"
                log_info "API:     http://localhost:5000/api/health"
                log_warn "Celery Worker/Beat 请另行部署（参考 SPEC.md 九、部署）"
                echo ""
                ;;
        esac
        ;;
    update)
        case "${2:-}" in
            --docker)       cd "$PROJECT_DIR" && docker compose up -d --build ;;
            --docker-lite)  cd "$PROJECT_DIR" && docker compose -f docker-compose.lite.yml up -d --build ;;
            --lite)         _update_local lite ;;
            *)              _update_local full ;;
        esac
        ;;
    uninstall)
        case "${2:-}" in
            --docker)       cd "$PROJECT_DIR" && docker compose down -v ;;
            --docker-lite)  cd "$PROJECT_DIR" && docker compose -f docker-compose.lite.yml down -v ;;
            *)              _uninstall_local ;;
        esac
        ;;
    *)
        _usage
        ;;
esac
