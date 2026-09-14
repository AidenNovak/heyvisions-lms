# 学习平台视觉：与静态站对齐

本文件记录 LMS 与 `heyvisions.com` 共享的视觉令牌，以及 LMS 侧的实现位置。
静态站的设计规范在 website 仓库：`docs/heyvisions/learning-platform-design.md`。

跟踪 issue：[#4](https://github.com/AidenNovak/heyvisions-lms/issues/4)

## 为什么需要这份对照

两处是同一个产品的两个面（内容面 / 帐号与进度面），从静态站跳到学习平台不应
像换了一个产品。具体做法是**共用同一套令牌**，而不是各调各的。

## 令牌对照

| 项 | 静态站 | LMS | LMS 实现位置 |
| --- | --- | --- | --- |
| 西文字体 | `Geist`（自托管 woff2） | `Geist`（`next/font/google`） | `app/layout.tsx` |
| 中文回退 | `PingFang SC` → `Hiragino Sans GB` → `Microsoft YaHei` | 同 | `styles/globals.css` 的 `font-family` |
| 焦点环（浅色） | `--ring: #144338`（深林绿，对纸色 10.11:1） | `--ring: 166.0 54.0% 17.1%` | `styles/globals.css` `:root` |
| 焦点环（深色） | 深色方向仍是预览态，未与品牌稿对齐 | `--ring: 155.2 19.0% 52.5%`（同色系浅绿 `#6f9d8a`） | `styles/globals.css` `.dark` |
| 卡片投影 | `--shadow-card: 0 1px 2px rgba(0,0,0,.04)` | `.nice-shadow` = 同值 | `styles/globals.css` utilities |
| 卡片圆角 | `--r-sm: 10px`（最常用） | `--radius: 0.625rem`（=10px，`rounded-lg` 用的是它） | `styles/globals.css` `:root` |
| 背景 / 正文 / 次级 | `#ffffff` / `#1c1c1c` / `#71717a` | `0 0% 100%` / `0 0% 3.9%` / `0 0% 45.1%` | 上游原值，未改 |
| 深色背景 / 正文 | `#0f0f13` / `#f5f5f6` | 上游原值（`10,10,10` / `250,250,250`） | 未改 |

HSL 值由十六进制换算而来（`hsl(var(--ring))` 的写法要求空格分隔、不带单位）。
焦点环令牌在 `40294c21` 由暖橙换成品牌深林绿（浅色 `#c2410c` → `#144338`，
深色 `#d86f3d` → `#6f9d8a`），本表随之同步。

## 深色模式：平台没有真正的深色模式

这一点在验收时要先说清楚，免得把「深色下不一致」当成回归：

- 上游就有 **1346 处硬编码 `bg-white`**，而 `dark:` 变体只有 181 处
- 平台上没有主题切换开关，`.dark` 只在 embed 路由等少数场景被设置
- 深色模式下卡片仍是白底，是上游的既有状态

所以 `.dark` 下的 `--ring` 用了同色系的浅绿 `#6f9d8a`（深绿 `#144338` 在 `.dark` 的
近黑底 `#0a0a0a` 上只有 1.78:1，必须亮一档），
但**不声称深色模式与静态站观感一致** —— 那是要另开工的事，成本在逐个组件替换
`bg-white`，与本 issue 的「对齐令牌」不是同一件事。

## 三个设计决定

**1. 品牌色只用于焦点环**

静态站的规则是「单一强调色，其余锌灰」，品牌绿出现在链接、`--ring` 与少量标记上，
按钮本身是黑/白中性色。LMS 的上游默认是同样的中性按钮（`bg-black`、
`bg-gray-900`），所以只把 `--ring` 换成品牌深林绿即可对齐观感，不必逐个组件换色。
这也把改动面压到 2 行——上游改版时不易被覆盖。

**2. 层次靠边线，不靠投影**

上游的 `.nice-shadow` 是 `shadow-md`（4–6px 扩散），卡片浮在页面之上；
静态站是「发丝线 + 1px 投影」，卡片与页面同层。改 `.nice-shadow` 与
`.light-shadow` 两条规则即覆盖全站 700+ 处使用，不必逐个改组件。

**3. 中文字族必须写在 `var()` 之外**

```css
/* 错：--font-default 由 next/font 注入且一定有值，var() 的 fallback 永不生效 */
font-family: var(--font-default, 'Geist', 'PingFang SC', ...);

/* 对：中文字族在 var() 之后，Geist 缺字时接管 */
font-family: var(--font-default, 'Geist'), 'PingFang SC', ...;
```

写在 `var()` 的 fallback 位置的字族是**死代码**。上游原本就是这样写的
（`var(--font-default, 'Wix Madefor Text'), -apple-system, ...`），
中文只能靠浏览器默认兜底，在 Windows/Linux 上会落到与静态站不同的字面。

## 没改的部分

- **上游语气的渐变与彩色**：`teal-*`（23 个文件）、`indigo/violet/purple`（669 处）
  仍在。这些多用于管理员后台与编辑器，学习者主路径（课程列表、课时阅读）不涉及。
  全量替换工作量大且会大面积冲突，判断为不值得——**这是取舍，不是遗漏**。
- **`--radius-xl` 等未定义的档位**：Tailwind 默认值仍然生效，未强行统一。
- 深色的背景/正文沿用上游值：`#0f0f13` 与 `10,10,10` 观感接近，
  改它会影响全部深色界面，收益不足。

## 复核方式

```bash
# 字体族含 Geist 与中文字体，且不含 Wix Madefor
curl -s http://127.0.0.1:3011/ | grep -o "Wix Madefor"   # → 空

# 计算样式（在浏览器控制台）
getComputedStyle(document.body).fontFamily
getComputedStyle(document.documentElement).getPropertyValue('--ring')   // → 166.0 54.0% 17.1%
getComputedStyle(document.querySelector('.nice-shadow')).boxShadow
  // → 末段为 0px 1px 2px 0px rgba(0,0,0,0.04)
```

对比度（WCAG AA）：

| 组合 | 比值 | 要求 |
| --- | --- | --- |
| `#144338` 焦点环 / 白底 | 11.11:1 | UI 组件 ≥3:1 |
| `#6f9d8a` 焦点环 / `#0a0a0a`（`.dark` 的 `--background`） | 6.47:1 | ≥3:1 |
| `#1c1c1c` 正文 / 白底 | 17.04:1 | 正文 ≥4.5:1 |
| `#71717a` 次级 / 白底 | 4.83:1 | ≥4.5:1 |
| `#a9a9af` 次级 / 深色底 | 8.18:1 | ≥4.5:1 |
