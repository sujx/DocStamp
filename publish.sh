#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# 鹊随金印 — Docker 镜像构建 & 发布到阿里云 ACR
#
# 密码走 .env（已在 .gitignore 中，不进仓库也不进镜像）：
#   ACR_PASSWORD=xxx        # ACR 控制台 → 访问凭证 → 设置固定密码
#
# 用法：
#   ./publish.sh            # 版本号取 SPEC.md 版本历史的首条，无需手改脚本
#   ./publish.sh v3.7.6     # 显式指定版本号
# ───────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[publish]${NC} $*"; }
warn() { echo -e "${YELLOW}[publish]${NC} $*" >&2; }
err()  { echo -e "${RED}[publish]${NC} $*" >&2; exit 1; }

# ── 配置（修改这里）─────────────────────────────────────────────────
ACR_REGISTRY="registry.cn-wulanchabu.aliyuncs.com"
ACR_NAMESPACE="grepsu"
ACR_USERNAME="sujx@live.cn"
IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/docstamp"
# ───────────────────────────────────────────────────────────────────

cd "$PROJECT_DIR"

# ── 前置检查 ────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || err "找不到 docker，请先安装 Docker Desktop"
docker info >/dev/null 2>&1 || err "Docker 守护进程未运行，请先启动 Docker Desktop"

# ── 密码：环境变量优先，其次 .env ───────────────────────────────────
# tr -d '\r' 兜住 Windows 上编辑过的 .env（CRLF 会让密码多一个不可见字符，
# 表现为 docker login 报认证失败）
if [[ -z "${ACR_PASSWORD:-}" ]] && [[ -f "$PROJECT_DIR/.env" ]]; then
    ACR_PASSWORD="$(grep -m1 '^ACR_PASSWORD=' "$PROJECT_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '\r' || true)"
fi
if [[ -z "${ACR_PASSWORD:-}" ]]; then
    err "未取到 ACR_PASSWORD：请设同名环境变量，或在 .env 里写 ACR_PASSWORD=xxx（ACR 控制台 → 访问凭证 → 固定密码）"
fi

# ── 版本号 ──────────────────────────────────────────────────────────
# 不写死默认值（曾经写死 v3.5，加了三轮功能后仍推 v3.5）。显式参数优先，
# 否则取 SPEC.md 版本历史的首条 —— 那本来就是每次发版都要更新的地方。
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    VERSION="$(grep -m1 -oE '^### v[0-9]+\.[0-9]+(\.[0-9]+)?' SPEC.md 2>/dev/null | sed 's/^### //' || true)"
    if [[ -z "$VERSION" ]]; then
        err "无法从 SPEC.md 解析当前版本号，请显式传入：./publish.sh v3.7.6"
    fi
    log "未指定版本号，取 SPEC.md 最新条目：${VERSION}"
fi

# ── 源码状态（便于把镜像回溯到提交）─────────────────────────────────
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo '未知')"
log "源码提交：${COMMIT}"
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    warn "工作树有未提交改动 —— 镜像里的代码不对应提交 ${COMMIT}"
fi

# ── Login ───────────────────────────────────────────────────────────
log "登录 ACR..."
echo "$ACR_PASSWORD" | docker login --username "$ACR_USERNAME" --password-stdin "$ACR_REGISTRY"

# ── Build ───────────────────────────────────────────────────────────
# --build-arg BUST_FRONTEND 只失效前端构建层（拿到新的 JS chunk hash），保留
# npm ci / apt / pip 缓存；否则只能 --no-cache 全量重建。
log "构建镜像 ${IMAGE}:${VERSION} ..."
docker build \
  --build-arg BUST_FRONTEND="$(date +%s)" \
  -t "${IMAGE}:${VERSION}" \
  -t "${IMAGE}:latest" .

# ── Push ────────────────────────────────────────────────────────────
log "推送 ${IMAGE}:${VERSION} ..."
docker push "${IMAGE}:${VERSION}"

log "推送 ${IMAGE}:latest ..."
docker push "${IMAGE}:latest"

# ── Done ────────────────────────────────────────────────────────────
log "══════ 发布完成 ══════"
log "镜像：${IMAGE}:${VERSION}  /  ${IMAGE}:latest（源码 ${COMMIT}）"
echo ""
log "ECS 上部署："
echo "  scp docker-compose.yml root@你的ECS:/opt/docstamp/"
echo "  ssh root@你的ECS 'cd /opt/docstamp && docker login --username ${ACR_USERNAME} ${ACR_REGISTRY} && docker compose pull && docker compose up -d --no-build'"
echo ""
echo "  说明：docker-compose.yml 的 api 服务已带 image: ${IMAGE}:latest，"
echo "        所以 ECS 只需 pull（--no-build 是防止它试图就地构建）；"
echo "        本地要继续从源码构建则用 ./manage.sh docker-up。"
echo "        只传 docker-compose.yml：服务器上那份 .env 是线上配置，别用本地的"
echo "        覆盖（compose 里的变量都带默认值，缺 .env 也能起）。"
echo "        若容器起不来并提示 data 目录不可写，按 docker-entrypoint.sh 打印的"
echo "        chown 指引处理，不要删卷（db_data 里是 tasks.db 唯一副本）。"
