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
| 6 | 视觉令牌对齐 heyvisions.com | [#4](https://github.com/AidenNovak/heyvisions-lms/issues/4) | [#14](https://github.com/AidenNovak/heyvisions-lms/pull/14) | `app/layout.tsx`、`lib/fonts.ts`、`styles/globals.css` |
| 7 | 品牌改名：HeyVisions → Yet to Dawn | [#15](https://github.com/AidenNovak/heyvisions-lms/issues/15) | [#16](https://github.com/AidenNovak/heyvisions-lms/pull/16) | `services/config/brand.ts`、`lrn-text.svg`、`locales/zh.json`、`public/hv/`（删除） |
| 8 | 品牌残留清扫：图片、界面文案、域名与邮件 | [#15](https://github.com/AidenNovak/heyvisions-lms/issues/15) | [#16](https://github.com/AidenNovak/heyvisions-lms/pull/16) | 见下方第 8 条 |
| 9 | 品牌残留清扫（续）：API 侧与构建产物 | [#15](https://github.com/AidenNovak/heyvisions-lms/issues/15) | [#16](https://github.com/AidenNovak/heyvisions-lms/pull/16) | 见下方第 9 条 |
| 10 | 生产上线：单主机名 HTTPS 部署与联调修出的四处缺陷 | [#17](https://github.com/AidenNovak/heyvisions-lms/issues/17) | [#18](https://github.com/AidenNovak/heyvisions-lms/pull/18) | 见下方第 10 条 |
| 11 | 单元正文的模板缺口：同步时生成平台专用副本 | [#19](https://github.com/AidenNovak/heyvisions-lms/issues/19) | [#20](https://github.com/AidenNovak/heyvisions-lms/pull/20) | 见下方第 11 条 |
| 12 | 数据服务加 restart 策略 | [#21](https://github.com/AidenNovak/heyvisions-lms/issues/21) | [#22](https://github.com/AidenNovak/heyvisions-lms/pull/22) | 无（本仓库独有文件） |
| 13 | 收敛上游强调色 + 正文阅读宽度 + 提示不再压字 | [#23](https://github.com/AidenNovak/heyvisions-lms/issues/23) | [#24](https://github.com/AidenNovak/heyvisions-lms/pull/24) | 见下方第 13 条 |
| 14 | 课程目录的列数随数量收窄 | [#25](https://github.com/AidenNovak/heyvisions-lms/issues/25) | [#27](https://github.com/AidenNovak/heyvisions-lms/pull/27) | 见下方第 14 条 |
| 15 | 登录/注册页只摆出真的能用的登录方式 | [#26](https://github.com/AidenNovak/heyvisions-lms/issues/26) | [#28](https://github.com/AidenNovak/heyvisions-lms/pull/28) | 见下方第 15 条 |
| 16 | 课程正文两条左边界 + 正文列与站点同宽 608px | [#29](https://github.com/AidenNovak/heyvisions-lms/issues/29) | [#30](https://github.com/AidenNovak/heyvisions-lms/pull/30) | 见下方第 16 条 |

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
- **追加**：复核时发现 `library.*` 整个命名空间在 zh 里没翻（66 个键的值与英文完全相同），
  而资料库在主导航里。一并补齐，连同导航标签（Library / Playgrounds / Store）
  与资料库分类页签 —— zh 的学习者路径已无未翻译的英文（品牌词与技术名词除外）。

## 6. 视觉令牌对齐 heyvisions.com

- **改什么**：字体换 Geist（中文回退 PingFang SC / 冬青黑 / 微软雅黑）；
  焦点环换品牌暖橙；圆角基准 8px → 10px；卡片投影从 `shadow-md` 压到 1px 浅投影。
- **为什么**：静态站已确立视觉规范，学习平台是同一产品的帐号与进度层，
  两处观感割裂会像换了一个产品。
- **影响范围**：`app/layout.tsx`、`lib/fonts.ts`、`styles/globals.css`，
  以及新增的 `docs/heyvisions/design-tokens.md`（令牌对照与验收方式）。
- **与上游的关系**：改动都落在令牌层——`.nice-shadow` 一条覆盖 700+ 处使用，
  不逐个组件替换，上游改版时不易被覆盖。`--ring`、`--radius` 各一行，冲突面极小。
- **顺带修掉的死代码**：中文字族原本写在 `var(--font-default, ...)` 的 fallback 位置，
  而这个变量由 next/font 注入且一定有值，所以那些字族从未生效 ——
  中文只能靠浏览器默认兜底，在 Windows/Linux 上会落到与静态站不同的字面。
  必须写在 `var()` 之外。
- **未覆盖**：`teal-*`（23 个文件）与 `indigo/violet/purple`（669 处）仍在。
  这些多用于管理员后台与编辑器，学习者主路径（课程列表、课时阅读）不涉及；
  全量替换工作量大且会大面积冲突，判断为不值得。

## 7. 品牌改名：HeyVisions → Yet to Dawn

- **改什么**：平台品牌名改为 Yet to Dawn，主站地址改为 `yettodawn.com`。
  `lrn-text.svg` 由 `<text>HeyVisions</text>` 换成从品牌稿拟合的「YET TO DAWN」矢量轮廓；
  删除已无引用的 `public/hv/`（第 2 条遗留的旧品牌源文件）。
- **为什么**：静态站已改用新品牌与配套域名，学习平台是同一产品的帐号与进度层，
  两处品牌名不一致会像两个产品。第 2 条把品牌收进了 `brand.ts`，
  所以改名只动一处默认值，未散落到组件里 —— 这正是当初抽配置的目的。
- **影响范围**：`apps/web/services/config/brand.ts`（默认值）、`apps/web/public/lrn-text.svg`
  （内容）、`apps/web/locales/zh.json`（`common.help_menu.website` 一处）、
  `components/Objects/Menus/OrgMenu.tsx`（字标改为按高度定尺）、
  若干 `alt` 与注释、`public/hv/`（删除）、`scripts/heyvisions/*`。
- **与上游的关系**：`lrn-text.svg` **沿用文件名**，与第 2 条的策略一致；
  同步时若上游更新了它的内容，固定保留本仓库版本。
- **字标改成矢量轮廓的原因**：原文件是 `<text>` + 字体栈，靠浏览器字体渲染。
  服务器端没有这些字体，不同机器渲染出的字宽与字形都不一致，而 logo 不该随环境变形；
  品牌稿用的是几何无衬线体，系统字体栈里没有对应字形。
  拟合脚本 `scripts/heyvisions/fit-wordmark.py` 的要点写在它自己的 docstring 里，
  其中最容易做错的一条是**字母带孔**：O、D、A 中间的空隙要靠
  `fill-rule="evenodd"` 表达，不能像实心标记那样把孔补上，否则 O 会糊成实心块。
- **未覆盖**：`docs/heyvisions/CHANGELOG.md` 第 2、3 条与 `docs/heyvisions/design-tokens.md`
  里仍写着旧品牌名 —— 那是历史记录，改写等于造假，保留原样。

## 8. 品牌残留清扫：图片、界面文案、域名与邮件

第 7 条只改了「名字」，界面里还有一批**旧品牌的载体**没跟着走：位图里的字、硬编码在
组件与 22 个 locale 里的域名与产品名、以及发给用户的邮件。这一条把它们收干净。

- **改什么**：
  1. **位图重做**。`public/` 下 13 张图里仍有旧标识：`black_logo.png`（404 页，图里就是
     "HeyVisions" 字标）、`learnhouse_ai_black_logo.png`（AI 对话头部，图里是 "HV"）、
     `learnhouse_ai_simple.png`/`lrnai_icon.png`（上游标记的实心块）、
     `learnhouse_ai_simple_colored.png`/`ai_avatar.png`（上游紫色标 + 星芒）、
     `empty_thumbnail.png`（缩略图兜底图里的上游字形）、`dashLogo.png`。
     新增 `scripts/heyvisions/build-brand-pngs.py` 与它依赖的 `svgkit.py` 重新生成。
  2. **界面文案**。页标题与 metadata（登录/注册/找回/重置/验证、管理员、后台、课程页）
     改从 `getBrandName()` 取；`org?.name || 'LearnHouse'` 这类兜底（登录面板、移动端
     头部、结业证书、品牌预览）同上；帮助菜单、引导卡片、API 访问页的**上游链接**
     （docs/discord/university/classroom）改为品牌配置驱动，未配置就不渲染；
     品牌设置页样张里模拟地址栏的 `learnhouse.io` 改用 `getBrandHost()`；
     会话共享开关的文案、错误页支持链接、EE 横幅、版本失配提示、下载文件名同理。
  3. **locale 收尾**。`localize-remaining.py` 把 7 个自指键在 22 个语言里变量化为
     `{{brand}}`；上游专有资源名（LearnHouse University / The Classroom）英文改写、
     其余语言删键回落。
  4. **邮件**。Web 端模板的头图不再从上游站点拉取，发件人默认值、欢迎/联系邮件、
     Loops 来源标识改用品牌配置。
- **为什么**：第 7 条把品牌名收进了 `brand.ts`，但**图片里的字不读配置**，域名与
  产品名也仍散在组件里。用户在这几处仍会看到旧品牌或上游域名 —— 对外交付的平台上
  出现第三方品牌与第三方域名是 bug。
- **影响范围**：`apps/web/public/`（10 个位图，文件名沿用上游）、
  `apps/web/services/config/brand.ts`（新增 5 个取值函数）、约 25 个组件与页面、
  `apps/web/locales/*.json`（22 个文件）、`scripts/heyvisions/`（新增 3 个脚本）。
- **与上游的关系**：位图**沿用上游文件名**（`learnhouse_*`），只换内容 —— 与第 2、7 条
  同一策略，把同步冲突压到最小。组件改动集中在「文案取值」这一层，不重构结构。
  locale 的 `{{brand}}` 变量化会与上游的翻译更新冲突，冲突是机械的。
- **脚本修复**：`localize-brand-strings.py`（第 5 条引入）与 `fit-wordmark.py` 的正则用
  `\b` 匹配品牌名，在 CJK 语境下失效（`LearnHouse大学`、`LearnHouseアカデミー` 里
  品牌名后紧跟的是非 ASCII 单词字符，Python 认为没有词边界），ja/ko 的硬编码因此被
  静默漏掉。改用「两侧不是拉丁字母」判据后两个脚本收敛到同一结果。
- **判断为「不改」的**（理由各自不同，都不是遗漏）：
  - `courses.import.learnhouse_*` 与 `dashboard.courses.import_learnhouse*`：这里的
    LearnHouse 指**外部导入格式**（「导入 LearnHouse 导出的 zip」），改名会让功能说不通。
  - 水印相关文案与 `public/upstream/`：开 `NEXT_PUBLIC_BRAND_WATERMARK` 时应显示
    **真的上游标识**，署名第三方却用自家 logo 是错的。
  - 代码标识符（`learnhouseIcon`、`LearnHousePlayer`、`LearnHousePlanType` 等）与注释：
    不渲染给用户，改名只会扩大同步冲突面。
  - 无调用点的死键（`showcase_explore`、`teach_the_world.description`、
    `dashboard.home.learnhouse_university`）：已核对全仓无引用，不渲染，改它只制造 diff。

## 9. 品牌残留清扫（续）：API 侧与构建产物

第 8 条按「界面渲染出来的东西」扫，覆盖面是 `apps/web`。这一条补上两处它够不到的地方：
**API 自己发出的字符串**，以及**只有打包进构建产物才看得见的常量**。

- **改什么**：
  1. **API 对外字符串**。`GET /` 返回 `Welcome to LearnHouse ✨`（公开端点）；
     MFA 的 `TOTP_ISSUER` 写死上游名，会出现在每位用户的验证器 App 里；
     webhook 外发请求的 `User-Agent` 与测试事件正文、课程导入的报错文案、
     AI 供应商面板的 `app_title` 兜底同理。全部改为从 `config.yaml` 的
     `site_name` 取值（复用邮件侧已有的 `brand_name()`）。
  2. **站内联系入口**。`_support_url()` 返回上游客服邮箱 `hello@learnhouse.app`，
     且 `contact_email` 的默认值也是它 —— 白标部署上等于把用户引导给上游。
     `contact_email` 默认改为空，魔法链接错误页在没有配置联系地址时**不渲染**按钮。
  3. **SaaS 专属入口**。定价页的 "Talk to us" 硬链 `learnhouse.app/contact`；
     新增 `getBrandContactUrl()`（默认空），未配置则不渲染该按钮。
  4. **孤儿素材**。`public/UNI_LOGO.png`（紫色大学标）与 `public/theclassroom.png`
     （第三方课程平台标）已无任何引用却仍可公开访问 —— 那是别人的商标挂在自家域名下，
     删除。二者都不在品牌位图生成脚本的清单里，删掉不会影响重生成。
- **为什么**：第 8 条查的是「页面上看得见的文字」，而 API 返回体、验证器里的发行方、
  外发 webhook 的 UA 都不经过页面。构建产物层面也只在打包后才暴露 —— 源码里搜不到，
  因为字符串来自组件被静态展开后的结果。
- **影响范围**：`apps/api/{app.py, config/config.yaml}` 与 5 个 service/router，
  `apps/web/services/config/brand.ts` 与 2 个定价组件，4 个 API 测试（断言改为取自配置，
  而非写死品牌名），新增 `scripts/heyvisions/server-rebuild-web.sh`（可反复执行的重建：
  备份 → 清理 → 构建 → 补齐 standalone 产物 → 重启，含内存预检）与
  `scripts/heyvisions/verify-brand-clean.sh`（交付前只读核对：页面层 / 产物层 / 接口层）。
- **判断为「不改」的**：
  - 水印组件（`Watermark.tsx`、org 页脚）：受 `NEXT_PUBLIC_BRAND_WATERMARK` 控制，
    默认关闭、已确认页面 DOM 里不存在。开启时应显示**真的**上游标识 —— 这是署名，
    不是推广，见第 8 条同一判断。
  - `public/upstream/` 与 `learnhouse_ai_*` 等沿用上游命名的位图：前者同上，
    后者内容已换成自有品牌，改名只会扩大与上游同步的冲突面。
  - 导入格式文案（`courses.import.learnhouse_*`）：指外部导入格式，见第 8 条。
  - 产物里残余的 `learnhouse.io` 字样：全在注释与 JSDoc 示例里，不渲染。
  - **未改，但需要决策**：`services/orgs/custom_domains.py` 有两处同源问题。
    (a) 自定义域名的保留表只挡 `*.learnhouse.io` / `*.learnhouse.app`，**不含本站域名**，
    租户管理员可以把 `yettodawn.com` 或 `*.yettodawn.com` 注册成自己的自定义域名，
    通过 TXT 校验后平台就会把该域名路由到他的组织；(b) `LEARNHOUSE_DOMAIN` 的默认值
    是 `learnhouse.io`，且它同时充当管理端看到的 CNAME 目标与「自有子域自动放行」
    判据 —— 未设该环境变量时等于告诉管理员把域名 CNAME 到上游主机。
    修法很小（保留表与默认值都改为从配置解析出的本站域名），但会改变已有数据的
    校验结果，需要先确认没有组织已经持有同类域名，所以留作决策项而非本次一并改。
    用于 TXT 校验的 `_learnhouse-verification` / `learnhouse-verify=` 是**内部协议常量**，
    改它会让管理员已添加的解析记录失效，不应动。

## 10. 生产上线：单主机名 HTTPS 部署与联调修出的四处缺陷

平台此前只在开发栈里跑过（`server-up.sh` + SSH 隧道，绑定回环、配置写死
`127.0.0.1`）。这一条把它做成对外服务（`learn.yettodawn.com`，systemd + nginx +
Let's Encrypt），并在真实链路（浏览器 → Cloudflare → nginx → Next/API）上暴露并修掉
四个只在生产形态下才会犯的问题。

- **改什么**：
  1. **注册账号不进组织**。单租户部署只有一个组织，但 `/signup` 首访时还没有
     `LH_org` cookie（middleware 把它写在**响应**上，服务端组件要下一次请求才看得到），
     于是表单不带 org，`/api/signup` 走「无组织」分支建出一个不属于任何组织的账号 ——
     能登录、能看公开课，但所有进度入口都按「访客」隐藏。现在单租户下由
     `/api/signup` 服务端解析默认组织（读 `instance/info` 的租户模式与默认 slug，
     而不是读 cookie：首访没有 cookie，而首访正是注册发生的时候），多租户行为不变。
  2. **服务端 API 地址写死在构建期**。`lib/auth/server.ts` 用模块级常量
     `process.env.NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL`，而 Next 会把 `NEXT_PUBLIC_*`
     内联进产物：换域名或换 API 端口后它仍是旧值，`getServerSession()` 恒为 null，
     已登录用户在读它的页面上被静默弹回 `/login`。改为每次调用从运行时配置取
     （`LEARNHOUSE_SERVER_BACKEND_URL`，只写进服务端的 `runtime-config.json`，
     不进浏览器），回环默认值让同机部署的服务端调用不必绕公网。
  3. **`/orgs/{slug}/…` 形式的 URL 一律 404**。catch-all rewrite 无条件加前缀，
     手输/收藏/外部文档里的 `/orgs/default/dash` 会被改写成
     `/orgs/default/orgs/default/dash`。已带内部前缀的路径改为透传。
  4. **会话 cookie 缺 `Secure`**。`getCookieOptions()` 读
     `request.nextUrl.protocol`，而它来自 `X-Forwarded-Proto` —— 这个头在本部署里
     **刻意不传给 Web**（见下），于是 Next 认为请求是 http，30 天的刷新令牌不带
     `Secure`。改为额外认 `X-Forwarded-Scheme`（Next 不读它，因此不会触发下面那个
     自转发问题），由 nginx 标记。
- **为什么**：前两条直接决定「注册了能不能用」与「登录会不会被随机弹掉」，
  是产品可用性问题而不是配置口味；后两条一个是 404、一个是安全属性缺失。
- **部署形态的坑（写进 `docs/heyvisions/PRODUCTION.md`）**：
  Web 必须绑 `0.0.0.0`（绑回环时 Next 处理绝对 URL rewrite 的自转发连不上，
  每个组织页 500 且路径被反复叠加）；API 单元不能设 `ProtectHome=true`
  （venv 解释器在 `/root/.local/share/uv/` 下，会 `203/EXEC`）；
  nginx 对 Web 不传 `X-Forwarded-Proto`（Next 用它拼自转发的绝对 URL，
  传 https 会对明文端口做 TLS 握手）；必须有 `/content/` 规则，否则头像、
  封面、附件全部 404。
- **影响范围**：`apps/web/app/api/signup/route.ts`、`apps/web/lib/auth/server.ts`、
  `apps/web/proxy.ts`、`apps/web/services/auth/cookies.ts`；
  新增 `docs/heyvisions/PRODUCTION.md`、`scripts/heyvisions/server-install-prod.sh`、
  `scripts/heyvisions/sync-content.sh`、`scripts/heyvisions/systemd/*.service`、
  `scripts/heyvisions/nginx/yettodawn-lms.conf.template`；
  `scripts/heyvisions/{docker-compose.yml,server-rebuild-web.sh}` 调整。
- **与上游的关系**：四处都是上游文件的小改，各自带注释说明「为什么这样改」，
  集中在「部署形态适配」这一层，不重构结构。同步上游时按注释逐条核对。
  数据服务的端口绑定与部署脚本是本仓库独有，冲突面为零。

## 11. 单元正文的模板缺口：同步时生成平台专用副本

- **改什么**：新增 `scripts/heyvisions/build-lms-units.py`，`sync-content.sh` 先调它生成
  自包含正文再上传。
- **为什么**：单元正文的「模板或反例」一节写着「使用本页下方的…模板」，但模板文字
  **不在 `.md` 里** —— 它存于 `example/src/course/templates.js`，由站点页面在渲染到该节时
  注入（`example/src/course-page.jsx`）。学习平台只渲染裸 Markdown，没有这层注入，
  于是 6/6 个公开单元都会指向一个不存在的模板：学习者读到「见下方模板」却看不到模板。
- **做法**：不把模板抄进 `.md`（那会变成两处维护），而是在同步时把 `templates.js` 的内容
  作为围栏代码块追加到该节末尾，生成平台专用副本。两边同源，站点读原始 `.md` 不受影响。
  脚本只在 `--out` 目录里写，不动 website 仓库的任何文件。
- **影响范围**：新增 `scripts/heyvisions/build-lms-units.py`；`scripts/heyvisions/sync-content.sh`
  增加生成步骤；`docs/heyvisions/PRODUCTION.md` 记录原因与用法。不触及上游文件。
- **与上游的关系**：纯本仓库新增，冲突面为零。

## 12. 数据服务加 restart 策略

- **改什么**：`scripts/heyvisions/docker-compose.yml` 的两个 service 加
  `restart: unless-stopped`，并把「端口只绑回环」的原因写进文件头。
- **为什么**：此前是默认的 `restart: no`。这台机器同时跑生产，主机重启后 systemd 单元
  会自启（`enabled=enabled`），但数据库容器不会回来 —— API 起来后连不上库，
  表现成「服务在跑、页面全 500」的静默故障。用 `unless-stopped` 而不是 `always`：
  手动 `docker compose stop` 之后不应被自动拉起。
- **影响范围**：仅该 compose 文件。本仓库独有（上游走 `npx learnhouse dev`），冲突面为零。

## 13. 收敛上游强调色 + 正文阅读宽度 + 提示不再压字

- **改什么**：
  1. **强调色收敛**。第 6 条只把 `--ring` 换成了品牌深林绿，**逐像素硬编码的强调色
     没跟着走**：单元页同一屏里出现四种互不相关的颜色 ——「咨询 AI」的紫蓝
     `conic-gradient`、右下角 Copilot 气泡的全紫（`bg-violet-600`）、顶部导航唯一的
     彩色实心图标（`text-violet-500`）、「贡献」的亮绿（`bg-emerald-600`），
     角色徽章另有紫/蓝/绿三档。按 `design-tokens.md` 的规则统一成
     「单一强调色 + 中性控件」，绿色/红色只留给「通过/失败」等语义状态
     （`bg-teal-*` / `bg-emerald-*` 的状态条与成绩单**保留不动**）。
  2. **品牌残留**。Copilot 空态的图形是**上游 LearnHouse 的字标**（紫渐变
     `#c4b5fd→#7c3aed`）—— 白标平台上出现第三方的图形标识，属于第 8/9 条同类问题的
     漏网。换成 `public/brand/yet-to-dawn-mark.svg`。
  3. **正文阅读宽度**。`.markdown-body` 铺满容器，1440px 屏幕上单行超过 70 个汉字。
     静态站的课时正文是 558px / 15.5px ≈ 36 字/行，平台取 40rem（≈40 字/行），
     与站点同一区间 —— 用户在两个面之间来回走，正文节奏不该在这条界限上变化。
     表格与代码块不压窄（按列/按行对齐，压窄反而难读）。
  4. **提示不再压住正文**。`MiniInfoTooltip` 固定 `-top-20`，而它的锚点在
     **固定底栏**里 —— 于是提示浮在底栏上方 5rem，正好压住正文最后一行
     （实测遮住「当作完成任务」几个字）。新增 `placement="inline-start"` 侧放模式，
     底栏的两处调用改用它；`top` 仍是默认值，其他调用点行为不变。
- **为什么**：这四条都属于「同一产品的两个面看起来像两个产品」——
  配色是观感上的，阅读宽度与遮挡是实际影响读不读得下去的。
- **影响范围**：`components/Copilot/CopilotBubble.tsx`、`components/Objects/Menus/OrgMenu.tsx`、
  `components/Objects/Activities/AI/AIActivityAsk.tsx`、`components/Security/HeaderProfileBox.tsx`、
  `components/Objects/MiniInfoTooltip.tsx`、
  `app/orgs/[orgslug]/(withmenu)/course/[courseuuid]/activity/[activityid]/activity.tsx`、
  `styles/globals.css`。
- **顺带修掉的脚本 bug**：`server-rebuild-web.sh` 用
  `systemctl list-unit-files | grep -q hv-lms-web` 判断是否装了生产单元。脚本开了
  `pipefail`，而 `grep -q` 一命中就退出，左侧进程吃到 SIGPIPE 让整条管道返回非零 ——
  结果是「明明装了单元却走开发栈」，把开发栈拉起来和 systemd 抢端口。
  第一次改成 `printf ... | grep -q` 仍犯同样的错（管道没去掉）；最终用 `case` 做纯字符串
  匹配，没有管道也没有子进程。
- **与上游的关系**：都是上游文件的小改，改动集中在 class 字符串、一处内联样式与
  一个新增的可选 prop，各自带注释说明原因。新增的 `.markdown-body` 规则在本仓库的
  `globals.css`，与上游无关。

## 14. 课程目录的列数随数量收窄

- **改了什么**：课程网格的列数随课程数量收窄 —— 1 门课收成一列（上限 560px），
  2 / 3 门按数量给列，4 门及以上保持原行为。规则抽在新增的
  `apps/web/lib/catalog-grid.ts`，两处调用点各改一行 className。
- **为什么**：列数原本写死成 4 列，与数量无关。站上只有 1 门课时，1440px 视口下
  实测是「4 列 × 328px，卡片只占 1 列」，网格内空出 76% —— 页面看起来像内容
  没加载出来，而不是像「这里就只有一门课」。规则对齐静态站
  `example/src/courses.css` 的 `.catalog-grid.count-1{minmax(0,560px)}`。
- **为什么不用 auto-fit**：`repeat(auto-fit, minmax(...))` 会把**唯一**一张卡片
  在 `1fr` 下拉到整行 1361px，把「左侧留白」换成「卡片过宽」，不是想要的收敛。
- **影响范围**：`apps/web/lib/catalog-grid.ts`（新增）、
  `app/orgs/[orgslug]/(withmenu)/courses/courses.tsx`、`components/Landings/LandingClassic.tsx`。
  仓库内另有 9 处同款 4 列网格（library、dash、账户页等）本次不动，避免改动面过大。
- **与上游的关系**：网格类是上游文件里的一行 className，冲突面窄；规则用新文件承载。
  这是跟随站点的品牌决策，不回馈上游。
- **验收**：`bun test tests/catalog-grid.test.mjs`（6 项）；生产实测 1440px 下
  1 门课时网格解析为 1 列、卡片宽 560px（修复前 4 列 328px、右侧空 1033px）。

## 15. 登录/注册页只摆出真的能用的登录方式

- **改了什么**：渲染条件从「组织策略允许」改为「组织策略允许 **且** 本部署配齐凭据」。
  未配 `LEARNHOUSE_GOOGLE_CLIENT_ID` 时不摆「使用 Google 登录」；未配
  `RESEND_API_KEY` 时不摆「把登录链接发到我的邮箱」与「忘记密码？」。
  另修 `/forgot` 的漏译（成功提示里混着后端英文原句）。
- **为什么**：组织策略把 password / magic_login / google / sso 全开着，但环境里
  两个凭据都没有。实测后果：「Google 登录」点下去是 **500**；两个邮件入口则
  界面提示「已发送」而**实际无信可发** —— 静默失败，用户会以为自己输错了邮箱。
  页面本身不删，配好凭据入口自动恢复。
- **实现要点**：新增 `services/auth/authCapabilities.ts`，与既有 `authMethods.ts`
  分工明确（前者=本机做不做得到，后者=组织允不允许）。能力必须在**服务端**页面
  组件里算好再用 props 下传 —— `process.env` 在 `'use client'` 里读不到。
- **影响范围**：`services/auth/authCapabilities.ts`（新增）、
  `app/auth/login/{page,login}.tsx`、`app/auth/signup/{page,OpenSignup,signup}.tsx`、
  `app/auth/forgot/forgot.tsx`、`locales/{en,zh}.json`。
- **与上游的关系**：改的是渲染条件与一句文案，能力探测放在新文件里，不与上游的
  组织策略逻辑纠缠。本站部署形态决定的产品决策，不回馈上游。
- **验收**：`bun test tests/auth-capabilities.test.mjs`（6 项，断言「缺凭据⇒不可用」）；
  生产实测未配凭据时三个入口均不出现、密码登录仍可用（关键回归项）；
  另起一个带 `RESEND_API_KEY` 的实例对比，确认邮件入口会恢复。

## 16. 课程正文两条左边界 + 正文列与站点同宽

- **改了什么**：`.markdown-body` 的阅读宽度与居中从「逐子元素设 margin」改为
  「容器限宽居中」，并把列宽从 40rem 校正为 **38rem（608px）**。
- **为什么**：#24 的写法特异性 (0,1,0)，被上游 `.markdown-body h1 { margin: .67em 0 }`
  这类元素级规则 (0,1,1) 盖掉，标题的左右 margin 被重置成 0 —— 结果是标题贴左、
  段落居中，实测 1440px 下标题 x=84、段落 x=393，一屏之内两条左边界。
  另外 #24 注释把静态站正文列记成「558px / 15.5px」，实测站点是
  **608px / 16px**，改成 38rem 后平台与站点完全同宽。
- **为什么带 !important**：正文排版基线来自 `github-markdown-css`（组件直接 import
  的第三方表），它是**无层**样式，而本文件在 `@layer utilities` 里 —— 无层优先级
  高于所有层，不带 `!important` 时 `margin-inline` 会被盖掉（实测列宽受限但仍左贴）。
  靠源顺序取胜不成立：Next.js 的 CSS 分块顺序不由该文件决定。上游在同名选择器下
  也用 `!important`（`.markdown-body > :first-child { margin-top: 0 !important }`）。
- **影响范围**：`apps/web/styles/globals.css`（本仓库自己加的规则，不碰上游文件）。
- **与上游的关系**：修法是**减少**与上游的特异性竞争（改到容器上），长期更利于同步。
- **验收**：无头 Chromium 断言 `.markdown-body` 直接子元素里标题与段落左边界相同；
  修复后 1440px 下两者同为 x=409、列宽 608px，390px 下同为 x=52、无横向滚动。

## 待办

| Issue | 内容 |
| --- | --- |
| — | 发信未配置：魔法链接、邮箱验证、找回密码都发不出信（密码登录正常）。要开需 Resend/SMTP 凭据。**第 15 条已让这些入口在未配置时不再显示**，配好凭据即自动恢复 |
| — | 上游导入/水印相关文案的取舍（见第 5、8 条的「未覆盖」与「不改」） |
| — | 管理员后台的 340+ 个 zh 未翻译键（学习者路径已覆盖） |
| — | `custom_domains.py` 的保留域名表只挡 `*.learnhouse.io`，未含本站域名；CNAME 目标的默认值也仍是上游域名（详见下） |
| — | 部署若需回复邮件与商务联系，需设 `LEARNHOUSE_CONTACT_EMAIL` 与 `NEXT_PUBLIC_BRAND_CONTACT_URL` |
| — | 静态站与学习平台是两套独立账号（不同后端、不同 cookie）；把站点入口接到平台前需先定域名的去留 |
| — | CF 上 faka/kb/usdt/status/sapi 等死子域记录待清理（与 LMS 无关，工作区遗留项） |

## 上游同步

| 日期 | 上游 commit | 结果 |
| --- | --- | --- |
| — | （尚未同步） | 基线 `2841620b` |
