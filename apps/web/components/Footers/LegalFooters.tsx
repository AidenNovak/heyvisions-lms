'use client'
// Shared legal/footer bits, ported from the platform's look.
//
// AuthFooter   — the "By continuing, you agree to … Terms of Service and
//                Privacy Policy." line shown under the auth forms.
// CopyrightFooter — the "© {year} <brand>" line for app surfaces
//                (the apex /home hub, the onboarding page, …).
//
// Yet to Dawn fork: brand name and legal URLs come from the brand config
// (services/config/brand.ts) instead of the upstream platform defaults.
// Leaving BRAND_TERMS_URL / BRAND_PRIVACY_URL unset hides the link rather
// than pointing readers at another company's terms.
import React from 'react'
import Link from 'next/link'
import { useTranslation } from 'react-i18next'
import { getBrandName, getPrivacyUrl, getTermsUrl } from '@services/config/brand'

export function AuthFooter({ className = '' }: { className?: string }) {
  const { t } = useTranslation()
  const brandName = getBrandName()
  // 运行时配置可能在模块加载后才注入，所以在组件内读取
  const termsUrl = getTermsUrl()
  const privacyUrl = getPrivacyUrl()
  const hasLegalLinks = Boolean(termsUrl || privacyUrl)
  // 没有配置条款/隐私地址时整句不渲染：句子的宾语就是那两个链接，
  // 只留"继续即表示你同意 Yet to Dawn 的"是不成句的。
  if (!hasLegalLinks) return null
  return (
    <div className={`pb-8 pt-6 text-center px-6 ${className}`}>
      <p className="text-[13px] text-black/30 font-medium">
        {t('auth.terms_text', {
          brand: brandName,
          defaultValue: `By continuing, you agree to ${brandName}'s`,
        })}{' '}
        {termsUrl ? (
          <>
            <Link
              href={termsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-black/50 hover:text-black/70 transition-colors"
            >
              {t('auth.terms_of_service', { defaultValue: 'Terms of Service' })}
            </Link>
            {privacyUrl ? ` ${t('auth.and', { defaultValue: 'and' })} ` : null}
          </>
        ) : null}
        {privacyUrl ? (
          <Link
            href={privacyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-black/50 hover:text-black/70 transition-colors"
          >
            {t('auth.privacy_policy', { defaultValue: 'Privacy Policy' })}
          </Link>
        ) : null}
        .
      </p>
    </div>
  )
}

export function CopyrightFooter({
  year,
  className = '',
  tone = 'light',
}: {
  year: number
  className?: string
  // `light` → dark text on light bg; `dark` → light text on dark bg.
  tone?: 'light' | 'dark'
}) {
  const { t } = useTranslation()
  const brandName = getBrandName()
  // 运行时配置可能在模块加载后才注入，所以在组件内读取
  const termsUrl = getTermsUrl()
  const privacyUrl = getPrivacyUrl()
  const base = tone === 'dark' ? 'text-white/40' : 'text-black/35'
  const link = tone === 'dark' ? 'text-white/60 hover:text-white/80' : 'text-black/55 hover:text-black/75'
  return (
    <footer className={`w-full py-6 px-6 ${className}`}>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-x-5 gap-y-2 text-[13px] font-medium">
        <p className={base}>
          {t('common.copyright', { brand: brandName, defaultValue: `© {{year}} ${brandName}`, year })}
        </p>
        {termsUrl || privacyUrl ? (
          <nav className="flex items-center gap-x-5">
            {termsUrl ? (
              <Link
                href={termsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`${link} transition-colors`}
              >
                {t('auth.terms_of_service', { defaultValue: 'Terms of Service' })}
              </Link>
            ) : null}
            {privacyUrl ? (
              <Link
                href={privacyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`${link} transition-colors`}
              >
                {t('auth.privacy_policy', { defaultValue: 'Privacy Policy' })}
              </Link>
            ) : null}
          </nav>
        ) : null}
      </div>
    </footer>
  )
}
