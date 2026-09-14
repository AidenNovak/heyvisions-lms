#!/usr/bin/env python3
"""把 locale 里「指代本平台自身」的上游品牌名换成 {{brand}} 变量。

区分两类 "LearnHouse"：

1. **平台自身**（本脚本处理）—— "欢迎回到 LearnHouse"、"继续即表示你同意 LearnHouse 的"。
   这类字符串里的名字就是我们自己，白标之后必须跟着品牌配置走。硬编码在 22 个 locale 里
   无法维护，改成 `{{brand}}` 由组件传入。

2. **上游这个外部实体**（不处理）—— "从 LearnHouse 导出的课程"、"Made with LearnHouse" 水印。
   这些指的是真实存在的第三方，替换成变量是错的。它们该被移除或按需隐藏，
   属于另一个决定，见 issue #12。

替换的是专有名词本身，不涉及翻译，所以对各语言都安全。
copyright 单独处理：原串是 "© {{year}} LearnHouse, Inc."，品牌后面不应再留 ", Inc."。

用法：
  python3 scripts/heyvisions/localize-brand-strings.py --locales apps/web/locales [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# 平台自指：字符串里的品牌名 = 我们自己。
SELF_REFERENCE_KEYS = (
    "auth.terms_text",
    "auth.image_title_login",
    "auth.image_title_signup",
    "onboarding.welcome.title",
    "embed.powered_by",
    "user.settings.security.mfa.codes_file_header",
)


def replace_brand(value: str, brand_pattern: re.Pattern[str], replacement: str) -> str | None:
    """把 value 里的上游品牌名换成 replacement；没命中返回 None。"""
    new = brand_pattern.sub(replacement, value)
    return new if new != value else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locales", default="apps/web/locales")
    ap.add_argument("--brand", default="LearnHouse", help="要被变量化的上游品牌名")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    locales_dir = Path(args.locales)
    # 用「两侧不是拉丁字母」而不是 `\b`：`\b` 在 CJK 语境下会失效
    # （"LearnHouse大学"、"LearnHouse에" 里品牌名后面紧跟的是非 ASCII 的单词字符，
    # Python 认为那里没有词边界），ja/ko 的硬编码就是这样被漏掉的。
    # 这里只要求两侧不是拉丁字母，既避免误伤 LearnHouseXxx，也覆盖 CJK 相连的写法。
    brand_pattern = re.compile(rf"(?<![A-Za-z]){re.escape(args.brand)}(?![A-Za-z])")

    total = 0
    for path in sorted(locales_dir.glob("*.json")):
        raw = path.read_text(encoding="utf-8-sig")
        had_bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
        data = json.loads(raw)
        changes: list[tuple[str, str, str]] = []

        for dotted in SELF_REFERENCE_KEYS:
            cur = _get(data, dotted)
            if not isinstance(cur, str):
                continue
            new = replace_brand(cur, brand_pattern, "{{brand}}")
            if new:
                _set(data, dotted, new)
                changes.append((dotted, cur, new))

        # copyright：品牌后不该留 ", Inc."
        cur = _get(data, "common.copyright")
        if isinstance(cur, str) and brand_pattern.search(cur):
            new = brand_pattern.sub("{{brand}}", cur)
            new = re.sub(r"\{\{brand\}\},?\s*Inc\.?", "{{brand}}", new).strip()
            _set(data, "common.copyright", new)
            changes.append(("common.copyright", cur, new))

        if not changes:
            continue

        # 复用 merge-locale-keys.py 的文本层写入：只改动的行变化，不重排文件。
        # 由于这里是"改值"而不是"加键"，直接按值做定点文本替换。
        updated = raw
        for _dotted, old, new in changes:
            updated = _replace_json_value(updated, old, new)

        after = json.loads(updated)
        for _dotted, old, new in changes:
            assert _find_value(after, new), f"{path.name}: 替换未生效 {new!r}"
        # 与原文件比：只有预期改动
        if json.loads(raw) == after and changes:
            raise SystemExit(f"{path.name}: 结构未变，替换可能失败")

        if not args.dry_run:
            path.write_text(("\ufeff" if had_bom else "") + updated, encoding="utf-8")

        total += len(changes)
        print(f"{path.name}: {len(changes)} 处")
        for dotted, old, new in changes:
            print(f"   {dotted}\n     - {old}\n     + {new}")

    print(f"\n合计 {total} 处" + ("（dry-run，未写入）" if args.dry_run else ""))
    return 0


def _replace_json_value(text: str, old: str, new: str) -> str:
    """在 JSON 文本里把某个字符串值替换成另一个（按 JSON 转义形式精确匹配）。"""
    old_enc = json.dumps(old, ensure_ascii=False)
    new_enc = json.dumps(new, ensure_ascii=False)
    if text.count(old_enc) != 1:
        # 同一个值出现多次时不猜，交给调用方人工处理
        raise SystemExit(f"值 {old!r} 在文件中出现 {text.count(old_enc)} 次，无法唯一定位")
    return text.replace(old_enc, new_enc, 1)


def _find_value(obj, target: str) -> bool:
    if isinstance(obj, dict):
        return any(_find_value(v, target) for v in obj.values())
    if isinstance(obj, str):
        return obj == target
    return False


def _get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set(obj, dotted, value):
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        cur = cur[part]
    cur[parts[-1]] = value


if __name__ == "__main__":
    raise SystemExit(main())
