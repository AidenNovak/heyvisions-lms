#!/usr/bin/env python3
"""把仍然硬编码上游品牌名的 locale 文案收尾处理干净。

分工（与 `localize-brand-strings.py` 一致，这里只补它没覆盖的键）：

1. **平台自指** —— 串里的品牌名 = 本平台 → 换成 `{{brand}}`，由组件传入。
   替换的是专有名词本身，不涉及翻译，对各语言都安全。

2. **上游专有资源名** —— "LearnHouse University" / "The Classroom" 指的是上游
   自己的站点，本平台没有对应物。这两张卡片在代码里已改成「配置了品牌文档 /
   社区地址才渲染」，所以标签也换成中性说法：英文改写，其余语言删键并回落到
   英文（i18next 的 `fallbackLng: 'en'`）—— 留着旧译文等于把第三方名字继续
   显示给用户，比显示英文更糟。

3. **不动** ——
   - `*.watermark_label/_desc`：描述的就是上游水印本身，开启时显示 "Made with
     LearnHouse" 是正确的署名。
   - `courses.import.learnhouse_*` / `dashboard.courses.import_learnhouse*`：
     "LearnHouse 课程导出包" 是一种**外部文件格式**的名字（类似「导入 WordPress
     站点」），改名会让功能说不通。
   - 没有任何调用点的死键（`teach_the_world.description`、
     `dashboard.home.learnhouse_university`、`settings.showcase_*`）：不渲染，
     改它只是制造 diff。

用法：
  python3 scripts/heyvisions/localize-remaining.py --locales apps/web/locales [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# 1) 平台自指：换成 {{brand}}
#    前 7 个是 `localize-brand-strings.py` 早先处理过的键；ja/ko 当年因为词边界
#    的正则问题被漏掉（"LearnHouse大学" / "LearnHouse에" 匹配不上 `\bLearnHouse\b`），
#    这里用修正后的判据补上，两个脚本的结果因此收敛到同一套。
SELF_REFERENCE_KEYS = (
    "common.copyright",
    "auth.terms_text",
    "auth.image_title_login",
    "auth.image_title_signup",
    "onboarding.welcome.title",
    "embed.powered_by",
    "user.settings.security.mfa.codes_file_header",
    "common.help_menu.website",
    "common.help_menu.feedback_description",
    "hub_new.createOrg.testHint.suffix",
    "dashboard.organization.branding.previews.thumbnail_desc",
    "dashboard.organization.security.session_sharing_label",
    "dashboard.organization.security.session_sharing_hint",
)

# 2) 上游专有资源名：英文改写，其余语言删键回落
NEUTRAL_REWRITE = {
    "onboarding.steps.teach_the_world.university": "Guides & tutorials",
    "onboarding.steps.teach_the_world.classroom": "Community & discussion",
}

# 3) 只从这些语言里删掉的键（英文源已无品牌名，旧译文反而带品牌）
DELETE_ONLY_KEYS = {
    "common.plans.feature_restricted.api_access.description": ("bn",),
}


def get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _pair_pattern(dotted: str, value: str, leading_newline: bool) -> re.Pattern[str]:
    """
    构造「键 + 值」的匹配式。

    必须把键名一起锚进模式：同一个值在不同键下可能重复出现（例如
    `dashboard.home.learnhouse_university` 与
    `onboarding.steps.teach_the_world.university` 的值都是 "LearnHouse
    University" 的译文），只按值定位会撞上「出现 N 次，无法唯一确定」。
    键名在文件里是唯一的，锚上就够。
    """
    leaf = dotted.split(".")[-1]
    val_enc = json.dumps(value, ensure_ascii=False)
    prefix = r"\n[ \t]*" if leading_newline else r""
    return re.compile(
        prefix + r'"' + re.escape(leaf) + r'"[ \t]*:[ \t]*' + re.escape(val_enc) + r"[ \t]*,?"
    )


def replace_value_text(text: str, dotted: str, old: str, new: str) -> str:
    """
    把某个键的值换成新值（键名锚定，保证作用于正确的那一处）。

    尾部可能跟着一个逗号（该键不是对象的最后一个成员），替换时必须原样保留 ——
    漏掉它会让整个文件变成非法 JSON（踩过）。
    """
    leaf = dotted.split(".")[-1]
    val_enc = json.dumps(old, ensure_ascii=False)
    pat = re.compile(
        r'"' + re.escape(leaf) + r'"[ \t]*:[ \t]*' + re.escape(val_enc) + r'([ \t]*,?)'
    )
    matches = list(pat.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"键 {dotted} 命中 {len(matches)} 处，无法唯一定位")
    m = matches[0]
    new_enc = json.dumps(new, ensure_ascii=False)
    start, end = m.span()
    return text[:start] + f'"{leaf}": {new_enc}' + m.group(1) + text[end:]


def drop_key_text(text: str, dotted: str, value: str) -> str:
    """
    从 JSON 文本里删掉一个键值对（含缩进）。

    只在文本层做，避免整个文件重写——这些 locale 文件里有紧凑成一行的小对象，
    整体 dump 会把它们展开，产生大量无关 diff。

    要处理尾逗号：如果被删的是对象最后一个成员，逗号挂在**上一个**成员行尾，
    直接切掉键值会留下 `...,\n}` 这种非法 JSON。所以删完再把悬空逗号收掉。
    """
    pat = _pair_pattern(dotted, value, leading_newline=True)
    matches = list(pat.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"键 {dotted} 命中 {len(matches)} 处，无法唯一定位")
    start, end = matches[0].span()
    out = text[:start] + text[end:]

    # 收尾逗号：删完之后，若「上一个非空白字符是逗号」而「下一个非空白字符是 } 或 ]」，
    # 说明被删的是最后一个成员，把那个逗号去掉。
    # 注意是**所有空白**（含换行）都要跳过：被删项与下一个字符之间隔着一个 `\n`，
    # 只跳空格与制表符会停在这个换行上，判断永远不成立（踩过）。
    before = start - 1
    while before >= 0 and out[before].isspace():
        before -= 1
    after = start
    while after < len(out) and out[after].isspace():
        after += 1
    if before >= 0 and out[before] == "," and after < len(out) and out[after] in "}]":
        out = out[:before] + out[before + 1:]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locales", default="apps/web/locales")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    locales_dir = Path(args.locales)
    # 词边界用「两侧不是拉丁字母」而不是 \b：
    # 中文/日文/韩文里品牌名与文字直接相连（"LearnHouse大学"、"LearnHouse에"），
    # Python 的 \w 把 CJK 也算作单词字符，`\bLearnHouse\b` 在这些位置**匹配不上**，
    # 于是静默漏掉 ja/ko 的硬编码（踩过）。这里只要求两侧不是拉丁字母。
    brand_pat = re.compile(r"(?<![A-Za-z])LearnHouse(?![A-Za-z])")
    domain_pat = re.compile(r"(?<![A-Za-z])learnhouse\.io(?![A-Za-z])")

    total = 0
    for path in sorted(locales_dir.glob("*.json")):
        lang = path.stem
        raw = path.read_text(encoding="utf-8-sig")
        had_bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
        data = json.loads(raw)
        text = raw
        changes: list[tuple[str, str, str]] = []

        # 1) 自指 → {{brand}}（顺带处理 learnhouse.io 这种域名自指）
        for dotted in SELF_REFERENCE_KEYS:
            cur = get(data, dotted)
            if not isinstance(cur, str):
                continue
            new = domain_pat.sub("{{brand}}", cur)
            new = brand_pat.sub("{{brand}}", new)
            if new != cur:
                changes.append((dotted, cur, new))

        # 2) 中性改写（仅英文）／其余语言删键
        for dotted, neutral in NEUTRAL_REWRITE.items():
            cur = get(data, dotted)
            if not isinstance(cur, str) or not brand_pat.search(cur):
                continue
            if lang == "en":
                changes.append((dotted, cur, neutral))
            else:
                changes.append((dotted, cur, "__DELETE__"))

        # 3) 指定语言里删键
        for dotted, langs in DELETE_ONLY_KEYS.items():
            if lang not in langs:
                continue
            cur = get(data, dotted)
            if isinstance(cur, str) and brand_pat.search(cur):
                changes.append((dotted, cur, "__DELETE__"))

        if not changes:
            continue

        # 先改值，再删键（删键会动行结构，放最后）
        for dotted, old, new in changes:
            if new == "__DELETE__":
                continue
            text = replace_value_text(text, dotted, old, new)
        for dotted, old, new in changes:
            if new != "__DELETE__":
                continue
            text = drop_key_text(text, dotted, old)

        after = json.loads(text)
        # 校验：该语言里这些键要么已改好，要么已删除
        for dotted, old, new in changes:
            now = get(after, dotted)
            if new == "__DELETE__":
                assert now is None, f"{path.name}: {dotted} 未被删除"
            else:
                assert now == new, f"{path.name}: {dotted} 替换未生效"

        if not args.dry_run:
            path.write_text(("\ufeff" if had_bom else "") + text, encoding="utf-8")

        total += len(changes)
        print(f"{path.name}: {len(changes)} 处")
        for dotted, old, new in changes:
            tail = "（删除，回落英文）" if new == "__DELETE__" else ""
            print(f"   {dotted}{tail}")
            print(f"     - {old[:100]}")
            if new != "__DELETE__":
                print(f"     + {new[:100]}")

    print(f"\n合计 {total} 处" + ("（dry-run，未写入）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
