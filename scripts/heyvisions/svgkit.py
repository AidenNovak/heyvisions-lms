"""把品牌 SVG（只含 M/C/Z 的填充路径）光栅化成 RGBA 数组。

为什么要自己写：仓库里没有 cairosvg，而这几张图标的形状、颜色、尺寸都要按
位置微调。与其为一次性的位图去引渲染依赖，不如直接解析路径 —— 品牌 SVG 是
从品牌稿描出来的纯三次贝塞尔填充，命令只用 M/C/Z，解析器不到 40 行。

坐标系：SVG 的 y 轴向下，matplotlib 的 y 轴向上，画完把不到 1 的 ylim 反转过来。
"""
from __future__ import annotations

import re

import matplotlib
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

matplotlib.use("Agg")

# 命令参数个数（仅支持品牌 SVG 实际用到的三种）
_ARITY = {"M": 2, "C": 6, "Z": 0}


def _tokenize(d: str) -> list[str]:
    """把路径字符串切成 命令 + 数字 的记号流。"""
    return re.findall(r"[MCZ]|-?\d*\.?\d+(?:[eE]-?\d+)?", d.replace(",", " "))


def _parse(d: str) -> tuple[np.ndarray, np.ndarray]:
    """解析成 matplotlib 的 (vertices, codes)。"""
    toks = _tokenize(d)
    verts: list[tuple[float, float]] = []
    codes: list[int] = []
    i = 0
    cmd = None
    start = (0.0, 0.0)
    while i < len(toks):
        if toks[i] in _ARITY:
            cmd = toks[i].upper()
            i += 1
            if cmd == "Z":
                verts.append(start)
                codes.append(MplPath.CLOSEPOLY)
                continue
        n = _ARITY[cmd]
        vals = [float(v) for v in toks[i : i + n]]
        i += n
        if cmd == "M":
            start = (vals[0], vals[1])
            verts.append(start)
            codes.append(MplPath.MOVETO)
        elif cmd == "C":
            verts.extend([(vals[0], vals[1]), (vals[2], vals[3]), (vals[4], vals[5])])
            codes.extend([MplPath.CURVE4] * 3)
    return np.array(verts, dtype=float), np.array(codes, dtype=np.uint8)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def svg_paths(svg_path) -> tuple[list[tuple[MplPath, tuple[int, int, int]]], tuple[float, float, float, float]]:
    """读出 SVG 里的每条填充路径（连同它的填色）与 viewBox。"""
    text = open(svg_path, encoding="utf-8").read()
    vb = re.search(r'viewBox="([\d.\-\s]+)"', text)
    if not vb:
        raise SystemExit(f"{svg_path} 里没有 viewBox")
    x0, y0, w, h = (float(v) for v in vb.group(1).split())

    paths = []
    for m in re.finditer(r"<path\b([^>]*)/?>", text):
        attrs = m.group(1)
        d = re.search(r'\sd="([^"]+)"', attrs)
        if not d:
            continue
        fill = re.search(r'fill="([^"]+)"', attrs)
        fill_val = fill.group(1).strip() if fill else "none"
        if fill_val.lower() == "none":
            continue
        verts, codes = _parse(d.group(1))
        paths.append((MplPath(verts, codes), _hex_to_rgb(fill_val) if fill_val.startswith("#") else (0, 0, 0)))
    if not paths:
        raise SystemExit(f"{svg_path} 里没有可填充的路径")
    return paths, (x0, y0, w, h)


def render_svg(svg_path, width: int, recolour: dict[tuple[int, int, int], tuple[int, int, int]] | None = None,
               colour: tuple[int, int, int] | None = None, supersample: int = 4) -> np.ndarray:
    """
    把 SVG 渲染成 (H, W, 4) 的 RGBA 数组，返回**透明底**。

    width 是目标宽度，高度按 viewBox 比例推出。supersample 倍渲染后再均值缩小，
    相当于抗锯齿（matplotlib 自己也有，但小尺寸下叠加一次更干净）。

    填色三选一，按需用：
      - 都不给：沿用 SVG 里写的颜色（品牌标准色）
      - `recolour`：按原色做替换，如 {(20,67,56): 奶油} —— 只换指定颜色，其余保留
      - `colour`：把每条路径都刷成同一色（单色版用）

    按原色替换比按下标指定更稳：SVG 里两条路径的先后顺序变了也不会把帆的颜色弄反。
    """
    paths, (vx, vy, vw, vh) = svg_paths(svg_path)
    H = max(1, round(width * vh / vw))
    W = width

    W2, H2 = W * supersample, H * supersample
    fig = Figure(figsize=(W2 / 100, H2 / 100), dpi=100)
    canvas = FigureCanvasAgg(fig)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(vx, vx + vw)
    ax.set_ylim(vy + vh, vy)     # 反转 y：SVG 的 y 向下

    for p, native in paths:
        if colour is not None:
            use = colour
        elif recolour and native in recolour:
            use = recolour[native]
        else:
            use = native
        ax.add_patch(PathPatch(p, facecolor=tuple(c / 255 for c in use),
                               edgecolor="none", antialiased=True))

    fig.canvas.draw()
    buf = np.asarray(canvas.buffer_rgba()).copy()
    fig.clear()

    # matplotlib 会把画布尺寸取整到整数像素，实际缓冲区可能比 W2/H2 略大或略小。
    # 先裁到 W2×H2（不够就补边），否则 reshape 会因元素数不匹配而失败。
    bh, bw = buf.shape[:2]
    if (bh, bw) != (H2, W2):
        fixed = np.zeros((H2, W2, buf.shape[2]), dtype=buf.dtype)
        fixed[: min(bh, H2), : min(bw, W2)] = buf[: min(bh, H2), : min(bw, W2)]
        buf = fixed

    # 均值缩小 = 抗锯齿
    buf = buf.reshape(H, supersample, W, supersample, 4).mean(axis=(1, 3))
    return buf.round().astype(np.uint8)
