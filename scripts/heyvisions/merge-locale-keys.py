#!/usr/bin/env python3
"""按路径改/补 locale JSON 的键，**不重排、不重格式化**既有内容。

为什么需要它：`json.dump` 会把文件里所有内联对象（`{ "a": 1, "b": 2 }`）展开成多行，
zh.json 里有大量这种写法，直接重序列化会产生两千多行无意义 diff，把真正的改动淹没，
也会让上游同步变成不可能。所以这里在**文本层**改：定位到具体路径的值 token 替换，
新增的键追加到父对象的最后一个成员之后。

**按路径定位而不是按内容匹配**：`'Open'`、`'Save'` 这类词在同一个文件里出现多次，
按内容替换会打错地方。

用法：
  python3 scripts/heyvisions/merge-locale-keys.py \
      --locale apps/web/locales/zh.json --keys /tmp/zh-changes.json [--dry-run]

`--keys` 是扁平 JSON：{"auth.mfa_title": "两步验证", ...}，键用点号表示嵌套路径。
父对象不存在时会创建（按需补出中间层）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class TextJSON:
    """在保留原文格式的前提下，记录每个对象的可插入位置。"""

    def __init__(self, text: str):
        self.s = text
        self.i = 0
        # path -> {"insert_at": int, "indent": str, "has_members": bool, "multiline": bool}
        self.objects: dict[tuple[str, ...], dict] = {}
        # path -> (start, end) 的字符区间，指向该叶子值的原始 token。
        # 用于按路径精确改值：同一个英文串在文件里出现多次时，
        # 按内容匹配会打错地方，按路径定位不会。
        self.values: dict[tuple[str, ...], tuple[int, int]] = {}

    # -- 词法 --
    def _ws(self) -> int:
        start = self.i
        while self.i < len(self.s) and self.s[self.i] in " \t\n\r":
            self.i += 1
        return self.i - start

    def _string(self) -> str:
        assert self.s[self.i] == '"'
        j = self.i + 1
        while True:
            c = self.s[j]
            if c == "\\":
                j += 2
                continue
            if c == '"':
                break
            j += 1
        out = json.loads(self.s[self.i : j + 1])
        self.i = j + 1
        return out

    def _skip_scalar(self) -> None:
        while self.i < len(self.s) and self.s[self.i] not in ",}]":
            self.i += 1

    # -- 语法 --
    def value(self, path: tuple[str, ...]) -> None:
        self._ws()
        start = self.i
        c = self.s[self.i]
        if c == "{":
            self.obj(path)
        elif c == "[":
            self.arr(path)
        elif c == '"':
            self._string()
            self.values[path] = (start, self.i)
        else:
            self._skip_scalar()
            self.values[path] = (start, self.i)

    def arr(self, path: tuple[str, ...]) -> None:
        self.i += 1
        self._ws()
        if self.s[self.i] == "]":
            self.i += 1
            return
        while True:
            self.value(path)
            self._ws()
            if self.s[self.i] == ",":
                self.i += 1
                continue
            assert self.s[self.i] == "]", (self.i, self.s[self.i - 40 : self.i + 10])
            self.i += 1
            return

    def obj(self, path: tuple[str, ...]) -> None:
        brace_pos = self.i
        self.i += 1
        self._ws()
        if self.s[self.i] == "}":
            self.objects[path] = {
                "insert_at": self.i,
                "empty": True,
                "multiline": False,
                "indent": "",
            }
            self.i += 1
            return

        has_members = False
        last_member_end = None
        while True:
            self._ws()
            key = self._string()
            self._ws()
            assert self.s[self.i] == ":"
            self.i += 1
            self.value(path + (key,))
            last_member_end = self.i
            has_members = True
            self._ws()
            if self.s[self.i] == ",":
                self.i += 1
                continue
            assert self.s[self.i] == "}", (path, self.i, self.s[self.i - 40 : self.i + 10])
            break

        close_pos = self.i
        segment = self.s[last_member_end:close_pos]
        multiline = "\n" in segment
        # 只取该行键名之前的前导空白作为行缩进（`  "common": ` → `  `），
        # 对象成员键缩进 = 行缩进 + 2。
        line_start = self.s.rfind("\n", 0, brace_pos) + 1
        prefix = self.s[line_start:brace_pos]
        line_indent = prefix[: len(prefix) - len(prefix.lstrip())]
        self.objects[path] = {
            "insert_at": last_member_end,
            "close_pos": close_pos,
            "empty": not has_members,
            "multiline": multiline,
            "indent": line_indent + "  ",
            "tail": segment,
        }
        self.i = close_pos + 1


def render_nested(parts: list[str], members: dict[str, object], base_indent: str) -> str:
    """把 `parts` 路径 + 叶子成员渲染成 JSON 片段，缩进从 base_indent 起。"""
    key = json.dumps(parts[0], ensure_ascii=False)
    body = ", ".join(
        f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
        for k, v in members.items()
    )
    if len(parts) == 1:
        return f"{key}: {{ {body} }}"
    inner = render_nested(parts[1:], members, base_indent + "  ")
    return f"{key}: {{\n{base_indent}  {inner}\n{base_indent}}}"


def apply_changes(text: str, changes: dict[str, object]) -> tuple[str, list[str]]:
    """按路径改值或补键，返回 (新文本, 报告行)。

    已存在的键 → 在原文里就地替换它的值 token（按路径定位，不按内容匹配，
    所以同一个英文串在文件里出现多次也不会打错地方）。
    不存在的键 → 交给 add_keys 插入。
    """
    parser = TextJSON(text)
    parser.value(())

    replacements: list[tuple[int, int, str]] = []
    additions: dict[str, object] = {}
    report: list[str] = []

    for dotted, value in changes.items():
        path = tuple(dotted.split("."))
        if path in parser.values:
            start, end = parser.values[path]
            old = json.loads(text[start:end])
            if old == value:
                continue
            replacements.append((start, end, json.dumps(value, ensure_ascii=False)))
            report.append(f"  改 {dotted}")
        else:
            additions[dotted] = value

    # 先替换（后面的位置会被 add_keys 用到，两者互不重叠：替换只动已有值的区间）
    for start, end, encoded in sorted(replacements, key=lambda r: r[0], reverse=True):
        text = text[:start] + encoded + text[end:]
    if additions:
        text = add_keys(text, additions)
        report.extend(f"  加 {k}" for k in additions)

    return text, report


def add_keys(text: str, additions: dict[str, object]) -> str:
    parser = TextJSON(text)
    parser.value(())
    edits: list[tuple[int, str]] = []
    # 同一父对象下新增的键要合并成一次插入，否则多次插入同一位置会互相覆盖。
    grouped: dict[tuple[str, ...], dict[str, object]] = {}
    created: dict[tuple[str, ...], dict] = {}

    for dotted, value in additions.items():
        parts = dotted.split(".")
        *parents, leaf = parts
        parent_path = tuple(parents)
        record = parser.objects.get(parent_path)
        if record is None:
            # 父层缺失：先补出中间层（例如 auth.complete_profile 在 zh 里没有）。
            # 深度优先找到最深的已存在祖先，把剩下的层级连键一起写成嵌套块。
            ancestor = parent_path
            while ancestor and ancestor not in parser.objects:
                ancestor = ancestor[:-1]
            if ancestor not in parser.objects:
                raise SystemExit(f"连根对象都找不到，中止：{dotted}")
            base = parser.objects[ancestor]
            if base["empty"] or not base["multiline"]:
                raise SystemExit(
                    f"{'.'.join(ancestor) or '(根)'} 是空对象或内联对象，无法安全地补出 {'.'.join(parent_path)}。"
                    "请先手动建出该层。"
                )
            missing = list(parent_path[len(ancestor):])
            created.setdefault((ancestor, tuple(missing)), {})[leaf] = value
            continue
        grouped.setdefault(parent_path, {})[leaf] = value

    for parent_path, members in grouped.items():
        record = parser.objects[parent_path]
        if record["empty"] or not record["multiline"]:
            # 空对象 / 内联对象：就地追加，保持原样（不动已有行）。
            encoded = ", ".join(
                f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                for k, v in members.items()
            )
            text_insert = "{" + encoded + "}" if record["empty"] else f", {encoded}"
            edits.append((record["insert_at"], text_insert))
            continue
        # 多行对象：每个键一行，缩进与既有成员一致。
        chunk = "".join(
            f',\n{record["indent"]}{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}'
            for k, v in members.items()
        )
        edits.append((record["insert_at"], chunk))

    for (ancestor, missing), members in created.items():
        record = parser.objects[ancestor]
        # 新键所在的缩进 = 祖先对象内成员键的缩进
        indent = record["indent"]
        block = render_nested(list(missing), members, indent)
        edits.append((record["insert_at"], ",\n" + indent + block))

    # 从后往前改，位置不失效
    for pos, chunk in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:pos] + chunk + text[pos:]
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locale", required=True, help="目标 locale 文件")
    ap.add_argument("--keys", required=True, help="键值的扁平 JSON：已存在的键改值，不存在的键插入")
    ap.add_argument("--dry-run", action="store_true", help="只报告，不写入")
    args = ap.parse_args()

    locale_path = Path(args.locale)
    had_bom = locale_path.read_bytes().startswith(b"\xef\xbb\xbf")
    raw = locale_path.read_text(encoding="utf-8-sig")
    changes = json.loads(Path(args.keys).read_text(encoding="utf-8"))

    if not changes:
        print("没有要改的键。")
        return 0

    before = json.loads(raw)
    updated, report = apply_changes(raw, changes)
    after = json.loads(updated)  # 语法校验：解析失败即报错，不落盘

    # 安全性校验：改动的键必须恰好等于目标值，未提到的键必须原样保留。
    for k, v in changes.items():
        if _get(after, k) != v:
            raise SystemExit(f"目标值未生效：{k}（得到 {_get(after, k)!r}）")
    for k in _flat(before):
        if k in changes:
            continue
        if _get(after, k) != _get(before, k):
            raise SystemExit(f"未提及的键被改动，中止：{k}")

    changed = len(changes)
    delta = len(updated.splitlines()) - len(raw.splitlines())
    print(f"{changed} 个键，文件行数 {len(raw.splitlines())} → {len(updated.splitlines())}（{delta:+d}）")
    if len(report) <= 25:
        print("\n".join(report))

    if args.dry_run:
        print("dry-run，未写入。")
        return 0
    # BOM 按原样保留：上游 zh.json 没有 BOM，不要让脚本给它加上。
    locale_path.write_text(("\ufeff" if had_bom else "") + updated, encoding="utf-8")
    return 0


def _flat(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _flat(v, key)
        else:
            yield key


def _get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


if __name__ == "__main__":
    raise SystemExit(main())
