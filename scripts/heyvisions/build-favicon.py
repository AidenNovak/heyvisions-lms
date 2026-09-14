#!/usr/bin/env python3
"""从品牌稿生成 favicon.ico。

为什么要脚本：favicon 是纯位图，手改只能靠图像软件，改完没有记录、
下次有人要换尺寸或调色无从下手。这里把「从品牌稿取形 → 合成 → 导出多尺寸」
写成可重复执行的步骤。

形状从品牌稿直接取（深绿底 + 奶油/鼠尾草两片帆），不依赖 SVG 渲染器：
仓库里没有 cairosvg，为了一张 16px 的图标去引渲染依赖不划算。
取色与轮廓的思路与 `scripts/heyvisions/fit-wordmark.py` 一致。

用法：
  python3 scripts/heyvisions/build-favicon.py --src "<品牌稿 PNG>" --out apps/web/public/favicon.ico
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


# 与静态站一致的三色（见 docs/heyvisions/design-tokens.md）
PAPER = (0xFA, 0xF8, 0xF2)   # 纸色，图标底
PRIMARY = (0x14, 0x43, 0x38)  # 深林绿，主帆
SECONDARY = (0xA1, 0xB5, 0x9A)  # 鼠尾草，副帆
SOURCE_BG = (0x15, 0x43, 0x39)  # 品牌稿的深绿底（实测值，与 PRIMARY 极近）

# Windows/浏览器会按需取用；16 是任务栏与标签页的最小场景，必须单独好看
SIZES = (16, 32, 48, 64, 128, 256)


def extract_mark(src: Path) -> tuple[Image.Image, Image.Image]:
    """
    从品牌稿切出两片帆，返回两张**与原图同尺寸**的透明底单色图。

    保持原尺寸、不各自裁到外接框：两片帆要按同一坐标系叠放，
    各自裁剪后会丢失相对位置，合成时右帆会跑到左帆上面。
    偏移在调用方按整体外接框统一计算。

    分两步：先划出「整体标记」范围（离底色足够远），再在其中按最近邻
    区分主帆与副帆。不能直接按颜色阈值分 —— 抗锯齿边缘是前景与深绿底的
    混合，色值会落在两片帆之间，直接分类会把边缘判给副帆。
    """
    img = Image.open(src).convert("RGB")
    a = np.asarray(img).astype(int)

    bg = np.array(SOURCE_BG)
    primary = np.array([0xF4, 0xF0, 0xE7])   # 稿里的奶油色，比 PAPER 略冷
    secondary = np.array(SECONDARY)

    # 离底色足够远 = 属于标记
    mark = np.abs(a - bg).sum(axis=2) > 150

    dists = np.stack([
        np.abs(a - primary).sum(axis=2),
        np.abs(a - secondary).sum(axis=2),
    ])
    nearest = np.argmin(dists, axis=0)

    out = []
    for i in range(2):
        m = (nearest == i) & mark
        if not m.any():
            raise SystemExit(f"第 {i} 片帆没取到，检查取色")
        rgba = np.zeros((a.shape[0], a.shape[1], 4), dtype=np.uint8)
        rgba[..., :3] = PRIMARY if i == 0 else SECONDARY
        rgba[..., 3] = np.where(m, 255, 0).astype(np.uint8)
        out.append(Image.fromarray(rgba, "RGBA"))
    return out[0], out[1]


def mark_bounds(src: Path) -> tuple[int, int, int, int]:
    """整体标记（两片帆合并）在品牌稿里的外接框，作为统一坐标系。"""
    img = Image.open(src).convert("RGB")
    a = np.asarray(img).astype(int)
    mark = np.abs(a - np.array(SOURCE_BG)).sum(axis=2) > 150
    ys, xs = np.where(mark)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def rounded_square(size: int, radius_ratio: float, bg: tuple[int, int, int]) -> Image.Image:
    """
    画圆角方形底。

    用 4 倍超采样再缩回来：PIL 的圆角是直接栅格化的，小尺寸下边缘会有
    明显锯齿（16px 尤其糟），先画大再缩相当于做了抗锯齿。
    """
    ss = 4
    big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    r = int(size * ss * radius_ratio)
    d.rounded_rectangle([0, 0, size * ss - 1, size * ss - 1], radius=r, fill=bg + (255,))
    return big.resize((size, size), Image.LANCZOS)


def build_icon(src: Path, size: int, primary: Image.Image, secondary: Image.Image, bounds) -> Image.Image:
    """合出一个尺寸的图标：纸色圆角底 + 居中留白的两片帆。"""
    x0, y0, x1, y1 = bounds
    mw, mh = x1 - x0, y1 - y0

    base = rounded_square(size, 0.22, PAPER)

    # 留白：标记占画布宽度约 68%，与静态站 favicon 的比例一致
    inner = size * 0.68
    scale = inner / mw
    draw_w, draw_h = max(1, round(mw * scale)), max(1, round(mh * scale))

    # 两片帆已在同一坐标系里，先叠到整体外接框大小，再一起缩放
    full = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    full.alpha_composite(primary, (-x0, -y0))
    full.alpha_composite(secondary, (-x0, -y0))
    full = full.resize((draw_w, draw_h), Image.LANCZOS)

    base.alpha_composite(full, ((size - draw_w) // 2, (size - draw_h) // 2))
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="品牌稿 PNG（深绿底 + 奶油/鼠尾草两片帆）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", help="可选：同时导出一张 128px PNG 便于目视核对")
    args = ap.parse_args()

    src = Path(args.src)
    bounds = mark_bounds(src)
    primary, secondary = extract_mark(src)

    frames = [build_icon(src, s, primary, secondary, bounds) for s in SIZES]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # PIL 的 ICO 保存：首帧决定默认尺寸，其余尺寸由 sizes 参数生成
    frames[-1].save(out, format="ICO", sizes=[(s, s) for s in SIZES])

    print(f"标记外接框 {bounds[2]-bounds[0]}x{bounds[3]-bounds[1]}")
    print(f"已写 {out}（{', '.join(str(s) for s in SIZES)} px，{out.stat().st_size // 1024} KB）")

    if args.preview:
        p = Path(args.preview)
        p.parent.mkdir(parents=True, exist_ok=True)
        frames[SIZES.index(128)].save(p)
        print(f"预览已写 {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
