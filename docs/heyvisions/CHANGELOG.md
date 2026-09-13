# 改动记录

本仓库相对上游 [`learnhouse/learnhouse`](https://github.com/learnhouse/learnhouse) 的所有改动。
每条对应一个 issue 和一个 PR，用来快速回答「我们和上游差在哪」。

基线：fork 于 `upstream/dev` @ `2841620b`。

## 汇总

| # | 改动 | Issue | PR | 触及上游文件 |
| --- | --- | --- | --- | --- |
| 1 | fork 维护流程与改动记录 | [#1](https://github.com/AidenNovak/heyvisions-lms/issues/1) | [#2](https://github.com/AidenNovak/heyvisions-lms/pull/2) | `README.md`（仅顶部加 fork 声明） |
| 2 | 品牌标识白标：LearnHouse → HeyVisions | [#3](https://github.com/AidenNovak/heyvisions-lms/issues/3) | [#8](https://github.com/AidenNovak/heyvisions-lms/pull/8)、[#11](https://github.com/AidenNovak/heyvisions-lms/pull/11) | `lrn.svg`、`lrn-text.svg`、`lrn-dash.svg`、各尺寸 PNG、`locales/*.json` |
| 3 | 移除上游水印与推广位 | [#5](https://github.com/AidenNovak/heyvisions-lms/issues/5) | [#9](https://github.com/AidenNovak/heyvisions-lms/pull/9) | `Watermark.tsx`、`LegalFooters.tsx`、`home.tsx`、orgs layout |
| 4 | 课程内容导入脚本入库 | [#7](https://github.com/AidenNovak/heyvisions-lms/issues/7) | [#10](https://github.com/AidenNovak/heyvisions-lms/pull/10) | 无（纯新增目录） |
| 5 | 简体中文设为默认语言并核对 zh 文案 | [#6](https://github.com/AidenNovak/heyvisions-lms/issues/6) | [#13](https://github.com/AidenNovak/heyvisions-lms/pull/13) | `organization_config.py`、`locales/*.json`（22 个语言文件） |

## 1. fork 维护流程与改动记录

- **改什么**：建立本 fork 的改动留痕机制——issue 模板、维护流程文档、本改动记录。
- **为什么**：fork 会持续偏离上游，需要能逐条追溯每处改动的原因与范围，
  也便于日后 `git merge upstream/dev` 时判断冲突该保留哪一边。
- **影响范围**：新增 `.github/ISSUE_TEMPLATE/upstream-change.yml`、
  `docs/heyvisions/CONTRIBUTING-FORK.md`、`docs/heyvisions/CHANGELOG.md`；
  `README.md` 顶部加 fork 声明。
- **与上游的关系**：纯本地维护文档，不回馈上游。`README.md` 顶部声明会在同步时产生小冲突，
  固定保留本仓库版本即可。

## 2. 品牌标识白标：LearnHouse → HeyVisions

- **改什么**：平台的上游品牌替换为 HeyVisions。新增 `services/config/brand.ts` 作为
  品牌名与法律链接的唯一事实源（默认值即 HeyVisions）；新增 `public/hv/` 存放品牌源文件；
  替换 `lrn.svg`/`lrn-text.svg`/`lrn-dash.svg`/favicon 及各尺寸 PNG 的内容；
  locale 里的 `copyright`/`powered_by` 不再写死上游品牌；`OrgMenu` 的 logo `alt` 改从配置取。
- **为什么**：对外交付的平台上出现第三方品牌是 bug，不是 fallback。
- **影响范围**：`apps/web/services/config/brand.ts`（新增）、`apps/web/public/hv/`（新增）、
  若干上游品牌资源（只换内容，沿用文件名）、`apps/web/locales/*.json`。
- **与上游的关系**：`lrn.svg`/`lrn-text.svg` 是上游界面里被引用最多的品牌资源（10+ 处），
  **沿用文件名**把同步冲突压到最小；同步时若上游更新了这两个文件的**内容**，固定保留本仓库版本。

## 3. 移除上游水印与推广位

- **改什么**：右下角固定水印、组织页脚水印、首页 "Powered by"、页脚指向 learnhouse.io 的
  条款/隐私链接，都改为受品牌配置控制并默认关闭。
- **为什么**：水印在 OSS 模式下默认展示（`usePlan()` 返回 `'oss'`，
  判断落到 `watermarkConfig !== false`，而组织配置里 `watermark` 默认 `True`）。
  条款链接指向别家公司是错的——HeyVisions 的服务条款与上游不是同一份。
- **影响范围**：`components/Objects/Watermark.tsx`、`components/Footers/LegalFooters.tsx`、
  `app/home/home.tsx`、`app/orgs/[orgslug]/(withmenu)/layout.tsx`。
- **与上游的关系**：都是上游文件，同步时会有冲突；改动频率低，冲突可控。
  水印保留组件与开关（`NEXT_PUBLIC_BRAND_WATERMARK=true` 打开），打开时显示**真正的上游标识**
  （`public/upstream/`）——署名第三方却用自家 logo 是错的。

## 4. 课程内容导入脚本入库

- **改什么**：把课程导入从一次性快照目录搬进本仓库，做成可复现、可重复执行的脚本；
  连同本地/服务器启动脚本与文档一起入库。
- **为什么**：内容导入此前依赖本机路径、不可复现，是验证「内容 → 章节 → 单元 → 进度」
  链路的最小数据集。
- **影响范围**：新增 `scripts/heyvisions/`（导入、静态服务、启动、locale 工具）、
  `docs/heyvisions/LOCAL-SETUP.md`。
- **与上游的关系**：纯新增目录，不触及上游文件。

## 5. 简体中文设为默认语言并核对 zh 文案

- **改什么**：新组织的 `default_language` 默认值改为 `zh`；补齐 zh 缺失的 141 个界面键；
  把 locale 里**指代本平台自身**的品牌名变量化为 `{{brand}}`（22 个语言文件，113 处），
  由组件传入 `getBrandName()`。
- **为什么**：课程正文是中文，界面是英文会有语言摩擦。品牌名硬编码在 22 个 locale 里
  无法维护——换品牌名必漏改。
- **影响范围**：`apps/api/src/db/organization_config.py`（一行）、`apps/web/locales/*.json`
  （22 个文件）、以及传入 `brand` 变量的组件。
- **与上游的关系**：`default_language` 默认值一行，冲突面极小。locale 文件的策略是
  **只补缺失键与品牌相关内容，其余保持上游原文**，便于后续 merge；`{{brand}}` 变量化
  会与上游的翻译更新冲突，但冲突是机械的（保留本仓库版本即可）。
- **未覆盖**：`courses.import.*`、`dashboard.*.watermark*` 等字符串里的 LearnHouse 指的是
  **真实存在的第三方**（导入上游导出包、上游水印），替换成变量是错的，属于另一个决定。

## 待办

| Issue | 内容 |
| --- | --- |
| [#4](https://github.com/AidenNovak/heyvisions-lms/issues/4) | 主题白标：字体与主色对齐 heyvisions.com |
| [#12](https://github.com/AidenNovak/heyvisions-lms/issues/12) | 事务性邮件文案白标（84 处 `LearnHouse`） |
| — | 上游导入/水印相关文案的取舍（见第 5 条的「未覆盖」） |
| — | CF 上 faka/kb/usdt/status/sapi 等死子域记录待清理（与 LMS 无关，工作区遗留项） |

## 上游同步

| 日期 | 上游 commit | 结果 |
| --- | --- | --- |
| — | （尚未同步） | 基线 `2841620b` |
