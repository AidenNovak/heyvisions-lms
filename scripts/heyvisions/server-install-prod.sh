#!/usr/bin/env bash
# Yet to Dawn LMS — 把这台机器上的代码变成对外服务（幂等，可重复执行）。
#
#   scripts/heyvisions/server-install-prod.sh                 # 用现有配置安装/更新
#   scripts/heyvisions/server-install-prod.sh --host learn.yettodawn.com
#
# 做四件事：
#   1. 生成 Web 的运行时配置（客户端 runtime-config.js + 服务端 runtime-config.json）
#   2. 安装三个 systemd 服务（units / api / web）并启动
#   3. 安装宿主 nginx vhost（一个主机名按路径分流到三个进程）
#   4. 自检：三个进程健康 + 通过公网主机名访问
#
# 与 server-up.sh（开发栈）的区别：那个用 pid 文件跑前台进程、绑定回环、配置写死
# 127.0.0.1，只适合经 SSH 隧道调试；这里是开机自启、崩溃重启、同源 HTTPS 的生产形态。
# 两者**不能同时跑**（端口相同），安装前会停掉开发栈。
#
# 前提：
#   - 已在 server-setup.sh 里备好依赖与 Web 构建（.next/standalone 存在）
#   - /srv/heyvisions-secrets/lms-prod.env 存在（见 docs/heyvisions/PRODUCTION.md）
#   - 该主机名的 DNS 已指向本机，且证书已签发（脚本会提示具体命令）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${HV_ENV_FILE:-/srv/heyvisions-secrets/lms-prod.env}"
RUN_DIR="${HV_RUN_DIR:-/srv/heyvisions-run}"
WEB_DIR="$ROOT/apps/web"
STANDALONE="$WEB_DIR/.next/standalone"

usage() {
  cat >&2 <<'EOF'
用法：server-install-prod.sh [--host <主机名>] [--cert-dir <letsencrypt目录名>]

  --host       对外主机名，默认取 $HV_HOST 或 lms-prod.env 里的 LEARNHOUSE_DOMAIN
  --cert-dir   /etc/letsencrypt/live/ 下的目录名，默认与 --host 相同
EOF
  exit 2
}

HOST="${HV_HOST:-}"
CERT_DIR=""
while (($#)); do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --cert-dir) CERT_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[ -f "$ENV_FILE" ] || { echo "缺少运行时配置：$ENV_FILE" >&2; exit 1; }
# shellcheck disable=SC1090
[ -z "$HOST" ] && HOST="$(grep -E '^LEARNHOUSE_DOMAIN=' "$ENV_FILE" | tail -1 | cut -d= -f2-)"
[ -z "$HOST" ] && { echo "无法确定主机名：传 --host 或在 $ENV_FILE 里设 LEARNHOUSE_DOMAIN" >&2; exit 1; }
CERT_DIR="${CERT_DIR:-$HOST}"
CERT_FULLCHAIN="/etc/letsencrypt/live/$CERT_DIR/fullchain.pem"
CERT_KEY="/etc/letsencrypt/live/$CERT_DIR/privkey.pem"

log() { printf '\n=== %s ===\n' "$*"; }

[ -f "$STANDALONE/server.js" ] || {
  echo "Web 未构建或 standalone 产物缺失，先跑：$ROOT/scripts/heyvisions/server-setup.sh" >&2
  exit 1
}
[ -f "$CERT_FULLCHAIN" ] || {
  echo "找不到证书：$CERT_FULLCHAIN" >&2
  echo "签发（DNS-01，本机已有 /root/.secrets/certbot/cloudflare.ini）：" >&2
  echo "  certbot certonly --dns-cloudflare --dns-cloudflare-credentials /root/.secrets/certbot/cloudflare.ini \\" >&2
  echo "    -d $HOST --non-interactive --agree-tos -m <邮箱>" >&2
  exit 1
}

mkdir -p "$RUN_DIR/logs"

log "1/5 停开发栈（端口与生产服务相同）"
if [ -x "$ROOT/scripts/heyvisions/server-up.sh" ]; then
  "$ROOT/scripts/heyvisions/server-up.sh" stop || true
fi

log "2/5 生成 Web 运行时配置（$HOST）"
# 客户端与服务端各一份：浏览器读 public/runtime-config.js，服务端组件读
# 同目录的 runtime-config.json（config.ts 的 loadRuntimeConfig 两条路径都查）。
# 这两个文件必须在构建产物里就地生成 —— runtime 值不进构建，换配置不用重编译。
#
# LEARNHOUSE_SERVER_BACKEND_URL 只写进服务端的 runtime-config.json，不进 public：
# 服务端组件自己调 API 时走回环，不必绕公网。它必须在这里给，因为 Next 会把
# NEXT_PUBLIC_* 内联进构建产物，改域名后构建期那份就过期了。
API_URL="https://$HOST/api/v1/"
BACKEND_URL="https://$HOST"
python3 - "$STANDALONE" "$API_URL" "$BACKEND_URL" "$HOST" <<'PY'
import json, sys, pathlib
standalone, api_url, backend_url, host = sys.argv[1:5]
cfg = {
    "NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL": backend_url,
    "NEXT_PUBLIC_LEARNHOUSE_API_URL": api_url,
    "NEXT_PUBLIC_LEARNHOUSE_DOMAIN": host,
    "NEXT_PUBLIC_LEARNHOUSE_HTTPS": "true",
    "NEXT_PUBLIC_DEFAULT_LANGUAGE": "zh",
    "NEXT_PUBLIC_BRAND_NAME": "Yet to Dawn",
    "NEXT_PUBLIC_BRAND_SITE_URL": "https://yettodawn.com",
}
base = pathlib.Path(standalone)
server_cfg = dict(cfg, LEARNHOUSE_SERVER_BACKEND_URL="http://127.0.0.1:1349")
(base / "runtime-config.json").write_text(json.dumps(server_cfg, indent=2) + "\n", encoding="utf-8")
pub = base / "public"
pub.mkdir(exist_ok=True)
(pub / "runtime-config.js").write_text(
    "window.__RUNTIME_CONFIG__ = " + json.dumps(cfg) + ";\n", encoding="utf-8"
)
print("已写入 runtime-config.json（含服务端专用键）与 public/runtime-config.js")
PY

log "3/5 安装 systemd 服务"

# Web 侧的服务端密钥文件（Google OAuth 凭据、发信 key）。单元用
# `EnvironmentFile=-` 引用它，缺失时按「未配置」处理 —— 登录页据此不摆出
# 对应入口。这里只在不存在时建一个空的骨架；已存在则原样保留，绝不覆盖密钥。
WEB_ENV_FILE="${HV_WEB_ENV_FILE:-/srv/heyvisions-secrets/lms-web.env}"
if [ ! -f "$WEB_ENV_FILE" ]; then
  install -m 600 /dev/null "$WEB_ENV_FILE"
  cat >> "$WEB_ENV_FILE" <<'EOF'
# Yet to Dawn LMS —— Web 侧服务端密钥。权限 600；不要入库、不要出现在输出里。
#
# 按需追加；改完执行 systemctl restart hv-lms-web
#   LEARNHOUSE_GOOGLE_CLIENT_ID=...      # 与 API 侧的 aud 校验用同一个值
#   LEARNHOUSE_GOOGLE_CLIENT_SECRET=...
#   RESEND_API_KEY=...                   # 事务性发信（魔法链接/找回密码/邮箱验证）
#   RESEND_FROM_EMAIL=...
EOF
  log "已创建 $WEB_ENV_FILE（暂为空；未配置时登录页不显示对应入口）"
fi

install -m 644 "$ROOT/scripts/heyvisions/systemd/hv-lms-units.service" /etc/systemd/system/
install -m 644 "$ROOT/scripts/heyvisions/systemd/hv-lms-api.service" /etc/systemd/system/
install -m 644 "$ROOT/scripts/heyvisions/systemd/hv-lms-web.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now hv-lms-units.service hv-lms-api.service hv-lms-web.service
for svc in hv-lms-units hv-lms-api hv-lms-web; do
  systemctl restart "$svc.service"
done

log "4/5 安装 nginx vhost（$HOST）"
# Web 进程绑在 0.0.0.0:3011（见 hv-lms-web.service 的说明），端口靠 ufw 挡住。
# 显式加一条 deny：ufw 的默认策略将来被改动时，这层不会跟着失守。
if ! ufw status | grep -qE '^3011/tcp +DENY'; then
  ufw deny 3011/tcp comment 'hv-lms web (loopback via nginx only)' >/dev/null
  echo "已加 ufw 规则：deny 3011/tcp"
fi
sed -e "s|__HOSTNAME__|$HOST|g" \
    -e "s|__CERT_FULLCHAIN__|$CERT_FULLCHAIN|g" \
    -e "s|__CERT_KEY__|$CERT_KEY|g" \
    "$ROOT/scripts/heyvisions/nginx/yettodawn-lms.conf.template" \
    > "/etc/nginx/sites-available/$HOST"
ln -sfn "/etc/nginx/sites-available/$HOST" "/etc/nginx/sites-enabled/$HOST"
nginx -t
systemctl reload nginx

log "5/5 自检"
fail=0
# API 就绪要几十秒（建连、迁移、后台消费者），先等到健康检查通过再判，
# 否则「刚重启」会被误判成失败。
for _ in $(seq 60); do
  curl -fsS -o /dev/null "http://127.0.0.1:1349/api/v1/health" 2>/dev/null && break
  sleep 2
done
for u in "http://127.0.0.1:1349/api/v1/health" "http://127.0.0.1:8022/units/judge-task-01.md" "http://127.0.0.1:3011/"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$u" || echo 000)
  printf '  %-46s %s\n' "$u" "$code"
  [ "$code" = "200" ] || fail=1
done
for p in / /login /api/v1/health "/units/judge-task-01.md"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "https://$HOST$p" || echo 000)
  printf '  %-46s %s\n' "https://$HOST$p" "$code"
  [ "$code" = "200" ] || fail=1
done

echo
systemctl --no-pager --lines=0 status hv-lms-units hv-lms-api hv-lms-web | grep -E '^(●|   Active|     Loaded)'
echo
if [ "$fail" = "0" ]; then
  echo "完成：https://$HOST/"
else
  echo "有检查未通过，看 $RUN_DIR/logs/ 与 journalctl -u hv-lms-web" >&2
  exit 1
fi
