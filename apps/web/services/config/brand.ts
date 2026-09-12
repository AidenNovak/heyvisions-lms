import { getConfig } from './config'

/**
 * 平台品牌配置 —— 本 fork 的唯一品牌事实源。
 *
 * 上游是通用开源平台，本仓库以 HeyVisions 的身份对外提供服务。
 * 所有对外可见的品牌文案、法律链接都从这里取，避免散落在各个组件里；
 * 也因为读的是运行时配置，换部署不需要改代码。
 *
 * 每一项都可用运行时配置覆盖（`runtime-config.js` 或 `NEXT_PUBLIC_*`），
 * 留空则回退到下面的默认值。默认值即 HeyVisions，不再回退到上游品牌 ——
 * 对外交付的平台上出现第三方品牌是 bug，不是 fallback。
 */

/** 平台显示名，出现在页脚版权、登录页条款措辞、分享卡片等处。 */
export const getBrandName = (): string => getConfig('NEXT_PUBLIC_BRAND_NAME', 'HeyVisions')

/** 服务条款地址。留空则页脚不渲染该链接，而不是指向别家的条款页。 */
export const getTermsUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_TERMS_URL', '')

/** 隐私政策地址。留空则不渲染。 */
export const getPrivacyUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_PRIVACY_URL', '')

/** 平台主站地址（首页 "Powered by" 的指向）。 */
export const getBrandSiteUrl = (): string => getConfig('NEXT_PUBLIC_BRAND_SITE_URL', 'https://heyvisions.com')

/**
 * 是否显示平台水印。
 *
 * 上游在 OSS 模式默认展示 "Made with LearnHouse" 并链到上游站点；
 * 本 fork 默认关闭 —— 对外交付的课程平台不应展示第三方推广。
 * 仅供上游贡献者或需要反向标注的场景显式打开。
 */
export const isBrandWatermarkEnabled = (): boolean =>
  getConfig('NEXT_PUBLIC_BRAND_WATERMARK', 'false') === 'true'
