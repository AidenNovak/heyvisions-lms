#!/usr/bin/env bash
# 在 vultr-sg 上重建 Yet to Dawn LMS 的 Web 产物。
#
# 为什么要单独一个脚本：`server-setup.sh` 只在 `.next/BUILD_ID` 不存在时才构建
# （一次性安装脚本），改代码后要重建得自己来。这里把它做成可反复执行的：
#   备份 → 清理 → 构建 → 按 setup 脚本同样的方式补齐 standalone 产物 → 重启 → 验收
#
# 资源：这台机器同时是 PROD（8 vCPU / 31 GiB），构建用 nice + 内存上限，
# 并先确认负载不高，避免把线上容器挤掉。
set -euo pipefail

ROOT=/srv/heyvisions-lms
WEB="$ROOT/apps/web"
BACKUP_ROOT=/srv/heyvisions-build-backup
STAMP="$(date +%Y%m%d-%H%M%S)"

cd "$WEB"

echo "══ 构建前检查"
uptime
FREE_GB=$(free -g | awk '/^Mem:/{print $7}')
echo "可用内存：${FREE_GB} GiB"
if [ "$FREE_GB" -lt 6 ]; then
  echo "可用内存不足 6 GiB，放弃构建以免影响线上容器" >&2
  exit 1
fi

if [ -d .next ]; then
  mkdir -p "$BACKUP_ROOT"
  echo "══ 备份现有产物 → $BACKUP_ROOT/.next-$STAMP"
  # 硬链接式备份：产物有几个 GB，cp -al 秒级完成且不占额外磁盘
  cp -al .next "$BACKUP_ROOT/.next-$STAMP"
  echo "备份完成（硬链接，回滚时先删 .next 再 mv 回去）"
fi

echo "══ 清理旧产物"
rm -rf .next

echo "══ 构建（nice 10，堆上限 6 GiB）"
# bun 在 /root/.bun/bin（见 server-up.sh 的 HV_EXTRA_PATH），不在系统 PATH 里。
PATH="/opt/hv-node/bin:/root/.bun/bin:$PATH" \
NODE_OPTIONS="--max-old-space-size=6144" \
NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL="http://127.0.0.1:1349" \
NEXT_PUBLIC_LEARNHOUSE_API_URL="http://127.0.0.1:1349/api/v1/" \
NEXT_PUBLIC_LEARNHOUSE_DOMAIN="127.0.0.1:3011" \
  nice -n 10 bun run next build 2>&1 | tail -30

if [ ! -f .next/standalone/server.js ]; then
  echo "构建未产出 .next/standalone/server.js，停止" >&2
  exit 1
fi

echo "══ 补齐 standalone 产物（与 server-setup.sh 一致）"
# 先删干净：`cp -r public .next/standalone/public` 在目标已存在时会套成
# public/public，跑第二遍就会出现一份不会被服务的陈旧副本。
rm -rf .next/standalone/public
cp -r public .next/standalone/public
rm -rf .next/standalone/.next/static
mkdir -p .next/standalone/.next
cp -r .next/static .next/standalone/.next/static
cp server-wrapper.js .next/standalone/server-wrapper.js

echo "══ 产物校验"
test -d .next/standalone/.next/static && echo "  ✓ .next/static"
test -d .next/standalone/public && echo "  ✓ public"
test -f .next/standalone/server-wrapper.js && echo "  ✓ server-wrapper.js"
test -f .next/BUILD_ID && echo "  ✓ BUILD_ID: $(cat .next/BUILD_ID)"

echo "══ 完成，重启服务"
cd "$ROOT"
scripts/heyvisions/server-up.sh stop 2>&1 | tail -4
sleep 2
scripts/heyvisions/server-up.sh 2>&1 | tail -6
