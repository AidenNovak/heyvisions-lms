#!/usr/bin/env bash
# 从 JSON 文件读取 Google OAuth 凭据并写入服务配置（非交互）。
#
# 与 set-google-oauth.sh 的区别：那份是给人手工粘贴用的（静默读入），
# 这份是给自动化用的（从 600 权限的 JSON 读）。两者写入的位置完全一致：
#   - lms-web.env: CLIENT_ID + CLIENT_SECRET（Web 换 token 要 secret）
#   - lms-prod.env: CLIENT_ID（API 用它校验 token 的 aud）
#
# 只打印掩码后的 client id，**不打印 secret**。
#
# 用法（在 vultr-sg 上）：set-google-oauth-from-json.sh <json路径>
set -euo pipefail

JSON="${1:-/srv/heyvisions-secrets/google-oauth-client.json}"
WEB_ENV="${HV_WEB_ENV_FILE:-/srv/heyvisions-secrets/lms-web.env}"
API_ENV="${HV_API_ENV_FILE:-/srv/heyvisions-secrets/lms-prod.env}"

[ -f "$JSON" ] || { echo "找不到 $JSON" >&2; exit 1; }

read -r CLIENT_ID CLIENT_SECRET < <(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
cid = (d.get("client_id") or "").strip()
sec = (d.get("client_secret") or "").strip()
if not cid or not sec:
    raise SystemExit("凭据文件缺少 client_id 或 client_secret")
print(cid, sec)
PY
)

[ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ] || { echo "凭据为空" >&2; exit 1; }

mask() { local v="$1"; if [ "${#v}" -le 12 ]; then printf '****'; else printf '%s...%s' "${v:0:6}" "${v: -4}"; fi; }

upsert() {
  local file="$1" key="$2" value="$3" tmp
  touch "$file"; chmod 600 "$file"
  tmp="$(mktemp)"
  grep -v "^${key}=" "$file" > "$tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

upsert "$WEB_ENV" LEARNHOUSE_GOOGLE_CLIENT_ID "$CLIENT_ID"
upsert "$WEB_ENV" LEARNHOUSE_GOOGLE_CLIENT_SECRET "$CLIENT_SECRET"
upsert "$API_ENV" LEARNHOUSE_GOOGLE_CLIENT_ID "$CLIENT_ID"

echo "已写入："
printf '  %-44s CLIENT_ID=%s  CLIENT_SECRET=%s\n' "$WEB_ENV" "$(mask "$CLIENT_ID")" "$(mask "$CLIENT_SECRET")"
printf '  %-44s CLIENT_ID=%s\n' "$API_ENV" "$(mask "$CLIENT_ID")"
stat -c '  权限 %a %n' "$WEB_ENV" "$API_ENV"

echo
echo "重启服务…"
systemctl restart hv-lms-web hv-lms-api
sleep 7
for s in hv-lms-web hv-lms-api; do printf '  %-12s %s\n' "$s" "$(systemctl is-active $s)"; done

echo
echo "进程是否拿到变量（只看键的数量）："
for s in hv-lms-web hv-lms-api; do
  pid="$(systemctl show -p MainPID --value "$s")"
  n="$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep -c '^LEARNHOUSE_GOOGLE_CLIENT' || true)"
  printf '  %-12s LEARNHOUSE_GOOGLE_CLIENT* = %s 个\n' "$s" "$n"
done

echo
for u in http://127.0.0.1:3011/ https://learn.yettodawn.com/login https://learn.yettodawn.com/api/v1/health; do
  printf '  %-46s ' "$u"
  curl -s -o /dev/null -w '%{http_code}\n' --max-time 25 "$u"
done
