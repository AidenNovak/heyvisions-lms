# 上游品牌资源（仅用于合规署名）

这里保存 LearnHouse 的原始品牌标识，**只在一处使用**：当
`NEXT_PUBLIC_BRAND_WATERMARK=true` 打开上游署名水印时，水印应显示真正的
LearnHouse 标识，而不是 Yet to Dawn 的标识。

其余所有界面位置都用 Yet to Dawn 的自有资源：

| 用途 | 资源 |
| --- | --- |
| 应用内标识（导航、首页、编辑器、看板） | `public/lrn.svg` · `public/lrn-dash.svg` |
| 字标 | `public/lrn-text.svg`（由 `scripts/heyvisions/fit-wordmark.py` 从品牌稿生成） |
| 品牌源文件（SVG） | `public/brand/` |

上游项目：<https://github.com/learnhouse/learnhouse>（AGPL-3.0）
