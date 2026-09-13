#!/usr/bin/env bash
# HeyVisions LMS — 在服务器上一次性准备开发环境（幂等，可重复执行）。
#
#   scripts/heyvisions/server-setup.sh
#
# 做四件事：数据服务（Docker）→ API 虚拟环境 → Web 依赖 → Web 构建。
# 编译类步骤在这台机器上跑而不是本机，见 docs/heyvisions/LOCAL-SETUP.md。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UV="${UV:-$HOME/.local/bin/uv}"
PIP_INDEX="${HV_PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
BUN_REGISTRY="${HV_BUN_REGISTRY:-https://registry.npmmirror.com}"

log() { printf '\n=== %s ===\n' "$*"; }

log "数据服务（Postgres + pgvector / Redis）"
cd "$ROOT"
docker compose -f scripts/heyvisions/docker-compose.yml up -d
for _ in $(seq 30); do
  docker exec hv-lms-postgres pg_isready -U learnhouse >/dev/null 2>&1 && break
  sleep 2
done
# 课程 embedding 依赖 pgvector，pgvector 镜像自带但扩展要显式创建。
docker exec hv-lms-postgres psql -U learnhouse -d learnhouse \
  -c 'CREATE EXTENSION IF NOT EXISTS vector;' >/dev/null
echo "数据服务就绪：127.0.0.1:15432 / 127.0.0.1:16379"

log "API 虚拟环境（Python 3.14.7）"
cd "$ROOT/apps/api"
# pyproject 锁定 >=3.14.7,<3.14.8：3.14.7 里有安全修复，放宽会引入已知漏洞。
if [ ! -x .venv/bin/uvicorn ]; then
  "$UV" venv --seed --python 3.14.7
  "$UV" export --format requirements-txt --no-hashes --no-dev -o /tmp/lh-req.txt
  # --no-deps：锁文件已经钉死全部传递依赖，让 pip 再解析一遍既慢又容易撞版本。
  .venv/bin/pip install --no-deps -r /tmp/lh-req.txt -i "$PIP_INDEX"
else
  echo "已存在，跳过"
fi

log "Web 依赖与构建"
cd "$ROOT/apps/web"
if [ ! -d node_modules ]; then
  bun install --registry "$BUN_REGISTRY"
else
  echo "依赖已存在，跳过"
fi

if [ ! -f .next/BUILD_ID ]; then
  # 构建期只需要一个合法形状的 API 地址；运行时真实地址来自 runtime-config.js。
  # Next.js 要求 Node >= 20，系统 Node 是 18；用 /opt/hv-node。
  PATH="/opt/hv-node/bin:$PATH" \
  NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL="http://127.0.0.1:1349" \
  NEXT_PUBLIC_LEARNHOUSE_API_URL="http://127.0.0.1:1349/api/v1/" \
  NEXT_PUBLIC_LEARNHOUSE_DOMAIN="127.0.0.1:3011" \
    bun run next build
else
  echo "构建产物已存在，跳过（要重建就先 rm -rf .next）"
fi

# standalone 产物不自带 .next/static 与 public —— 生产镜像是靠 Dockerfile
# 里两步 COPY 补上的，这里等价补一遍。放在构建之后，保证与本次构建同源。
if [ -f .next/standalone/server.js ]; then
  cp -r public .next/standalone/public
  mkdir -p .next/standalone/.next
  cp -r .next/static .next/standalone/.next/static
  cp server-wrapper.js .next/standalone/server-wrapper.js
  echo "standalone 产物已补齐（public / .next/static / server-wrapper.js）"
else
  echo "找不到 .next/standalone/server.js，检查 output 配置" >&2
  exit 1
fi

log "完成"
echo "启动：$ROOT/scripts/heyvisions/server-up.sh"
