#!/usr/bin/env bash
# 检查服务器上部署的源码与仓库是否一致（只读，不做任何修改）。
#
# 为什么需要它：`server-rebuild-web.sh` 只重建 Web，而 API 的 Python 源码
# 是「安装时拷一份」就再没被保证过与仓库同步。曾因此出过一次真实故障 ——
# `services/email/branding.py` 比同目录的 `emails.py` 旧一天，
# `from ... import powered_by_url` 直接 ImportError，表现为 OAuth 建号后
# 界面只显示 “Authentication Failed”，而错误只落在服务端日志里。
#
# 用法（在 vultr-sg 上，或本机指定仓库路径）：
#   ./scripts/heyvisions/check-deploy-drift.sh [仓库路径] [部署路径]
#
# 退出码：0 = 一致；1 = 有差异（列出文件）；2 = 用法/环境错误
set -euo pipefail

REPO="${1:-/srv/heyvisions-lms}"
DEPLOY="${2:-/srv/heyvisions-lms}"

[ -d "$REPO/.git" ] || { echo "不是 git 仓库：$REPO" >&2; exit 2; }
[ -d "$DEPLOY/apps" ] || { echo "找不到部署目录：$DEPLOY/apps" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 用 git 导出「仓库当前 HEAD」的这几棵子树，再与部署端逐文件比 checksum。
# 只比源码树：tests/ 与 __pycache__ 不参与（前者不影响运行，后者是产物）。
PATHS=(apps/api/src apps/web/app apps/web/components apps/web/lib apps/web/services apps/web/locales apps/web/styles)
for p in "${PATHS[@]}"; do
  git -C "$REPO" archive HEAD "$p" 2>/dev/null | tar -x -C "$TMP" 2>/dev/null || true
done

diffs=0
for p in "${PATHS[@]}"; do
  [ -d "$TMP/$p" ] || continue
  [ -d "$DEPLOY/$p" ] || { echo "部署端缺少：$p"; diffs=$((diffs+1)); continue; }
  # --dry-run + --checksum：只报告差异，不传输、不删除
  while IFS= read -r f; do
    [ -n "$f" ] && [ "$f" != "./" ] && printf '%s\n' "$p/${f#./}"
  done < <(rsync -n -c -r --out-format='%n' "$TMP/$p/" "$DEPLOY/$p/" 2>/dev/null) | while read -r line; do
    printf '差异  %s\n' "$line"
  done
  n=$(rsync -n -c -r --out-format='%n' "$TMP/$p/" "$DEPLOY/$p/" 2>/dev/null | grep -vcE '^$|/$' || true)
  diffs=$((diffs + n))
done

echo
echo "仓库 HEAD: $(git -C "$REPO" rev-parse --short HEAD) ($(git -C "$REPO" rev-parse --abbrev-ref HEAD))"
if [ "$diffs" -eq 0 ]; then
  echo "结果：部署的源码与仓库一致"
  exit 0
fi
echo "结果：有 $diffs 个文件与仓库不一致（上面列出）"
echo
echo "常见的两种成因："
echo "  1) 部署端是旧副本 —— 同步即可："
echo "     rsync -c -r --exclude='__pycache__' <仓库>/apps/api/src/ <部署>/apps/api/src/"
echo "     同步后清字节码并重启："
echo "     find <部署>/apps/api/src -name __pycache__ -type d -exec rm -rf {} + && systemctl restart hv-lms-api"
echo "  2) 部署端有手工热修 —— 先把它回灌到仓库，再同步，不要直接覆盖。"
exit 1
