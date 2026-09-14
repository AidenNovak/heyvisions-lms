#!/usr/bin/env python3
"""从仓库内的品牌 SVG 生成界面用的位图。

为什么要脚本：这些都是位图，手改只能靠图像软件，改完没有记录、下次要换尺寸或
调色无从下手。这里把「取形 → 合成 → 导出」写成可重复执行的步骤。

**形状一律来自仓库内的 SVG**（`public/brand/yet-to-dawn-mark.svg` 与
`public/lrn-text.svg`），不再依赖 `~/Downloads` 里的品牌稿 —— 那两个 SVG 已是
从品牌稿描好的矢量源，本身就是事实源；位图从它们派生，链条才闭合。
渲染走 `svgkit.py`（仓库没有 cairosvg，为几张位图引渲染依赖不划算）。

多数目标文件**保留各自的底板**，只换里面的字形：底板的圆角、渐变、暗色都是
既有设计语言的一部分（`docs/heyvisions/design-tokens.md` 明确保留上游的紫蓝
渐变），重画底板等于顺手改设计。所以流程是「抠掉旧字形 → 补底 → 画新标记」。

沿用上游原有文件名（`learnhouse_*`）是刻意的：这些名字被 10+ 处引用，改名会
把日后 `git merge upstream/dev` 的冲突面放大（见 CHANGELOG 第 2 条）。

用法：
  python3 scripts/heyvisions/build-brand-pngs.py --dir apps/web/public
  python3 scripts/heyvisions/build-brand-pngs.py --dir apps/web/public --preview /tmp/brand.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import render_svg  # noqa: E402

# 与静态站一致的三色（见 docs/heyvisions/design-tokens.md）
PRIMARY = (0x14, 0x43, 0x38)      # 深林绿
SECONDARY = (0xA1, 0xB5, 0x9A)    # 鼠尾草
CREAM = (0xF4, 0xF0, 0xE7)
INK = (0x1C, 0x1C, 0x1C)          # 字标墨色，与 lrn-text.svg 一致
PLATE_DARK = (0x29, 0x2B, 0x2C)   # 上游 AI 图标的暗板实测色

MARK = "brand/yet-to-dawn-mark.svg"
WORDMARK = "lrn-text.svg"

# 深底上主帆用奶油、副帆用鼠尾草：品牌稿的深绿主帆放到深底上会整片消失
ON_DARK = {PRIMARY: CREAM, SECONDARY: SECONDARY}


def load(pub: Path, name: str) -> Image.Image:
    return Image.open(pub / name)


def mark_rgba(pub: Path, width: int, recolour=None, colour=None) -> np.ndarray:
    """按目标宽度渲染品牌标记（透明底 RGBA）。"""
    return render_svg(pub / MARK, width, recolour=recolour, colour=colour)


def wordmark_rgba(pub: Path, width: int, colour=None) -> np.ndarray:
    """按目标宽度渲染「YET TO DAWN」字标（透明底 RGBA）。"""
    return render_svg(pub / WORDMARK, width, colour=colour, supersample=3)


def paste(canvas: np.ndarray, art: np.ndarray, box: tuple[int, int]) -> np.ndarray:
    """
    把小图按 alpha 合成到画布上（source-over）。

    必须真做混合，不能直接拷 RGB：matplotlib 渲染出来的透明像素 RGB 是白色，
    直接拷会在深色底板上留一个白框（踩过）。画布带 alpha 时 alpha 也要一起合成。
    """
    out = canvas.astype(float).copy()
    x, y = box
    h, w = art.shape[:2]
    a = art[..., 3:4] / 255.0
    region = out[y : y + h, x : x + w]
    out[y : y + h, x : x + w, :3] = region[..., :3] * (1 - a) + art[..., :3] * a
    if out.shape[2] == 4:
        out[y : y + h, x : x + w, 3:4] = region[..., 3:4] * (1 - a) + art[..., 3:4] * a
    return out.round().astype(np.uint8)


def centred(total: int, size: int, offset: float = 0.0) -> int:
    """居中位置；offset 为相对尺寸的微调（光学对齐用）。"""
    return round((total - size) / 2 + offset)


def inpaint(arr: np.ndarray, mask: np.ndarray, radius: int = 2, iters: int = 6000,
            labels: np.ndarray | None = None, thr: float = 0.02) -> np.ndarray:
    """
    用周围像素把 mask 区域补掉（由边界向内迭代填充）。

    为什么要自己补：底板是渐变的（紫蓝渐变、暗色径向渐变），不能拿一个常数盖住，
    否则会看到一块补丁。

    labels 给出「分区」时，各分区独立填充，颜色不跨区扩散 —— 紫色板上有一条从
    左上到右下的硬边（深蓝底 / 亮紫圆），不分区的话补底会把这条边糊掉。

    两个参数是调出来的，都影响能否填满：
      - radius 用 2：核太大时，字形窄处（星芒的尖角）四周已知像素占比始终不够，
        填充推进不过去，会留白（实际踩过）
      - thr 用 0.02：阈值默认取「过半已知」同样会卡住宽字形内部
    """
    out = arr.astype(float).copy()
    k = 2 * radius + 1
    chan = out.shape[2]
    groups = [None] if labels is None else list(np.unique(labels))

    for lab in groups:
        subject = mask if lab is None else (mask & (labels == lab))
        known = (~subject).astype(float)
        if lab is not None:
            # 只在同区内扩散：区外的已知像素不参与，硬边因此得以保留
            known = ((labels == lab) & ~mask).astype(float)
        todo = subject.copy()
        for _ in range(iters):
            if not todo.any():
                break
            den = ndimage.uniform_filter(known, size=k)
            num = np.stack(
                [ndimage.uniform_filter(out[..., c] * known, size=k) for c in range(chan)],
                axis=-1,
            )
            filled = num / np.maximum(np.repeat(den[..., None], chan, axis=-1), 1e-6)
            ready = todo & (den > thr)
            out[ready] = filled[ready]
            known = known + ready.astype(float)
            todo = todo & ~ready
    return out.round().astype(np.uint8)


# --------------------------------------------------------------------------
# 各个产出
# --------------------------------------------------------------------------


def build_square_icon(pub: Path, size: int) -> Image.Image:
    """
    深绿圆角底 + 居中标记 —— 登录页、嵌入页、Stripe 回调用的方形图标。

    配色与静态站 favicon 刻意不同：favicon 用纸色底（要在浅色标签栏里跳出来），
    这里的图标是页面构图的一部分，跟随品牌稿的深绿底。
    """
    ss = 4
    big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1], radius=round(size * 0.17) * ss, fill=PRIMARY + (255,)
    )
    icon = np.asarray(big.resize((size, size), Image.LANCZOS)).copy()

    art = mark_rgba(pub, round(size * 0.66), recolour=ON_DARK)
    return Image.fromarray(paste(icon, art, (centred(size, art.shape[1]), centred(size, art.shape[0]))))


def build_lockup(pub: Path, size: tuple[int, int], dark: bool) -> Image.Image:
    """
    横版锁定：标记 + 字标，用于 `learnhouse_logo.png`（浅底）与
    `learnhouse_text_white.png`（深底）。

    宽度按上游同名文件的 972×252 出图，留白比例沿用品牌稿（内容占宽约 88%）。
    深底版整幅用奶油色：深底上两片帆若都用奶油会糊成一块，所以副帆压暗一档。
    """
    W, H = size
    if dark:
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = (0x20, 0x20, 0x20)
        ink = CREAM
    else:
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = (255, 255, 255)
        ink = PRIMARY

    pad = 0.06
    avail_w, avail_h = round(W * (1 - 2 * pad)), round(H * (1 - 2 * pad))

    # 标记高度决定整体高度；字标按同一高度对齐后并排
    mark = mark_rgba(pub, avail_h * 2)          # 先按高度上限渲染，再等比缩到位
    mark_scale = avail_h / mark.shape[0]
    mark = np.asarray(
        Image.fromarray(mark).resize(
            (max(1, round(mark.shape[1] * mark_scale)), avail_h), Image.LANCZOS
        )
    )

    gap = round(avail_h * 0.22)
    word_w = avail_w - mark.shape[1] - gap
    word = wordmark_rgba(pub, word_w, colour=ink)

    total_w = mark.shape[1] + gap + word.shape[1]
    if total_w > avail_w:                        # 字标顶到边就整体再缩一档
        s = avail_w / total_w
        mark = np.asarray(Image.fromarray(mark).resize(
            (max(1, round(mark.shape[1] * s)), max(1, round(mark.shape[0] * s))), Image.LANCZOS))
        word = np.asarray(Image.fromarray(word).resize(
            (max(1, round(word.shape[1] * s)), max(1, round(word.shape[0] * s))), Image.LANCZOS))
        total_w = mark.shape[1] + round(gap * s) + word.shape[1]
        gap = round(gap * s)

    x = centred(W, total_w)
    canvas = paste(canvas, mark, (x, centred(H, mark.shape[0])))
    canvas = paste(canvas, word, (x + mark.shape[1] + gap, centred(H, word.shape[0])))

    if dark:
        # 副帆（鼠尾草）压暗一档，避免两片帆在深底上糊成一块
        art = mark_rgba(pub, mark.shape[1], recolour=ON_DARK)
        art = np.asarray(Image.fromarray(art).resize((mark.shape[1], mark.shape[0]), Image.LANCZOS))
        sage = np.abs(art[..., :3].astype(int) - np.array(SECONDARY)).sum(axis=2) < 90
        region = canvas[centred(H, mark.shape[0]) : centred(H, mark.shape[0]) + mark.shape[0],
                        x : x + mark.shape[1]]
        region[sage & (art[..., 3] > 128)] = (region[sage & (art[..., 3] > 128)] * 0.72).astype(np.uint8)
    return Image.fromarray(canvas)


def build_black_logo(pub: Path) -> Image.Image:
    """
    `black_logo.png` —— 404 页用的横版标识（浅底页面上）。

    上游这张是纯文字「HeyVisions」。换成标记 + 字标，画布尺寸沿用上游的
    1732×320：`app/not-found.tsx` 按 width=270 / height=100 引用它。
    """
    W, H = 1732, 320
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    canvas[:] = (255, 255, 255)

    avail_w = round(W * 0.78)
    mark = mark_rgba(pub, round(H * 0.62))
    gap = round(H * 0.18)
    word = wordmark_rgba(pub, avail_w - mark.shape[1] - gap, colour=INK)

    total_w = mark.shape[1] + gap + word.shape[1]
    x = centred(W, total_w)
    canvas = paste(canvas, mark, (x, centred(H, mark.shape[0])))
    canvas = paste(canvas, word, (x + mark.shape[1] + gap, centred(H, word.shape[0])))
    return Image.fromarray(canvas)


def build_ai_black_logo(pub: Path) -> Image.Image:
    """
    `learnhouse_ai_black_logo.png` —— AI 对话头部的深色徽标。

    原图是暗板 + 白色「HV」+ 小号「AI」（332×160），四角留白。底板与圆角保留，
    只把 HV/AI 换成品牌标记：画布尺寸不变，引用处（`width={100}` / `width={80}`）
    的版式不走样。标记居中而不是留在左侧 —— 原图字形只占左边 55%，右侧是空白。
    """
    W, H = 332, 160
    radius = 12          # 原图四角留白是 12×12，即圆角半径

    # 先在 4 倍尺寸上画圆角板再缩回来，等于做了一次抗锯齿
    plate = Image.new("RGBA", (W * 4, H * 4), (255, 255, 255, 255))
    ImageDraw.Draw(plate).rounded_rectangle(
        [0, 0, W * 4 - 1, H * 4 - 1], radius=radius * 4, fill=PLATE_DARK + (255,)
    )
    canvas = np.asarray(plate.resize((W, H), Image.LANCZOS)).copy()

    art = mark_rgba(pub, round(H * 0.42), recolour=ON_DARK)
    canvas = paste(canvas, art, (centred(W, art.shape[1]), centred(H, art.shape[0])))
    return Image.fromarray(canvas[..., :3])


def build_ai_simple(pub: Path, size: int = 590) -> Image.Image:
    """
    `learnhouse_ai_simple.png` 与 `lrnai_icon.png`（两文件内容完全相同）——
    内联在编辑器 / 课程创建里的 AI 小图标。

    方案：暗色圆角盘 + 标记（与 favicon 同一套语言）。原图是上游标记的实心暗块，
    「深色块状图形」本来就是它在这些入口里的角色，圆角盘保留这个观感。

    为什么不直接双帆剪影铺满白底：这两张图标在界面上只有 14–24px，两片帆之间
    那道缝在那个尺度会糊成一块，看起来像污渍。实测四组方案（见 CHANGELOG），
    圆角盘 + 双帆在小尺寸下轮廓最清楚 —— 盘的边界提供了额外的形，帆的缝也还在。
    """
    ss = 4
    plate = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1], radius=round(size * 0.24) * ss, fill=PLATE_DARK + (255,)
    )
    canvas = plate.resize((size, size), Image.LANCZOS)
    art = mark_rgba(pub, round(size * 0.62), recolour=ON_DARK)
    canvas.alpha_composite(
        Image.fromarray(art), (centred(size, art.shape[1]), centred(size, art.shape[0]))
    )
    # 底色填白再转 RGB：原图就是白底，而直接 convert("RGB") 会把盘外的透明像素
    # 变成黑色，四角出现黑块（踩过）。
    flat = Image.new("RGB", (size, size), (255, 255, 255))
    flat.paste(canvas, (0, 0), canvas)
    return flat


def glyph_mask_white(arr: np.ndarray, thr: int = 165, dilate: int = 3) -> np.ndarray:
    """
    抠出彩色板上的白色字形（上游标记 + 星芒）。

    判据是**亮度阈值**，不用饱和度：亮紫角虽然比字形暗（143 vs 240），但字形的
    边缘像素饱和度会升到 50-60，用「低饱和」当条件会把边缘留下，补完就出现一圈
    淡色轮廓（实际踩过，比多抠一点难看得多）。纯亮度阈值在 165 以上时只命中字形。
    """
    lum = arr[..., :3].astype(int).mean(axis=2)
    solid = arr[..., 3] > 200
    return ndimage.binary_dilation((lum > thr) & solid, iterations=dilate)


def plate_regions(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    把板上的像素分成两区（1 = 亮紫圆，2 = 深蓝底），字形区按最近区域归属。

    紫色板的右下是一片亮紫圆、其余是深蓝底，两者之间是硬边。补底必须分区做，
    否则卷积会把这条边糊成渐变。
    """
    rgb = arr[..., :3].astype(int)
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    solid = arr[..., 3] > 200

    seed = np.zeros(lum.shape, dtype=np.uint8)
    seed[(sat > 110) & (lum > 110) & solid & ~mask] = 1     # 亮紫圆
    seed[solid & ~mask & (seed == 0)] = 2                   # 深蓝底
    # 字形区（seed==0）按最近的非零标签归属
    _, idx = ndimage.distance_transform_edt(seed == 0, return_indices=True)
    return seed[tuple(idx)]


def build_tinted_plate(pub: Path, src: Image.Image, art_width_ratio: float,
                       out_size: tuple[int, int] | None = None) -> Image.Image:
    """
    紫色渐变 AI 图标（`learnhouse_ai_simple_colored.png`、`ai_avatar.png`）：
    保留渐变底板，把原来的上游字形换成品牌标记。

    渐变底是上游 AI 的口径，`docs/heyvisions/design-tokens.md` 明确保留
    （「这是取舍，不是遗漏」），所以只动字形。底板没有解析式（是网格渐变），
    只能从原图把字形抠掉再补底 —— 见 `glyph_mask_white` / `plate_regions` /
    `inpaint`。

    这两张图在界面上的实际尺寸只有 28px 与 35px，补底留下的极淡痕迹在这个
    尺度下不可见；按显示尺寸放大核对过（`--preview` 会一并出对照）。
    """
    a = np.asarray(src.convert("RGBA")).copy()
    glyph = glyph_mask_white(a)
    labels = plate_regions(a, glyph)
    # 只补字形，alpha 一起补（字形处本来就在不透明的板内），板外的透明保持不动
    filled = inpaint(a, glyph, labels=labels)

    W, H = out_size or (src.width, src.height)
    art = mark_rgba(pub, round(W * art_width_ratio), recolour=ON_DARK)
    out = paste(filled, art, (centred(W, art.shape[1]), centred(H, art.shape[0])))
    return Image.fromarray(out)


def build_empty_thumbnail(pub: Path) -> Image.Image:
    """
    `empty_thumbnail.png` —— 课程/播客缩略图的兜底图，出现频率很高。

    原图是暗色径向渐变 + 中央一个圆角方框水印，框内是上游字形的「1」。
    这里只换框内的字形：圆角方框本身没有品牌含义，保留它能省掉重画渐变，
    也保证尺寸与引用处（多处 backgroundImage）完全一致。
    """
    src = load(pub, "empty_thumbnail.png").convert("RGB")
    a = np.asarray(src).copy()

    # 「1」的精确范围（实测）：x[407-440] y[164-256]
    glyph = np.zeros(a.shape[:2], dtype=bool)
    glyph[164:257, 407:441] = True
    # 多留 2px 抗锯齿边
    glyph = ndimage.binary_dilation(glyph, iterations=2)

    filled = inpaint(a, glyph, radius=4)

    # 水印的对比度：原图字形比周围亮约 15-25，新标记沿用同一档
    lum = filled.astype(int).mean(axis=2)
    base = float(np.median(lum[164:257, 380:470]))
    art = mark_rgba(pub, 104, colour=(255, 255, 255))
    target = min(255.0, base + 22)
    art = art.astype(float)
    art[..., :3] *= target / 255.0
    art[..., 3] = art[..., 3] * 0.9
    out = paste(filled, np.clip(art, 0, 255).astype(np.uint8), (centred(845, 104), centred(427, art.shape[0])))
    return Image.fromarray(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True, help="apps/web/public 的路径")
    ap.add_argument("--preview", help="可选：拼一张对照图便于目视核对")
    args = ap.parse_args()

    pub = Path(args.dir)
    if not (pub / MARK).exists():
        raise SystemExit(f"--dir 下找不到品牌 SVG: {pub / MARK}")

    written: list[str] = []

    def save(img: Image.Image, name: str) -> None:
        img.save(pub / name)
        written.append(f"{name} {img.width}x{img.height}")

    # 1) 方形图标：1180² 与 590²
    big = build_square_icon(pub, 1180)
    for name in ("learnhouse_bigicon.png", "learnhouse_bigicon_1.png"):
        save(big, name)
    save(build_square_icon(pub, 590), "learnhouse_icon.png")

    # 2) 横版锁定（浅底 / 深底）
    save(build_lockup(pub, (972, 252), dark=False), "learnhouse_logo.png")
    save(build_lockup(pub, (972, 252), dark=True), "learnhouse_text_white.png")

    # 3) 404 页的横版标识
    save(build_black_logo(pub), "black_logo.png")

    # 4) AI 徽标与内联图标
    save(build_ai_black_logo(pub), "learnhouse_ai_black_logo.png")
    simple = build_ai_simple(pub)
    save(simple, "learnhouse_ai_simple.png")
    save(simple, "lrnai_icon.png")

    # 5) 紫色渐变的 AI 图标：保留底板，只换字形
    save(build_tinted_plate(pub, load(pub, "learnhouse_ai_simple_colored.png"), 0.62),
         "learnhouse_ai_simple_colored.png")
    save(build_tinted_plate(pub, load(pub, "ai_avatar.png"), 0.62), "ai_avatar.png")

    # 6) 缩略图兜底图
    save(build_empty_thumbnail(pub), "empty_thumbnail.png")

    # 7) 侧边栏方标（dashLogo）——当前代码里没有引用（上游遗留，git 里能查到），
    #    但文件名是「面板方标」，一并换成品牌标记，免得日后有人启用时拿到上游标。
    save(build_ai_simple(pub, 96), "dashLogo.png")

    for line in written:
        print("  已写", line)

    if args.preview:
        names = [l.split()[0] for l in written]
        tiles = []
        for n in names:
            im = Image.open(pub / n).convert("RGBA")
            im.thumbnail((190, 190), Image.LANCZOS)
            t = Image.new("RGBA", (200, 200), (250, 250, 250, 255))
            t.alpha_composite(im, ((200 - im.width) // 2, (200 - im.height) // 2))
            tiles.append(t)
        cols = 5
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (200 * cols, 200 * rows), (255, 255, 255))
        for i, t in enumerate(tiles):
            sheet.paste(t.convert("RGB"), ((i % cols) * 200, (i // cols) * 200))
        Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.preview)
        print("  对照图", args.preview)
        print("  顺序:", " | ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
