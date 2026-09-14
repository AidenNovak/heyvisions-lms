#!/usr/bin/env python3
"""把 website 仓库的课程单元正文转成**自包含**的 Markdown，供学习平台使用。

## 为什么需要这一步

单元正文的「模板或反例」一节写着「使用本页下方的『…』模板」，但模板文字**不在 .md 里**，
而是存于 `example/src/course/templates.js`，由**站点页面**注入
（`example/src/course-page.jsx` 在渲染到该节时额外插入一个可复制的模板块）。

学习平台只渲染裸 Markdown，没有这一层注入，于是每个单元都会指向一个不存在的模板 ——
学习者读到「见下方模板」却看不到模板。实测 6/6 个公开单元都是这样。

本脚本把模板**追加到该节末尾**生成平台专用副本：站点继续用它自己的注入（不受影响，
因为它读的是原始 .md），平台拿到的是自包含正文。两边同源（都来自 templates.js），
不存在两处维护的模板文字。

## 用法

  python3 scripts/heyvisions/build-lms-units.py \
      --website ~/projects/website --out /tmp/lms-units

只写 `--out` 目录，不动源仓库的任何文件。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 模板要插进的那一节。与站点 course-page.jsx 里判断的标题一致，改一处要改两处。
TEMPLATE_SECTION = "模板或反例"


def load_templates(website: Path) -> dict[str, str]:
    """用 node 读 templates.js，避免在 Python 里重解析 JS 字面量。"""
    mod = website / "example/src/course/templates.js"
    if not mod.exists():
        sys.exit(f"找不到模板源：{mod}")
    script = (
        f"import {{approvedTemplates}} from 'file://{mod}';"
        "console.log(JSON.stringify(approvedTemplates))"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"读取模板源失败：{out.stderr.strip()}")
    return json.loads(out.stdout)


def split_sections(markdown: str) -> list[tuple[str, list[str]]]:
    """按一级标题切分；返回 [(标题, 行列表)]，标题不含 '#'。"""
    sections: list[tuple[str, list[str]]] = []
    title: str | None = None
    body: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            if title is not None:
                sections.append((title, body))
            title = line[2:].strip()
            body = []
        else:
            body.append(line)
    if title is not None:
        sections.append((title, body))
    return sections


def inject_template(markdown: str, template: str, unit_key: str) -> tuple[str, str]:
    """把模板作为围栏代码块追加到「模板或反例」一节末尾。

    返回 (新正文, 结果说明)。该节不存在或已含围栏块时不改，并说明原因 ——
    静默跳过会让「模板没出现」看起来像脚本正常跑完了。
    """
    sections = split_sections(markdown)
    out: list[str] = []
    status = "未处理"
    for title, body in sections:
        out.append(f"# {title}")
        if title == TEMPLATE_SECTION:
            if any(line.startswith("```") for line in body):
                status = "该节已有代码块，跳过"
            else:
                while body and not body[-1].strip():
                    body.pop()
                body = (
                    body
                    + ["", "可直接复制到自己的工作区使用：", "", "```text", template, "```"]
                )
                status = "已注入模板"
        out.extend(body)
    return "\n".join(out).rstrip() + "\n", status


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--website", default="~/projects/website", help="website 仓库根目录")
    ap.add_argument("--out", required=True, help="输出目录（会被清空重建）")
    args = ap.parse_args()

    website = Path(args.website).expanduser()
    units_dir = website / "example/src/course-content/units"
    if not units_dir.is_dir():
        sys.exit(f"找不到单元目录：{units_dir}")

    templates = load_templates(website)
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.md"):
        stale.unlink()

    injected = skipped = 0
    for src in sorted(units_dir.glob("*.md")):
        unit_key = src.stem  # 站点侧 templateKey 就等于 unitKey（见 course/source.js）
        text = src.read_text(encoding="utf-8")
        template = templates.get(unit_key)
        if not template:
            (out_dir / src.name).write_text(text, encoding="utf-8")
            print(f"  {unit_key}: 无模板源，原样输出")
            continue
        new_text, status = inject_template(text, template, unit_key)
        (out_dir / src.name).write_text(new_text, encoding="utf-8")
        if status == "已注入模板":
            injected += 1
        else:
            skipped += 1
        print(f"  {unit_key}: {status}")

    print(f"\n输出到 {out_dir}：注入 {injected} 个，跳过 {skipped} 个，共 {len(list(out_dir.glob('*.md')))} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
