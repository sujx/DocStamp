#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────
# 鹊随金印 — Docker 镜像构建 & 发布到阿里云 ACR
#
# 使用前：
#   1. 在 ACR 控制台设置固定密码：容器镜像服务 → 访问凭证 → 设置固定密码
#   2. 填入下面的 ACR_PASSWORD
#   3. chmod +x publish.sh
#
# 用法：
#   ./publish.sh          # 构建 + 推送 latest
#   ./publish.sh v3.6     # 构建 + 推送指定版本 + latest
# ───────────────────────────────────────────────────────────────────
set -euo pipefail

# ── 配置（修改这里）─────────────────────────────────────────────────
ACR_REGISTRY="registry.cn-wulanchabu.aliyuncs.com"
ACR_NAMESPACE="grepsu"
ACR_USERNAME="sujx@live.cn"
# 密码从 .env 读取（.env 在 .gitignore 中，不会提交到代码库）
if [[ -z "${ACR_PASSWORD:-}" ]] && [[ -f "$PROJECT_DIR/.env" ]]; then
    ACR_PASSWORD=$(grep '^ACR_PASSWORD=' "$PROJECT_DIR/.env" 2>/dev/null | cut -d= -f2-)
fi
if [[ -z "${ACR_PASSWORD:-}" ]]; then
    err "请设置 ACR_PASSWORD 环境变量或在 .env 中添加 ACR_PASSWORD=xxx"
fi

IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/docstamp"
VERSION="${1:-v3.5}"
# ───────────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
log()  { echo -e "${GREEN}[publish]${NC} $*"; }
err()  { echo -e "${RED}[publish]${NC} $*"; exit 1; }

# Check password
if [[ -z "$ACR_PASSWORD" ]]; then
    err "请先在脚本中填入 ACR_PASSWORD（ACR 控制台 → 访问凭证 → 固定密码）"
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# ── Login ──────────────────────────────────────────────────────────
log "登录 ACR..."
echo "$ACR_PASSWORD" | docker login --username "$ACR_USERNAME" --password-stdin "$ACR_REGISTRY"

# ── Build ──────────────────────────────────────────────────────────
log "构建镜像 ${IMAGE}:${VERSION} ..."
docker build -t "${IMAGE}:${VERSION}" .

# ── Tag latest ─────────────────────────────────────────────────────
log "标记 latest..."
docker tag "${IMAGE}:${VERSION}" "${IMAGE}:latest"

# ── Push ───────────────────────────────────────────────────────────
log "推送 ${IMAGE}:${VERSION} ..."
docker push "${IMAGE}:${VERSION}"

log "推送 ${IMAGE}:latest ..."
docker push "${IMAGE}:latest"

# ── Done ───────────────────────────────────────────────────────────
log "══════ 发布完成 ══════"
log "镜像: ${IMAGE}:${VERSION}"
log "镜像: ${IMAGE}:latest"
echo ""
log "ECS 上部署:"
echo "  scp docker-compose.prod.yml .env root@你的ECS:/opt/docstamp/"
echo "  ssh root@你的ECS 'cd /opt/docstamp && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d'"
