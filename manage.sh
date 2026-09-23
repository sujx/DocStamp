#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# docStamp 项目管理脚本
#
# Usage:
#   ./manage.sh start       启动后端 + 前端（开发模式）
#   ./manage.sh stop        停止所有服务
#   ./manage.sh restart     重启所有服务
#   ./manage.sh status      查看运行状态
#   ./manage.sh backend     仅启动后端
#   ./manage.sh frontend    仅启动前端
#   ./manage.sh test        运行后端测试
#   ./manage.sh test-cov    运行测试 + 覆盖率
#   ./manage.sh docker-up   启动 Docker 部署（单容器）
#   ./manage.sh docker-down 停止 Docker 部署
#   ./manage.sh clean-output 清理 output 目录
# ───────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_DIR="$PROJECT_DIR/.pids"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

BACKEND_PORT=5000
FRONTEND_PORT=8080

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[docStamp]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[docStamp]${NC} $*"; }
log_error() { echo -e "${RED}[docStamp]${NC} $*"; }

_mkdir_pid() { mkdir -p "$PID_DIR"; }

_is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

_stop_by_pid() {
    local pid_file="$1"
    local name="$2"
    if ! _is_running "$pid_file"; then
        rm -f "$pid_file"
        log_warn "$name 未在运行"
        return 0
    fi
    local pid
    pid=$(cat "$pid_file")
    log_info "正在停止 $name (PID: $pid)..."
    kill "$pid" 2>/dev/null || true
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 5 ]]; do
        sleep 0.5
        waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        log_warn "$name 未响应，强制终止..."
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
    log_info "$name 已停止"
}

_force_stop_port() {
    local port="$1"
    local pids
    pids=$(fuser "$port/tcp" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        log_warn "端口 $port 仍有进程残留，强制清理: $pids"
        fuser -k "$port/tcp" 2>/dev/null || true
        sleep 1
    fi
}

_start_backend() {
    if [[ -f "$BACKEND_PID" ]]; then
        local old_pid
        old_pid=$(cat "$BACKEND_PID" 2>/dev/null || true)
        if [[ -n "$old_pid" ]] && ! kill -0 "$old_pid" 2>/dev/null; then
            rm -f "$BACKEND_PID"
        fi
    fi
    if _is_running "$BACKEND_PID"; then
        log_warn "后端已在运行 (PID: $(cat "$BACKEND_PID"))"
        return 0
    fi
    _force_stop_port "$BACKEND_PORT"
    log_info "启动后端 (Flask, 端口 $BACKEND_PORT)..."
    cd "$BACKEND_DIR"
    python3 app.py > "$PID_DIR/backend.log" 2>&1 &

    local pid=$!
    echo "$pid" > "$BACKEND_PID"
    cd "$PROJECT_DIR"

    local waited=0
    while [[ $waited -lt 15 ]]; do
        if curl -s -o /dev/null "http://localhost:$BACKEND_PORT/api/v1/health" 2>/dev/null; then
            log_info "后端就绪 → http://localhost:$BACKEND_PORT"
            return 0
        fi
        sleep 0.5
        waited=$((waited + 1))
    done
    log_warn "后端启动超时，请查看日志: $PID_DIR/backend.log"
}

_start_frontend() {
    if [[ -f "$FRONTEND_PID" ]]; then
        local old_pid
        old_pid=$(cat "$FRONTEND_PID" 2>/dev/null || true)
        if [[ -n "$old_pid" ]] && ! kill -0 "$old_pid" 2>/dev/null; then
            rm -f "$FRONTEND_PID"
        fi
    fi
    if _is_running "$FRONTEND_PID"; then
        log_warn "前端已在运行 (PID: $(cat "$FRONTEND_PID"))"
        return 0
    fi
    rm -rf "$FRONTEND_DIR/.nuxt"
    log_info "启动前端 (Nuxt, 端口 $FRONTEND_PORT)..."
    cd "$FRONTEND_DIR"
    npm run dev > "$PID_DIR/frontend.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$FRONTEND_PID"
    cd "$PROJECT_DIR"
    local waited=0
    while [[ $waited -lt 30 ]]; do
        if curl -s -o /dev/null "http://localhost:$FRONTEND_PORT" 2>/dev/null; then
            log_info "前端就绪 → http://localhost:$FRONTEND_PORT"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    log_warn "前端启动超时，请查看日志: $PID_DIR/frontend.log"
}

_stop_all() {
    _stop_by_pid "$FRONTEND_PID" "前端"
    _stop_by_pid "$BACKEND_PID" "后端"
    _force_stop_port "$BACKEND_PORT"
}

_show_status() {
    echo ""
    echo "  docStamp 服务状态"
    echo "  ─────────────────"
    if _is_running "$BACKEND_PID"; then
        echo -e "  后端  (Flask)      ${GREEN}● 运行中${NC}  PID: $(cat "$BACKEND_PID")  :$BACKEND_PORT"
    else
        echo -e "  后端  (Flask)      ○ 已停止"
    fi
    if _is_running "$FRONTEND_PID"; then
        echo -e "  前端  (Nuxt)     ${GREEN}● 运行中${NC}  PID: $(cat "$FRONTEND_PID")  :$FRONTEND_PORT"
    else
        echo -e "  前端  (Nuxt)     ○ 已停止"
    fi
    echo ""
}

_mkdir_pid

case "${1:-}" in
    start)
        log_info "══════ 启动 docStamp 服务 ══════"
        _start_backend
        _start_frontend
        log_info "══════ 全部启动完成 ══════"
        _show_status
        ;;
    stop)
        log_info "══════ 停止 docStamp 服务 ══════"
        _stop_all
        log_info "══════ 全部停止完成 ══════"
        ;;
    restart)
        log_info "══════ 重启 docStamp 服务 ══════"
        _stop_all
        sleep 1
        _start_backend
        _start_frontend
        log_info "══════ 重启完成 ══════"
        _show_status
        ;;
    status)
        _show_status
        ;;
    backend)
        _start_backend
        ;;
    frontend)
        _start_frontend
        ;;
    docker-up)
        log_info "══════ 启动 Docker 部署 ══════"
        cd "$PROJECT_DIR"
        docker compose up -d --build
        docker compose ps
        log_info "══════ Docker 部署已启动 ══════"
        ;;
    docker-down)
        log_info "停止 Docker 部署..."
        cd "$PROJECT_DIR"
        docker compose down
        log_info "Docker 部署已停止"
        ;;
    test)
        log_info "运行后端测试..."
        cd "$BACKEND_DIR"
        python3 -m pytest tests/ -v
        cd "$PROJECT_DIR"
        ;;
    test-cov)
        log_info "运行后端测试（含覆盖率）..."
        cd "$BACKEND_DIR"
        python3 -m pytest tests/ --cov=./ --cov-report=term
        cd "$PROJECT_DIR"
        ;;
    clean-output)
        log_info "清理 output 目录..."
        rm -f "$BACKEND_DIR/output/"*
        log_info "清理完成"
        ;;
    *)
        echo ""
        echo "docStamp 项目管理脚本"
        echo ""
        echo "用法: $0 <command>"
        echo ""
        echo "开发命令:"
        echo "  start         启动后端 + 前端（开发模式）"
        echo "  stop          停止所有服务"
        echo "  restart       重启所有服务"
        echo "  status        查看运行状态"
        echo "  backend       仅启动后端"
        echo "  frontend      仅启动前端"
        echo "  test          运行后端 pytest 测试"
        echo "  test-cov      运行后端测试（含覆盖率）"
        echo "  clean-output  清理 output 目录文件"
        echo ""
        echo "Docker 部署:"
        echo "  docker-up     构建并启动 Docker 容器（单容器）"
        echo "  docker-down   停止 Docker 容器"
        echo ""
        ;;
esac
