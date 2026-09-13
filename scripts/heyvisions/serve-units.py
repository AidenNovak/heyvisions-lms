#!/usr/bin/env python3
"""带 CORS 的静态文件服务，给 Markdown 活动提供 .md URL。

单元正文的事实源是 website 仓库，本服务直接指向那里，不在本仓库留副本。
生产形态约等于对象存储 / CDN 托管 .md；这里只是本地等价物。

服务根目录是 **course-content 目录**（其下是 units/），不是 units 目录本身：
活动的 markdown_url 形如 <base>/units/<unitKey>.md，把根目录设成 units 会让
/units/... 全部 404，课程页显示 "Failed to fetch markdown (404)"。

用法：
  python3 scripts/heyvisions/serve-units.py --root ~/projects/website/example/src/course-content
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 浏览器会直接拉取 markdown_url，缺 CORS 头会导致编辑器 Failed to fetch
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):  # noqa: N802 (http.server 约定)
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f"[units] {self.address_string()} {fmt % args}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="~/projects/website/example/src/course-content")
    ap.add_argument("--port", type=int, default=8022)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        raise SystemExit(f"内容目录不存在：{root}")
    if not (root / "units").is_dir():
        # 传成 units 目录本身是最容易犯的错，直接说清楚。
        raise SystemExit(f"{root} 下没有 units/。--root 要指向 course-content 目录（其下是 units/）。")

    handler = partial(CORSHandler, directory=str(root))
    print(f"服务 {root} 于 http://{args.host}:{args.port}/units/<unitKey>.md")
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
