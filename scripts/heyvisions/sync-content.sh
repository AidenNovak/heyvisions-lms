#!/usr/bin/env bash
# Yet to Dawn LMS — 把 website 仓库的课程内容同步到服务器，并按需重跑导入。
#
#   scripts/heyvisions/sync-content.sh              # 同步 + 校正活动 URL
#   scripts/heyvisions/sync-content.sh --no-import  # 只同步文件
#
# 为什么需要它：单元正文的事实源在 website 仓库（`example/src/course-content/units/*.md`
# 与 `example/src/course/curriculum.js`），LMS 只在服务器上留一份拷贝。
# 改完正文不跑这一步，站点重新构建了而平台还是旧内容 —— 两边会不一致。
#
# 在**本机**（有 website 仓库的那台）执行，不是服务器上。
set -euo pipefail

SERVER="${HV_SERVER:-vultr-sg}"
WEBSITE="${HV_WEBSITE:-$HOME/projects/website}"
REMOTE_ROOT="${HV_CONTENT_DIR:-/srv/heyvisions-content}"
HOST="${HV_HOST:-learn.yettodawn.com}"
IMPORT=1

while (($#)); do
  case "$1" in
    --no-import) IMPORT=0; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done

SRC="$WEBSITE/example/src/course-content"
[ -d "$SRC/units" ] || { echo "找不到单元目录：$SRC/units" >&2; exit 1; }
[ -f "$WEBSITE/example/src/course/curriculum.js" ] || { echo "找不到课程合同" >&2; exit 1; }

echo "══ 同步内容 → $SERVER:$REMOTE_ROOT"
rsync -az --delete "$SRC/units/" "$SERVER:$REMOTE_ROOT/units/"
rsync -az "$WEBSITE/example/src/course/curriculum.js" "$SERVER:$REMOTE_ROOT/curriculum.js"

# import-course.py 用 node 以 ESM 方式 import 课程合同；该目录若被当成 CommonJS
# 会报「Named export not found」。补一个最小的 package.json 定住模块类型。
ssh "$SERVER" 'if [ ! -f '"$REMOTE_ROOT"'/package.json ]; then echo "{\"type\":\"module\"}" | sudo tee '"$REMOTE_ROOT"'/package.json >/dev/null; fi'

echo "已同步：$(ssh "$SERVER" "ls $REMOTE_ROOT/units | wc -l") 个单元"

[ "$IMPORT" = "1" ] || exit 0

echo
echo "══ 校正平台侧的活动 URL（幂等，只动 markdown_url）"
# --units-base 必须是**对外可达**的地址：单元正文由浏览器直接 fetch，
# 写成回环地址时每个课时页都会显示 Failed to fetch markdown。
ssh "$SERVER" 'sudo bash -c "
  set -a; . /srv/heyvisions-secrets/lms-prod.env; set +a
  export PATH=/opt/hv-node/bin:/usr/bin:/bin
  cd /srv/heyvisions-lms
  python3 scripts/heyvisions/import-course.py \
    --website /srv/heyvisions-website \
    --api http://127.0.0.1:1349/api/v1 \
    --units-base https://'"$HOST"'/units \
    --secrets /srv/heyvisions-secrets/lms-prod.env
"'

echo
echo "完成。抽查："
curl -s -o /dev/null -w "  %{http_code}  https://$HOST/units/judge-task-01.md\n" --max-time 20 "https://$HOST/units/judge-task-01.md"
