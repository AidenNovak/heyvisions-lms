import { getConfig } from './config'

/**
 * 平台品牌配置 —— 本 fork 的唯一品牌事实源。
 *
 * 上游是通用开源平台，本仓库以 Yet to Dawn 的身份对外提供服务。
 * 所有对外可见的品牌文案、法律链接都从这里取，避免散落在各个组件里；
 * 也因为读的是运行时配置，换部署不需要改代码。
 *
 * 每一项都可用运行时配置覆盖（`runtime-config.js` 或 `NEXT_PUBLIC_*`），
 * 留空则回退到下面的默认值。默认值即 Yet to Dawn，不再回退到上游品牌 ——
 * 对外交付的平台上出现第三方品牌是 bug，不是 fallback。
 */

/** 平台显示名，出现在页脚版权、登录页条款措辞、分享卡片等处。 */
export const getBrandName = (): string => getConfig('NEXT_PUBLIC_BRAND_NAME', 'Yet to Dawn')

/** 服务条款地址。留空则页脚不渲染该链接，而不是指向别家的条款页。 */
export const getTermsUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_TERMS_URL', '')

/** 隐私政策地址。留空则不渲染。 */
export const getPrivacyUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_PRIVACY_URL', '')

/** 平台主站地址（首页 "Powered by" 的指向）。 */
export const getBrandSiteUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_SITE_URL', 'https://yettodawn.com')

/**
 * 平台主站的主机名（不含协议），用于界面里的域名示意。
 *
 * 品牌设置页有几处「模拟浏览器地址栏 / 聊天链接预览」的样张，需要显示一个域名；
 * 原来硬编码上游的 `learnhouse.io`，在那个位置等于告诉管理员本站不是自己的域名。
 */
export const getBrandHost = (): string =>
  getBrandSiteUrl().replace(/^https?:\/\//, '').replace(/\/+$/, '')

/**
 * 帮助菜单里的外部链接。
 *
 * 上游这三项指向 docs.learnhouse.app / learnhouse.app / discord.gg/learnhouse ——
 * 那是**上游社区**，不是本站。白标平台上把用户送去第三方社区，既是第三方推广，
 * 也会让人以为本站是别人的子站，所以默认不再指向上游：
 *
 * - 官网：默认用品牌主站（一定有值）
 * - 文档 / 社区：默认**留空**。没有对应的自有资源时，界面隐藏该项而不是塞一个
 *   上游链接或猜一个可能 404 的路径；有资源时用环境变量配上即可恢复。
 */
export const getBrandDocsUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_DOCS_URL', '')

/** 社区 / 交流群地址。留空则帮助菜单不显示该项。 */
export const getBrandCommunityUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_COMMUNITY_URL', '')

/**
 * 商务 / 销售联系地址，用于 SaaS 模式的「联系我们」入口。
 *
 * 上游把这条 CTA 硬链到 `learnhouse.app/contact` —— 点下去是去给上游发商务咨询，
 * 而这是别家的部署。默认**留空**：没有自建销售渠道时就不渲染这个按钮，
 * 而不是把访客送去第三方。配置了 `NEXT_PUBLIC_BRAND_CONTACT_URL` 即可恢复。
 */
export const getBrandContactUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_CONTACT_URL', '')

/**
 * 品牌名的「文件名安全」写法，用于下载文件的默认名。
 *
 * 品牌名是给人看的（"Yet to Dawn" 带空格与大写），直接拼进文件名在部分系统上
 * 会带来多余的引号或转义；这里统一转成小写连字符形式（`yet-to-dawn`）。
 */
export const getBrandFileStem = (): string =>
  getBrandName().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-').replace(/^-+|-+$/g, '')

/**
 * 是否显示平台水印。
 *
 * 上游在 OSS 模式默认展示 "Made with LearnHouse" 并链到上游站点；
 * 本 fork 默认关闭 —— 对外交付的课程平台不应展示第三方推广。
 * 仅供上游贡献者或需要反向标注的场景显式打开。
 */
export const isBrandWatermarkEnabled = (): boolean =>
  getConfig('NEXT_PUBLIC_BRAND_WATERMARK', 'false') === 'true'

/**
 * 未指定语言时的平台默认语言。
 *
 * 与组织配置里的 `default_language` 不同：那个只有等组织配置取回后才生效
 * （首屏之后），这个是**首帧**就用的值。两者默认都是 zh。
 * 组织配置若与之不同，会在其取回后覆盖。
 */
export const getDefaultLanguage = (): string =>
  getConfig('NEXT_PUBLIC_DEFAULT_LANGUAGE', 'zh')
