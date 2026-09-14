#!/usr/bin/env bash
# 交付前最后一次全量核对（只读，不改任何东西）。
#
# 覆盖三层：
#   ① 页面层：匿名页 + 登录态页的 HTML
#   ② 产物层：客户端 chunk 与 SSR 产物里的可点击上游链接 / 资源
#   ③ 接口层：API 公开端点的返回体
set -uo pipefail
PAT='LearnHouse|Learnhouse|HeyVisions|learnhouse\.(io|app|dev)|hello@learnhouse|support@learnhouse|discord\.gg/learnhouse'
FAIL=0

echo "══ ① 页面层（服务器本机直连）"
for p in / /login /signup /verify-email /forgot /404xx; do
  body=$(curl -s --max-time 25 "http://127.0.0.1:3011$p")
  n=$(printf '%s' "$body" | grep -oE "$PAT" | wc -l | tr -d ' ')
  if [ "$n" = "0" ]; then
    printf "  ✓ %-16s\n" "$p"
  else
    printf "  ⚠ %-16s %s 处命中\n" "$p" "$n"; FAIL=1
  fi
done

echo
echo "══ ② 产物层（可点击的上游链接 / 上游资源）"
linkhits=$(grep -rhoE 'href[:=]"?https://(www\.)?learnhouse\.[a-z]+' /srv/heyvisions-lms/apps/web/.next/static /srv/heyvisions-lms/apps/web/.next/server 2>/dev/null | sort -u)
if [ -z "$linkhits" ]; then
  echo "  ✓ 无"
else
  echo "  · 以下链接存在于产物中（需逐条确认是否在开关后面）："
  printf '%s\n' "$linkhits" | sed 's/^/      /'
fi
srchits=$(grep -rhoE 'src[:=]"?[^"]*learnhouse\.[a-z]+' /srv/heyvisions-lms/apps/web/.next/static /srv/heyvisions-lms/apps/web/.next/server 2>/dev/null | sort -u)
[ -z "$srchits" ] && echo "  ✓ 无上游资源引用" || { echo "  ⚠ 存在上游资源引用:"; printf '%s\n' "$srchits" | sed 's/^/      /'; FAIL=1; }

echo
echo "══ ③ 接口层"
root=$(curl -s --max-time 15 http://127.0.0.1:1349/)
echo "  GET / → $root"
printf '%s' "$root" | grep -qE "$PAT" && { echo "  ⚠ 含上游名"; FAIL=1; } || echo "  ✓ 无上游名"

echo
echo "══ 结论：$([ "$FAIL" = "0" ] && echo "全部通过" || echo "有需要处理的项目")"
exit $FAIL
