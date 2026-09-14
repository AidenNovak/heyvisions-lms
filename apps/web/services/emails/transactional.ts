import 'server-only'
import { send } from './resend'
import { getBrandName, getBrandSiteUrl } from '@services/config/brand'
import { getConfig } from '@services/config/config'

// Non-billing transactional emails (welcome, contact). Same never-throw contract
// as the billing mails: fire-and-forget, no-op without RESEND_API_KEY.

export async function sendWelcomeAccountMail(args: { email: string; username?: string }): Promise<void> {
  const { email, username } = args
  const brand = getBrandName()
  await send(email, `Welcome to ${brand} 👋`, {
    accentColor: '#171717',
    heading: `Welcome to ${brand}!`,
    subtitle: username
      ? `Hey ${username}, we're thrilled to have you on board.`
      : "We're thrilled to have you on board.",
    body: "You're ready to build and share courses. Here's how to get the most out of it:",
    bulletPoints: [
      'Create your first course and add content in minutes.',
      'Invite learners and track their progress.',
      'Brand your school and share it with the world.',
    ],
    cta: { label: 'Get started', href: getBrandSiteUrl() },
  })
}

export async function sendContactMail(args: {
  fromEmail: string
  name?: string
  message: string
  to?: string
}): Promise<void> {
  const { fromEmail, name, message, to } = args
  // 收件人兜底：原来的 hello@learnhouse.app 会把站内联系表单的留言发到**上游**邮箱。
  // 改成品牌配置里的地址（留空则由 RESEND_CONTACT_TO 指定，否则不发）。
  const fallback = process.env.RESEND_CONTACT_TO || getConfig('NEXT_PUBLIC_BRAND_CONTACT_EMAIL', '')
  if (!to && !fallback) {
    console.warn('[email] contact form has no recipient configured, skipping send')
    return
  }
  await send(to || fallback, `New contact form message from ${name || fromEmail}`, {
    accentColor: '#171717',
    heading: 'New contact message',
    subtitle: `From ${name ? `${name} · ` : ''}${fromEmail}`,
    body: message,
  })
}

// NOTE: org-created / org-deleted / account-deleted confirmation emails are
// deliberately NOT sent from here. Unlike Stripe/billing mails (which the web
// webhook owns), user/org lifecycle is owned by apps/api, which has its own
// email service — those confirmations belong there to avoid duplicate sends.
