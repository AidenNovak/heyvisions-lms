/**
 * 这台部署**实际**能做到哪些登录方式。
 *
 * 与 `authMethods.ts` 的分工，别混淆：
 *
 * - `authMethods.ts` 回答「组织策略允不允许」。策略存在数据库里，管理员可改，
 *   前端读它只是为了不摆出后端一定会拒的方式。
 * - 本文件回答「这台机器有没有配齐凭据」。凭据在环境变量里，改它要动部署配置。
 *
 * **两个条件都满足，入口才该出现。** 只按策略渲染，会出现「策略允许、凭据没配」
 * 的组合，用户点下去要么 500，要么更糟：界面说邮件已发、实际无信可发。
 *
 * 这两个函数只能在**服务端**调用（页面组件里算好，再用 props 传进客户端组件）。
 * 环境变量在客户端读不到（`process.env.X` 只在构建期替换 `NEXT_PUBLIC_*`），
 * 在 `'use client'` 里调用会恒为 false，把能用的入口也一起藏掉。
 */

/** 事务性邮件（magic link、密码重置、邮箱验证）是否可用。 */
export function isTransactionalEmailConfigured(): boolean {
  // 发信走 Resend；没有 key 时 send() 会返回 { skipped: true }，
  // 调用方拿到的却仍是成功 —— 界面因此会谎报「已发送」。
  return Boolean(process.env.RESEND_API_KEY)
}

/** Google 登录是否可用。授权地址由服务端拿 client id 拼，缺了就是 500。 */
export function isGoogleSignInConfigured(): boolean {
  return Boolean(process.env.LEARNHOUSE_GOOGLE_CLIENT_ID)
}

export interface AuthCapabilities {
  /** 能否真正发信 —— 决定 magic link 与「忘记密码」是否摆出来。 */
  email: boolean
  /** 能否走 Google OAuth —— 决定「使用 Google 登录」是否摆出来。 */
  google: boolean
}

export function getAuthCapabilities(): AuthCapabilities {
  return {
    email: isTransactionalEmailConfigured(),
    google: isGoogleSignInConfigured(),
  }
}
