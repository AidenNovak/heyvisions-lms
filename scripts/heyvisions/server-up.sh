#!/usr/bin/env bash
# HeyVisions LMS — 在服务器上启动开发栈。
#
# 为什么在服务器上跑：本机（Mac）资源紧张，编译与长驻进程都放这台机器，
# 本机只留编辑。数据服务是 Docker（见 docker-compose.yml），应用进程跑在
# 宿主上，便于直接看日志、改代码后重启单个进程。
#
# 用法：
#   scripts/heyvisions/server-up.sh            # 起全部
#   scripts/heyvisions/server-up.sh api web    # 只起指定的
#   scripts/heyvisions/server-up.sh status     # 看状态
#   scripts/heyvisions/server-up.sh stop       # 停全部
#
# 环境变量覆盖（都有默认值，见下方 env 块）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="${HV_RUN_DIR:-/srv/heyvisions-run}"
LOG_DIR="$RUN_DIR/logs"
SECRETS="${HV_SECRETS:-/srv/heyvisions-secrets/lms.env}"

WEB_PORT="${HV_WEB_PORT:-3011}"
API_PORT="${HV_API_PORT:-1349}"
UNITS_PORT="${HV_UNITS_PORT:-8022}"
CONTENT_DIR="${HV_CONTENT_DIR:-/srv/heyvisions-content}"

# 绑定地址。
# - API 与单元静态服务绑回环即可，只经 SSH 隧道访问。
# - Web 必须绑到含 ::1 的地址：Next.js standalone 的 middleware 对绝对 URL 的
#   rewrite 会走一次真实 HTTP 请求，目标主机是 localhost；这台机器的 /etc/hosts
#   让 localhost 先解析到 ::1，只绑 127.0.0.1 会让该跳失败并返回 500。
#   绑 0.0.0.0 时该自转发走通（同一 host 被视作内部 rewrite）。
#   端口不对公网开放由 ufw 默认拒绝兜底，见 docs/heyvisions/LOCAL-SETUP.md。
BIND="${HV_BIND:-127.0.0.1}"
WEB_BIND="${HV_WEB_BIND:-0.0.0.0}"

mkdir -p "$RUN_DIR" "$LOG_DIR"

# 这台工具机上 bun 与 Node 22 装在非默认前缀（详见 docs/heyvisions/LOCAL-SETUP.md）。
# 非交互 ssh 不会带上这些 PATH，所以在这里显式补。
export PATH="${HV_EXTRA_PATH:-/opt/hv-node/bin:/root/.bun/bin}:$PATH"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }
}

# 启动一个后台进程并记录 pid。已在跑就不重复起。
spawn() {
  local name="$1"; shift
  local pidfile="$RUN_DIR/$name.pid"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] 已在运行 (pid $(cat "$pidfile"))"
    return 0
  fi
  ( "$@" ) >"$LOG_DIR/$name.log" 2>&1 &
  echo $! > "$pidfile"
  echo "[$name] 已启动 (pid $!) → $LOG_DIR/$name.log"
}

wait_http() {
  local name="$1" url="$2" tries="${3:-60}"
  for _ in $(seq "$tries"); do
    if curl -fsS -o /dev/null "$url" 2>/dev/null; then
      echo "[$name] 就绪：$url"
      return 0
    fi
    sleep 2
  done
  echo "[$name] 未在预期时间内就绪，看 $LOG_DIR/$name.log" >&2
  return 1
}

start_units() {
  need python3
  # --root 指向 course-content（其下是 units/），与 markdown_url 的 /units/ 前缀对应。
  spawn units python3 "$ROOT/scripts/heyvisions/serve-units.py" \
    --root "$CONTENT_DIR" --host "$BIND" --port "$UNITS_PORT"
}

start_api() {
  need curl
  [ -f "$SECRETS" ] || { echo "缺少凭据文件：$SECRETS" >&2; exit 1; }
  local venv="$ROOT/apps/api/.venv/bin"
  [ -x "$venv/uvicorn" ] || { echo "API 虚拟环境不存在，先跑 $ROOT/scripts/heyvisions/server-setup.sh" >&2; exit 1; }

  # config.py 在解析配置时读环境变量，所以这些必须 export 而不是写进 yaml。
  set -a
  # shellcheck disable=SC1090
  . "$SECRETS"
  set +a

  export LEARNHOUSE_SQL_CONNECTION_STRING="postgresql+asyncpg://learnhouse:learnhouse@127.0.0.1:15432/learnhouse"
  export LEARNHOUSE_REDIS_CONNECTION_STRING="redis://127.0.0.1:16379/0"
  export LEARNHOUSE_DEVELOPMENT_MODE=true
  # 单租户：开发栈只服务一个组织，多租户要靠子域，本地没有 DNS。
  export LEARNHOUSE_TENANCY=single
  export LEARNHOUSE_DOMAIN="127.0.0.1:$WEB_PORT"
  export LEARNHOUSE_FRONTEND_DOMAIN="127.0.0.1:$WEB_PORT"
  # 注意：.local 是保留域，会被 email-validator 拒（引擎启动即失败）。
  export LEARNHOUSE_INITIAL_ADMIN_EMAIL="${LEARNHOUSE_INITIAL_ADMIN_EMAIL:-admin@heyvisions.com}"
  # Web 与 API 端口不同，属跨源请求，必须显式放行。
  export LEARNHOUSE_ALLOWED_ORIGINS="http://127.0.0.1:$WEB_PORT,http://localhost:$WEB_PORT"

  # uvicorn 用 "app:app" 这种导入串解析模块，工作目录必须是 apps/api。
  spawn api env -C "$ROOT/apps/api" "$venv/uvicorn" app:app --host "$BIND" --port "$API_PORT" --log-level info
}

start_web() {
  need bun
  local web="$ROOT/apps/web"
  [ -d "$web/node_modules" ] || { echo "Web 依赖未装，先跑 $ROOT/scripts/heyvisions/server-setup.sh" >&2; exit 1; }
  [ -f "$web/.next/BUILD_ID" ] || { echo "Web 未构建，先跑 $ROOT/scripts/heyvisions/server-setup.sh" >&2; exit 1; }
  # 生产构建下客户端配置只认 runtime-config.js；这里在启动时生成，
  # 与本机部署的形状一致（改配置无需重新构建）。
  cat > "$web/public/runtime-config.js" <<EOF
window.__RUNTIME_CONFIG__ = {"NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL":"http://$BIND:$API_PORT","NEXT_PUBLIC_LEARNHOUSE_API_URL":"http://$BIND:$API_PORT/api/v1/","NEXT_PUBLIC_LEARNHOUSE_DOMAIN":"$BIND:$WEB_PORT","NEXT_PUBLIC_LEARNHOUSE_HTTPS":"false","NEXT_PUBLIC_DEFAULT_LANGUAGE":"${HV_DEFAULT_LANGUAGE:-zh}"};
EOF

  # 生产同款入口：standalone server + server-wrapper.js（后者把 NEXT_PUBLIC_*
  # 写成 public/runtime-config.js，客户端配置的唯一来源）。
  # 不用 `next start`：在 output:standalone 下它额外套一层到 localhost 的代理。
  spawn web env -C "$web/.next/standalone" PATH="/opt/hv-node/bin:$PATH" \
    NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL="http://$BIND:$API_PORT" \
    NEXT_PUBLIC_LEARNHOUSE_API_URL="http://$BIND:$API_PORT/api/v1/" \
    NEXT_PUBLIC_LEARNHOUSE_DOMAIN="$BIND:$WEB_PORT" \
    NEXT_PUBLIC_LEARNHOUSE_HTTPS="false" \
    PORT="$WEB_PORT" HOSTNAME="$WEB_BIND" \
    node server-wrapper.js
}

stop_all() {
  for pidfile in "$RUN_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    local name pid
    name="$(basename "$pidfile" .pid)"
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      # next start 会 fork；杀掉整个进程组，避免留下孤儿监听端口。
      kill -TERM -"$(ps -o pgid= -p "$pid" | tr -d ' ')" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
      echo "[$name] 已停止 (pid $pid)"
    fi
    rm -f "$pidfile"
  done
}

status() {
  printf '%-8s %-10s %s\n' 服务 PID 状态
  for pidfile in "$RUN_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    local name pid state
    name="$(basename "$pidfile" .pid)"
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then state="运行中"; else state="已停止"; fi
    printf '%-8s %-10s %s\n' "$name" "$pid" "$state"
  done
  echo
  echo "端口：units=$UNITS_PORT api=$API_PORT web=$WEB_PORT"
  curl -fsS -o /dev/null "http://$BIND:$API_PORT/api/v1/health" 2>/dev/null && echo "API 健康检查：通过" || echo "API 健康检查：未通过"
}

case "${1:-all}" in
  status) status ;;
  stop)   stop_all ;;
  all)
    start_units
    start_api
    wait_http api "http://$BIND:$API_PORT/api/v1/health" 90
    start_web
    wait_http web "http://$BIND:$WEB_PORT/" 90 || true
    echo
    status
    ;;
  *)
    for target in "$@"; do
      case "$target" in
        units|api|web) "start_$target" ;;
        *) echo "未知目标：$target（可选 units / api / web）" >&2; exit 1 ;;
      esac
    done
    ;;
esac
