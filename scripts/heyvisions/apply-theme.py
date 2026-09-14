#!/usr/bin/env python3
"""把 LMS 的视觉令牌对齐静态站 heyvisions.com（issue #4）。

设计依据与令牌对照见 docs/heyvisions/design-tokens.md。

做成脚本而不是手改，是因为改动分散在几个文件、且每条都是「精确替换一处」——
脚本能保证幂等（重复执行不产生额外改动）与可复核（每条替换都打印命中数）。

用法：
  python3 scripts/heyvisions/apply-theme.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"

# 静态站的字体栈（example/src/index.css 的 --font-sans），
# 中文字体位置与静态站一致，两处在 Windows 上会落到同一字面。
FONT_STACK = (
    "var(--font-default, 'Geist'), -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Roboto, Oxygen, Ubuntu, "
    "Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif"
)
OLD_FONT_STACK = (
    "var(--font-default, 'Wix Madefor Text'), -apple-system, BlinkMacSystemFont, "
    "'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', "
    "'Helvetica Neue', sans-serif"
)

EDITS: list[tuple[str, str, str, int]] = [
    # (文件, 原文, 新文, 期望命中数)
    (
        "app/layout.tsx",
        "import { Wix_Madefor_Text, Tajawal } from 'next/font/google'",
        "import { Geist, Tajawal } from 'next/font/google'",
        1,
    ),
    (
        "app/layout.tsx",
        """const wixMadeforText = Wix_Madefor_Text({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-default',
})""",
        """// Yet to Dawn fork：平台默认字体与静态站 yettodawn.com 一致（Geist）。
// 静态站自托管 Geist，这里用 next/font 取同一个字族：字体是「同一个产品」
// 最直接的信号，换掉上游的 Wix Madefor Text 后两处观感才连续。
// 中文由 globals.css 里的 PingFang SC / 微软雅黑 兜底（Geist 不含汉字）。
const geist = Geist({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-default',
})""",
        1,
    ),
    (
        "app/layout.tsx",
        "className={`${wixMadeforText.variable} ${tajawal.variable}`}",
        "className={`${geist.variable} ${tajawal.variable}`}",
        1,
    ),
    # 字体常量同时是「未选自定义字体」的哨兵值，跟着改，
    # 否则品牌设置页会把它显示成 "Wix Madefor Text (默认)"。
    ("lib/fonts.ts", "  'Fira Sans',\n  'IBM Plex Sans',", "  'Fira Sans',\n  'Geist',\n  'IBM Plex Sans',", 1),
    (
        "lib/fonts.ts",
        "export const DEFAULT_FONT = 'Wix Madefor Text'",
        """// 平台默认字体（`--font-default`，见 app/layout.tsx 的 next/font 声明）。
// 这个常量同时是「未选择自定义字体」的哨兵值：组织配置里 font 为空或等于它时，
// 走平台默认而不是去 Google Fonts 额外加载。
export const DEFAULT_FONT = 'Geist'""",
        1,
    ),
    # 中文字族必须写在 var() 之外：--font-default 由 next/font 注入且一定有值，
    # 写在 var() 的 fallback 位置的字族是死代码。
    ("styles/globals.css", OLD_FONT_STACK, FONT_STACK, 2),
    # 焦点环用品牌深林绿（静态站 --ring: #144338）。
    # 第四个元素起是「可接受的旧写法」：本仓库曾短暂用过暖橙版，脚本要能从它收敛。
    (
        "styles/globals.css",
        "    --border: 0 0% 89.8%;\n    --input: 0 0% 89.8%;\n    --ring: 0 0% 3.9%;",
        """    --border: 0 0% 89.8%;
    --input: 0 0% 89.8%;
    /* 焦点环用品牌深林绿，与静态站同一枚令牌（静态站 --ring: #144338）。
       品牌色只出现在焦点态：按钮与输入框的可见外观仍是中性黑白，
       与静态站「单一强调色、其余锌灰」的规则一致。 */
    --ring: 166.0 54.0% 17.1%;""",
        1,
        '    --ring: 17.5 88.3% 40.4%;',
    ),
    (
        "styles/globals.css",
        "    --border: 0 0% 14.9%;\n    --input: 0 0% 14.9%;\n    --ring: 0 0% 83.1%;",
        """    --border: 0 0% 14.9%;
    --input: 0 0% 14.9%;
    /* 暗色焦点环要亮一档：深绿 #144338 在近黑底上只有 1.78:1，
       换成同色系的浅绿 #6f9d8a（6.47:1）。 */
    --ring: 155.2 19.0% 52.5%;""",
        1,
        '    --ring: 19.4 66.5% 54.3%;',
    ),
    # 圆角基准：rounded-lg 用的就是它，界面里最常用的一档
    (
        "styles/globals.css",
        "    --radius: 0.5rem;",
        """    /* 圆角基准。Tailwind v4 通过 @theme 派生：lg=本值、md=本值-2px、sm=本值-4px。
       界面里最常用的是 rounded-lg（1300+ 处），所以让 lg 等于静态站最常用的
       圆角令牌 --r-sm: 10px，两处的卡片与控件弧度一致。 */
    --radius: 0.625rem;""",
        1,
    ),
    # 投影：静态站「发丝线 + 1px 投影」，层次靠边线不靠投影。
    # 这两条 utility 覆盖 700+ 处使用，改这里即全站生效。
    (
        "styles/globals.css",
        """  .nice-shadow {
    @apply shadow-md shadow-gray-300/25 outline outline-1 outline-neutral-200/40;
  }

  .light-shadow {
    @apply shadow-lg shadow-gray-300/15 outline outline-1 outline-neutral-200/30;
  }""",
        """  /* 卡片/控件的默认投影。静态站的观感是「发丝线 + 极浅投影」——
     层次靠边线而不是靠投影，所以这里把投影压到 1px 级别，
     与静态站的 --shadow-card (0 1px 2px rgba(0,0,0,.04)) 对齐；
     边线保留，它是主要的分层手段。这两条规则覆盖全部界面，
     改这一处即全站生效，不必逐个组件替换。 */
  .nice-shadow {
    @apply shadow-[0_1px_2px_rgba(0,0,0,0.04)] outline outline-1 outline-neutral-200/40;
  }

  .light-shadow {
    @apply shadow-[0_2px_8px_rgba(0,0,0,0.05)] outline outline-1 outline-neutral-200/30;
  }""",
        1,
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    by_file: dict[str, str] = {}
    failures: list[str] = []
    applied = 0

    for edit in EDITS:
        rel, old, new, expected = edit[0], edit[1], edit[2], edit[3]
        # 允许一条改动列出多个「可接受的旧写法」：上游原版，以及本仓库历史上
        # 应用过的版本。这样脚本能从任一状态收敛到目标，而不是只在全新检出上可用。
        priors = [old] + list(edit[4:]) if len(edit) > 4 else [old]

        if rel not in by_file:
            by_file[rel] = io.open(WEB / rel, encoding="utf-8").read()
        text = by_file[rel]

        if new in text and not any(p in text for p in priors):
            print(f"  已是目标状态，跳过：{rel} :: {old.splitlines()[0][:50]}")
            continue

        hit = next((p for p in priors if text.count(p) == expected), None)
        if hit is None:
            counts = [text.count(p) for p in priors]
            failures.append(f"{rel}: 期望命中 {expected} 处，实际 {counts} —— {old.splitlines()[0][:60]!r}")
            continue
        by_file[rel] = text.replace(hit, new)
        applied += 1

    if failures:
        for f in failures:
            print("失败:", f)
        return 1

    for rel, text in by_file.items():
        if args.dry_run:
            print(f"  （dry-run）{rel}")
            continue
        io.open(WEB / rel, "w", encoding="utf-8").write(text)
        print(f"  写入 {rel}")

    print(f"\n{applied} 处替换" + ("（dry-run）" if args.dry_run else "，已写入"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
