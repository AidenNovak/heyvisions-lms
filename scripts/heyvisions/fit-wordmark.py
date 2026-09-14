#!/usr/bin/env python3
"""从品牌稿里拟合出「YET TO DAWN」字标的矢量轮廓。

为什么不直接用 `<text>`：原字标是 `<text>` + 字体栈，靠浏览器的字体渲染。
服务器端没有这些字体，不同机器渲染出来的字宽和字形都不一样，而 logo
不该随环境变形。而且品牌稿用的是一款几何无衬线体，系统字体栈里没有对应字形，
用 Arial 顶着渲染出来的东西不是这个品牌的样子。所以从稿子里取轮廓。

与标记（两片帆）那套拟合的区别，也是这里唯一的技术难点：**字母带孔**。
O、D、R、A 中间都有封闭的空隙（counter）。标记是实心的，所以那边用
`binary_fill_holes` 把洞补上；这里不能补，否则 O 会糊成一个实心块。
做法是把所有等值线（外轮廓 + 孔轮廓）一起取出来放进同一条 path，
用 `fill-rule="evenodd"` 让相交次数为偶的区域成为空 —— 这是 SVG 处理
带孔字形的标准做法。

用法：
  python3 scripts/heyvisions/fit-wordmark.py --src "<品牌稿 PNG>" --out apps/web/public/lrn-text.svg
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

import numpy as np
from PIL import Image


def text_mask(img: Image.Image, colors: dict[str, tuple[int, int, int]], min_gap: int = 12) -> np.ndarray:
    """
    取出品牌稿里的字标部分（右半），丢掉左边的帆形标记。

    按列统计内容量找空白带：标记与字标之间一定有一段明显的空白。
    取最宽的那条空白带作为切分点，比写死坐标更耐得住稿子重新导出。
    """
    a = np.asarray(img.convert("RGB")).astype(int)
    bg = np.array(colors["bg"])
    ink = np.array(colors["ink"])
    mark = (np.abs(a - ink).sum(axis=2) < 200) & (np.abs(a - bg).sum(axis=2) > 80)

    colsum = mark.sum(axis=0)
    gaps: list[tuple[int, int]] = []
    run: int | None = None
    for i, v in enumerate(colsum):
        if v == 0:
            if run is None:
                run = i
        else:
            if run is not None:
                gaps.append((run, i - 1))
                run = None
    if run is not None:
        gaps.append((run, len(colsum) - 1))

    # 只在图像中间区域找切分点，避免把两端的大片空白也当成候选
    width = a.shape[1]
    inner = [g for g in gaps if g[0] > width * 0.15 and g[1] < width * 0.85 and (g[1] - g[0]) >= min_gap]
    if not inner:
        raise SystemExit("找不到标记与字标之间的空白带，检查稿子或调 --min-gap")
    cut = max(inner, key=lambda g: g[1] - g[0])
    return mark[:, cut[1] + 1 :]


def trace_all(mask: np.ndarray) -> list[np.ndarray]:
    """
    取掩码的全部等值线（外轮廓与孔各一条）。

    与标记脚本的关键差别：这里**取所有**曲线，不只取最长的那条 ——
    孔就是要靠这些额外曲线表达。
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure()
    try:
        cs = plt.contour(mask.astype(float), levels=[0.5])
        segs = [np.asarray(s, dtype=float) for s in cs.allsegs[0] if len(s) >= 4]
    finally:
        plt.close(fig)
    if not segs:
        raise SystemExit("没有取出任何轮廓，检查取色阈值")
    return segs


def smooth_closed(points: np.ndarray, window: int = 5) -> np.ndarray:
    """环形滑动平均，抹掉栅格台阶。窗口取奇数，环绕取样保证接缝连续。"""
    if len(points) <= window or window < 3:
        return points
    n = len(points)
    half = window // 2
    idx = (np.arange(n)[:, None] + np.arange(-half, half + 1)[None, :]) % n
    return points[idx].mean(axis=1)


def simplify(points: np.ndarray, tolerance: float) -> np.ndarray:
    """Douglas-Peucker 简化（闭合曲线版，从离起点最远处起刀避免切掉接缝）。"""
    pts = points
    if len(pts) > 1 and np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    if len(pts) < 4:
        return pts

    start = int(np.argmax(np.linalg.norm(pts - pts[0], axis=1)))
    rolled = np.roll(pts, -start, axis=0)
    rolled = np.vstack([rolled, rolled[:1]])

    def dp(seg):
        if len(seg) < 3:
            return seg
        a, b = seg[0], seg[-1]
        ab = b - a
        nrm = np.linalg.norm(ab)
        dists = np.linalg.norm(seg - a, axis=1) if nrm == 0 else np.abs(np.cross(ab, seg - a)) / nrm
        i = int(np.argmax(dists))
        if dists[i] > tolerance:
            return np.vstack([dp(seg[: i + 1])[:-1], dp(seg[i:])])
        return np.array([a, b])

    out = dp(rolled)
    return out[:-1] if len(out) > 1 else out


def to_path(points: np.ndarray) -> str:
    """闭合 Catmull-Rom 转三次贝塞尔。"""
    n = len(points)
    if n < 3:
        return ""
    d = [f"M{points[0][0]:.2f} {points[0][1]:.2f}"]
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        prev, nxt = points[(i - 1) % n], points[(i + 2) % n]
        c1 = a + (b - prev) / 6.0
        c2 = b - (nxt - a) / 6.0
        d.append(f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {b[0]:.2f} {b[1]:.2f}")
    return "".join(d) + "Z"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="品牌稿 PNG（浅底 + 深绿字标）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fill", default="#1c1c1c", help="字标填充色")
    ap.add_argument("--tolerance", type=float, default=0.30, help="简化容差；越小越贴合，path 越长")
    ap.add_argument("--min-gap", type=int, default=12, help="标记与字标之间空白带的最小宽度（像素）")
    ap.add_argument("--alpha", type=float, default=0.25, help="轮廓平滑窗口（相对字高的比例）")
    ap.add_argument("--upscale", type=int, default=4, help="追踪前先放大的倍数")
    args = ap.parse_args()

    img = Image.open(args.src)
    # 字标在稿子里只有一百多像素高，栅格化产生的台阶会变成笔画上的抖动。
    # 先平滑放大再取轮廓，等于给曲线拟合更多采样点，比单纯加大平滑窗口好 ——
    # 后者会把 Y 与 A 的尖角一起磨圆。
    if args.upscale > 1:
        img = img.resize(
            (img.width * args.upscale, img.height * args.upscale), Image.LANCZOS
        )
    mask = text_mask(
        img,
        {"bg": (250, 248, 242), "ink": (0x1c, 0x1c, 0x1c)},
        args.min_gap * args.upscale,
    )

    ys, xs = np.where(mask)
    if len(ys) == 0:
        raise SystemExit("切出来的区域没有内容")
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    W, H = x1 - x0 + 1, y1 - y0 + 1
    scale = 100.0 / W

    segs = trace_all(mask)
    # 平滑窗口按字高取，避免不同分辨率的稿子表现不一致
    window = max(3, int(H * args.alpha) | 1)

    pieces = []
    stats = []
    for seg in segs:
        sm = smooth_closed(seg, window=window)
        simp = simplify(sm, args.tolerance)
        if len(simp) < 3:
            continue
        pts = np.stack([(simp[:, 0] - x0) * scale, (simp[:, 1] - y0) * scale], axis=1)
        pieces.append(to_path(pts))
        stats.append((len(seg), len(simp)))

    if not pieces:
        raise SystemExit("所有轮廓都被简化掉了，把 --tolerance 调小")

    d = "".join(pieces)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 {H * scale:.2f}"'
        f' fill="none" role="img" aria-label="Yet to Dawn">\n'
        f"  <title>Yet to Dawn</title>\n"
        # evenodd 是带孔字形的关键：孔是与外轮廓反向的独立子路径，
        # 默认的 nonzero 在方向一致时会把孔填实。
        f'  <path fill-rule="evenodd" fill="{args.fill}" d="{d}"/>\n'
        "</svg>\n"
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    io.open(args.out, "w", encoding="utf-8").write(svg)

    print(f"字标 {W}x{H} → viewBox 0 0 100 {H * scale:.2f}")
    print(f"  轮廓 {len(pieces)} 条（含字母内的孔），简化后共 {sum(s[1] for s in stats)} 点")
    print(f"  path {len(d)} 字符，平滑窗口 {window}")
    print(f"已写 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
