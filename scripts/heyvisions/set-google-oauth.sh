#!/usr/bin/env bash
# 写入 Google OAuth 客户端凭据并重启服务。
#
# 为什么做成脚本：client secret 不该经过聊天记录、日志或 Git。这里用静默读入，
# 只在最后打印掩码后的 client id 供核对（client id 本身是公开值，secret 不是）。
#
# 两处都要 client id，是上游的设计：
#   - Web 侧：拿它拼授权地址、换 token（还要 secret）
#   - API 侧：校验 Google 返回的 token 的 aud，确认是发给我们的
# 见 apps/api/src/services/auth/utils.py 的 get_expected_google_client_id。
#
# 用法（在 vultr-sg 上）：./scripts/heyvisions/set-google-oauth.sh
set -euo pipefail

WEB_ENV="${HV_WEB_ENV_FILE:-/srv/heyvisions-secrets/lms-web.env}"
API_ENV="${HV_API_ENV_FILE:-/srv/heyvisions-secrets/lms-prod.env}"

mask() {
  # 只显示前 6 位与后 4 位，中间打码：便于核对是不是同一个客户端，又不泄露完整值
  local v="$1"
  if [ "${#v}" -le 12 ]; then printf '****'; else printf '%s...%s' "${v:0:6}" "${v: -4}"; fi
}

upsert() {
  # 幂等地写一个 KEY=VALUE：先删掉同名旧行，再追加。保留文件里其余注释与键。
  local file="$1" key="$2" value="$3" tmp
  touch "$file"
  chmod 600 "$file"
  tmp="$(mktemp)"
  grep -v "^${key}=" "$file" > "$tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

printf 'Google OAuth 客户端凭据录入\n\n'
printf '客户端 ID：'
read -r CLIENT_ID
if [ -z "$CLIENT_ID" ]; then echo '客户端 ID 不能为空' >&2; exit 1; fi

printf '客户端密钥（输入不回显）：'
read -r -s CLIENT_SECRET
printf '\n'
if [ -z "$CLIENT_SECRET" ]; then echo '客户端密钥不能为空' >&2; exit 1; fi

# 形态粗校验：Google 的 client id 以 .apps.googleusercontent.com 结尾，secret 以 GOCSPX- 开头。
# 只做提醒，不阻止 —— 格式变了不该把部署卡死。
case "$CLIENT_ID" in
  *.apps.googleusercontent.com) ;;
  *) echo "提示：客户端 ID 通常以 .apps.googleusercontent.com 结尾，请确认没粘错。" >&2 ;;
esac
case "$CLIENT_SECRET" in
  GOCSPX-*) ;;
  *) echo "提示：客户端密钥通常以 GOCSPX- 开头，请确认没粘错。" >&2 ;;
esac

upsert "$WEB_ENV" LEARNHOUSE_GOOGLE_CLIENT_ID "$CLIENT_ID"
upsert "$WEB_ENV" LEARNHOUSE_GOOGLE_CLIENT_SECRET "$CLIENT_SECRET"
upsert "$API_ENV" LEARNHOUSE_GOOGLE_CLIENT_ID "$CLIENT_ID"

echo
echo "已写入："
printf '  %s  LEARNHOUSE_GOOGLE_CLIENT_ID=%s\n' "$WEB_ENV" "$(mask "$CLIENT_ID")"
printf '  %s  LEARNHOUSE_GOOGLE_CLIENT_SECRET=%s\n' "$WEB_ENV" "$(mask "$CLIENT_SECRET")"
printf '  %s  LEARNHOUSE_GOOGLE_CLIENT_ID=%s\n' "$API_ENV" "$(mask "$CLIENT_ID")"
stat -c '  权限 %a %n' "$WEB_ENV" "$API_ENV"

echo
echo '重启服务…'
systemctl restart hv-lms-web hv-lms-api
sleep 6
for s in hv-lms-web hv-lms-api; do printf '  %-12s %s\n' "$s" "$(systemctl is-active $s)"; done

echo
echo '进程是否真的拿到了变量（只看键名，不打印值）：'
for s in hv-lms-web hv-lms-api; do
  pid="$(systemctl show -p MainPID --value "$s")"
  keys="$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep -c '^LEARNHOUSE_GOOGLE_CLIENT' || true)"
  printf '  %-12s LEARNHOUSE_GOOGLE_CLIENT* 共 %s 个\n' "$s" "$keys"
done

echo
for u in http://127.0.0.1:3011/ https://learn.yettodawn.com/login https://learn.yettodawn.com/api/v1/health; do
  printf '  %-46s ' "$u"
  curl -s -o /dev/null -w '%{http_code}\n' --max-time 25 "$u"
done
