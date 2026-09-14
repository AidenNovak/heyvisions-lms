#!/usr/bin/env python3
"""把 API 事务性邮件文案里「指代本平台自身」的上游品牌名换成 {brand} 变量。

覆盖 `apps/api/src/services/email/translations.py` 的 84 处（20 个语言包 × 8 个键）。

区分两类 "LearnHouse"：

1. **平台自身**（本脚本处理）—— "Welcome to LearnHouse"、"Powered by LearnHouse"、
   "…permanently removed from LearnHouse."。这些字符串里的名字就是我们自己，
   白标之后必须跟着品牌配置走。用 `{brand}` 占位符（该文件里 email_verification.*
   与 magic_login.* 已经在用同一个占位符，str.format 契约已存在），
   调用方从 `get_learnhouse_config().site_name` 取值后传入。
2. **上游这个外部实体**（不处理）—— 课程导出的 "LearnHouse export format" 之类。
   那些指的是真实存在的第三方格式名，替换成变量是错的。

替换的是专有名词本身，不涉及翻译，所以对各语言都安全（含 ja/ko 这类品牌名与
CJK 相连、两边没有词边界的写法）。

`academy_link_text` 单独处理，不走 `{brand}`：它原本是上游社区站的链接文案
（"LearnHouse Academy"），本 fork 没有对应资源，链接本身改为可配置
（`LEARNHOUSE_ACADEMY_URL`，默认空 → 不渲染该句），文案随之改成中性的
「帮助中心」并按语言给出译文，而不是留着上游品牌名。

用法：
  python3 scripts/heyvisions/localize-email-brand-strings.py [--dry-run]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

DEFAULT_TARGET = "apps/api/src/services/email/translations.py"

# 平台自指：值里的品牌名 = 我们自己。
SELF_REFERENCE_KEYS = (
    "account_creation.subject",
    "account_creation.body",
    "common.powered_by",
    "org_created.footer",
    "org_deleted.body",
    "account_deleted.subject",
    "account_deleted.body",
)

# 上游社区站链接的文案 → 中性说法（帮助中心），逐语言给出。
# 未列出的语言会被断言拦下，避免静默漏掉一种语言。
ACADEMY_LABELS: dict[str, str] = {
    "en": "the help centre",
    "fr": "le centre d'aide",
    "de": "das Hilfe-Center",
    "es": "el centro de ayuda",
    "ar": "مركز المساعدة",
    "ja": "ヘルプセンター",
    "pt": "a central de ajuda",
    "ru": "справочный центр",
    "zh": "帮助中心",
    "hi": "सहायता केंद्र",
    "ko": "도움말 센터",
    "it": "il centro assistenza",
    "tr": "yardım merkezi",
    "vi": "trung tâm trợ giúp",
    "id": "pusat bantuan",
    "pl": "centrum pomocy",
    "uk": "довідковий центр",
    "nl": "het helpcentrum",
    "th": "ศูนย์ช่วยเหลือ",
    "bn": "সহায়তা কেন্দ্র",
}


def brand_pattern(brand: str) -> re.Pattern[str]:
    """品牌名的匹配式：两侧不是拉丁字母。

    用 `\\b` 会在 CJK 语境下失效（"LearnHouseアカデミー"、"LearnHouse에" 里品牌名
    后面紧跟的是非 ASCII 的单词字符，Python 认为那里没有词边界），ja/ko 因此会被
    静默漏掉 —— 与 `localize-brand-strings.py` 同一判据。
    """
    return re.compile(rf"(?<![A-Za-z]){re.escape(brand)}(?![A-Za-z])")


def _email_translations_node(tree: ast.Module) -> ast.Dict:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(getattr(t, "id", None) == "EMAIL_TRANSLATIONS" for t in targets):
            assert isinstance(node.value, ast.Dict), "EMAIL_TRANSLATIONS 必须是字面量 dict"
            return node.value
    raise SystemExit("在目标文件里找不到 EMAIL_TRANSLATIONS")


def _absolute_span(source: str, node: ast.Constant) -> tuple[int, int]:
    """节点在源码里的绝对 **字节** 区间。

    ast 的 `col_offset` / `end_col_offset` 以 UTF-8 字节计，而这里要替换的字符串
    里有 CJK、西里尔、阿拉伯文 —— 直接当字符下标用会切错位置（阿拉伯文那行会
    吃掉半句）。整个替换过程一律走 bytes，最后再 decode 回文本。
    """
    lines = source.splitlines(keepends=True)
    starts = []
    pos = 0
    for line in lines:
        starts.append(pos)
        pos += len(line.encode("utf-8"))
    start = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    return start, end


def collect_edits(source: str, pattern: re.Pattern[str]):
    """返回 [(lang, key, old_value, new_value, start, end)]，按位置排序。"""
    tree = ast.parse(source)
    table = _email_translations_node(tree)
    edits = []
    for key_node, bundle_node in zip(table.keys, table.values):
        lang = ast.literal_eval(key_node)
        assert isinstance(bundle_node, ast.Dict)
        for k_node, v_node in zip(bundle_node.keys, bundle_node.values):
            key = ast.literal_eval(k_node)
            if not isinstance(key, str) or not isinstance(v_node, ast.Constant):
                continue
            old = v_node.value
            if not isinstance(old, str):
                continue
            if key in SELF_REFERENCE_KEYS:
                new = pattern.sub("{brand}", old)
                if new == old:
                    continue
            elif key == "academy_link_text":
                if lang not in ACADEMY_LABELS:
                    raise SystemExit(f"{lang}: academy_link_text 没有对应译文，先补 ACADEMY_LABELS")
                new = ACADEMY_LABELS[lang]
                if new == old:
                    continue
            else:
                continue
            start, end = _absolute_span(source, v_node)
            edits.append((lang, key, old, new, start, end))

    # 同一位置的重复编辑会互相覆盖，先挡住。
    spans = [e[4:6] for e in edits]
    assert len(spans) == len(set(spans)), "同一个字面量被匹配了两次"
    return sorted(edits, key=lambda e: e[4])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--brand", default="LearnHouse", help="要被变量化的上游品牌名")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = Path(args.target)
    source = path.read_text(encoding="utf-8")
    pattern = args.brand
    pattern = brand_pattern(pattern)

    edits = collect_edits(source, pattern)
    if not edits:
        print("没有需要改动的字符串（幂等）")
        return 0

    # 从后往前替换，避免前面的改动把后面的偏移量顶歪。字面量统一重写成
    # 双引号 + JSON 转义（`ensure_ascii=False`），与该文件原有的写法一致：
    # 值里只有撇号一类字符，逐字保留；" 与 \ 会按 Python 字符串字面量规则转义。
    updated = source.encode("utf-8")
    for _lang, _key, _old, new, start, end in reversed(edits):
        literal = json.dumps(new, ensure_ascii=False).encode("utf-8")
        updated = updated[:start] + literal + updated[end:]
    updated_text = updated.decode("utf-8")

    # 语法必须仍然成立，且结构上只有这些值变了。
    after_tree = ast.parse(updated_text)
    after = ast.literal_eval(_email_translations_node(after_tree))
    before = ast.literal_eval(_email_translations_node(ast.parse(source)))
    assert set(after) == set(before), "语言包集合发生了变化"
    expected = {lang: dict(bundle) for lang, bundle in before.items()}
    for lang, key, _old, new, _s, _e in edits:
        expected[lang][key] = new
    assert after == expected, "解析结果与预期不符"

    remaining = pattern.findall(updated_text)
    assert not remaining, f"仍有 {len(remaining)} 处品牌名未处理"

    print(f"{path}: 共 {len(edits)} 处")
    by_lang: dict[str, list[tuple[str, str, str]]] = {}
    for lang, key, old, new, _s, _e in edits:
        by_lang.setdefault(lang, []).append((key, old, new))
    for lang in sorted(by_lang):
        print(f"  {lang}: {len(by_lang[lang])} 处")
        if lang == "en":
            for key, old, new in by_lang[lang]:
                print(f"    {key}\n      - {old}\n      + {new}")

    if not args.dry_run:
        path.write_text(updated_text, encoding="utf-8")
    print(f"合计 {len(edits)} 处" + ("（dry-run，未写入）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
