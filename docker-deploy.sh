#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# 鹊随金印 (docStamp) Docker 部署脚本
#
# Full 模式: 6 容器（docker-compose.yml）
#   api + redis + celery-convert + celery-pdf + celery-office + celery-beat
#   3 个 Celery 队列独立隔离，高并发，适合 4GB+ 服务器
#
# Lite 模式: 3 容器（docker-compose.lite.yml）
#   api + redis + celery (合并 3 队列 + Beat 内嵌)
#   内存 ~800MB，适合 2C2G ECS
#
# Usage:
#   ./docker-deploy.sh build                # 构建镜像
#   ./docker-deploy.sh up                   # 启动 Full 模式
#   ./docker-deploy.sh up --lite            # 启动 Lite 模式
#   ./docker-deploy.sh down                 # 停止 Full 模式
#   ./docker-deploy.sh down --lite          # 停止 Lite 模式
#   ./docker-deploy.sh restart --lite       # 重启 Lite 模式
#   ./docker-deploy.sh ps                   # Full 模式状态
#   ./docker-deploy.sh ps --lite            # Lite 模式状态
#   ./docker-deploy.sh logs [service]       # 查看日志
#   ./docker-deploy.sh clean               # 停止并删除所有数据卷
# ───────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FULL="$PROJECT_DIR/docker-compose.yml"
COMPOSE_LITE="$PROJECT_DIR/docker-compose.lite.yml"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info()  { echo -e "${GREEN}[docker]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[docker]${NC} $*"; }
log_error() { echo -e "${RED}[docker]${NC} $*"; }
log_title() { echo -e "${CYAN}══════ $* ══════${NC}"; }

# ── Resolve mode, compose file, and extra args ─────────────────────
MODE="full"
COMPOSE_FILE="$COMPOSE_FULL"
COMPOSE_ARGS=()

_parse_mode() {
    MODE="full"
    COMPOSE_FILE="$COMPOSE_FULL"
    for arg in "$@"; do
        case "$arg" in
            --lite|-lite|lite)
                MODE="lite"
                COMPOSE_FILE="$COMPOSE_LITE"
                ;;
            *)
                COMPOSE_ARGS+=("$arg")
                ;;
        esac
    done
}

# ── Check prerequisites ─────────────────────────────────────────────
_check_docker() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker 未安装。请先安装 Docker: https://docs.docker.com/engine/install/"
        exit 1
    fi
    if ! docker compose version &>/dev/null; then
        log_error "Docker Compose 插件未安装。请安装 docker compose 插件。"
        exit 1
    fi
}

# ── Build ───────────────────────────────────────────────────────────
_build() {
    _parse_mode "$@"
    log_title "构建镜像 (${MODE})"
    log_info "Compose file: $COMPOSE_FILE"
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" build
    log_info "镜像构建完成"
    echo ""
    docker images | grep docstamp || true
}

# ── Start ───────────────────────────────────────────────────────────
_up() {
    _parse_mode "$@"
    log_title "启动 docStamp (${MODE})"

    # Show mode summary
    if [[ "$MODE" == "lite" ]]; then
        log_info "Lite 模式: 3 容器 | Celery 合并队列 | concurrency=2 | ~800MB"
    else
        log_info "Full 模式: 6 容器 | Celery 独立队列 | concurrency=4 | ~2.5GB"
    fi

    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" up -d --build

    # Wait & health check
    echo ""
    log_info "等待服务就绪..."
    sleep 8
    _ps
}

# ── Stop ────────────────────────────────────────────────────────────
_down() {
    _parse_mode "$@"
    log_title "停止 docStamp (${MODE})"
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" down
    log_info "已停止"
}

# ── Restart ─────────────────────────────────────────────────────────
_restart() {
    _parse_mode "$@"
    log_info "重启 (${MODE})..."
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" down
    sleep 2
    docker compose -f "$COMPOSE_FILE" up -d --build
    sleep 8
    _ps
}

# ── Status ──────────────────────────────────────────────────────────
_ps() {
    _parse_mode "$@"
    echo ""
    log_info "容器状态 (${MODE}):"
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" ps 2>/dev/null || {
        log_warn "无运行中的容器"
        return 0
    }
    echo ""

    # Quick health summary
    if [[ "$MODE" == "lite" ]]; then
        echo -n "API:  "
        curl -sf http://localhost:5000/api/health 2>/dev/null \
            && echo -e "${GREEN}✓ healthy${NC}" \
            || echo -e "${RED}✗ unreachable${NC}"
    else
        echo -n "API:  "
        curl -sf http://localhost:5000/api/health 2>/dev/null \
            && echo -e "${GREEN}✓ healthy${NC}" \
            || echo -e "${RED}✗ unreachable${NC}"
    fi
}

# ── Logs ────────────────────────────────────────────────────────────
_logs() {
    _parse_mode "$@"
    local svc="${COMPOSE_ARGS[0]:-}"
    cd "$PROJECT_DIR"
    if [[ -n "$svc" ]]; then
        docker compose -f "$COMPOSE_FILE" logs --tail=50 -f "$svc"
    else
        docker compose -f "$COMPOSE_FILE" logs --tail=30
    fi
}

# ── Clean (stop + remove volumes) ───────────────────────────────────
_clean() {
    _parse_mode "$@"
    echo ""
    log_warn "将删除所有容器、网络和数据卷（包括 Redis 数据、日志、输出文件）"
    echo -n "确认? (yes/no): "
    read -r ans
    if [[ "$ans" != "yes" ]]; then
        log_info "已取消"
        return 0
    fi
    log_title "清理 (${MODE})"
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" down -v
    log_info "已清理（容器 + 网络 + 数据卷）"
}

# ── Usage ───────────────────────────────────────────────────────────
_usage() {
    echo ""
    echo "docStamp Docker 部署脚本"
    echo ""
    echo "用法: $0 <command> [--lite] [options]"
    echo ""
    echo "命令:"
    echo "  build           构建 Docker 镜像"
    echo "  up              启动服务（默认 Full 模式，加 --lite 切换 Lite）"
    echo "  down            停止服务"
    echo "  restart         重启服务"
    echo "  ps              查看容器状态 + API 健康检查"
    echo "  logs [service]  查看日志（默认最近 30 行，指定 service 时 tail -f）"
    echo "  clean          停止并删除所有数据卷（⚠ 不可恢复）"
    echo ""
    echo "模式:"
    echo "  (默认)    Full — 6 容器, 独立队列, 4GB+ 推荐"
    echo "  --lite    Lite — 3 容器, 合并队列, 2C2G 推荐"
    echo ""
    echo "示例:"
    echo "  $0 build                    # 构建镜像"
    echo "  $0 up --lite               # 启动 Lite 模式"
    echo "  $0 ps --lite               # 查看 Lite 状态"
    echo "  $0 logs api                # 跟踪 API 日志"
    echo "  $0 restart                 # 重启 Full 模式"
    echo "  $0 down --lite             # 停止 Lite 模式"
    echo "  $0 clean --lite            # 清理 Lite 所有数据"
    echo ""
}

# ── Main ────────────────────────────────────────────────────────────
_check_docker

case "${1:-}" in
    build)      shift; _build "$@" ;;
    up|start)   shift; _up "$@" ;;
    down|stop)  shift; _down "$@" ;;
    restart)    shift; _restart "$@" ;;
    ps|status)  shift; _ps "$@" ;;
    logs)       shift; _logs "$@" ;;
    clean)      shift; _clean "$@" ;;
    *)          _usage ;;
esac
