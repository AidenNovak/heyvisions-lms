import { NextRequest } from 'next/server'
import { isSubdomainOf, isSameHost, isLocalhost, stripPort } from '@services/utils/ts/hostUtils'
import { getConfig } from '@services/config/config'

export const ACCESS_TOKEN_COOKIE = 'LH_access'
export const REFRESH_TOKEN_COOKIE = 'LH_refresh'
export const ACCESS_TOKEN_MAX_AGE = 8 * 60 * 60 // 8 hours
export const REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60 // 30 days

export function getDomainFromRequest(request: NextRequest): { domain: string; topDomain: string } {
  const envDomain = getConfig('NEXT_PUBLIC_LEARNHOUSE_DOMAIN')
  const envTopDomain = getConfig('NEXT_PUBLIC_LEARNHOUSE_TOP_DOMAIN')
  if (envDomain) {
    return {
      domain: envDomain,
      topDomain: stripPort(envTopDomain || envDomain),
    }
  }

  const cookieDomain = request.cookies.get('LH_frontend_domain')?.value
  const cookieTopDomain = request.cookies.get('LH_top_domain')?.value
  if (cookieDomain) {
    return {
      domain: cookieDomain,
      topDomain: stripPort(cookieTopDomain || cookieDomain),
    }
  }

  return { domain: 'localhost', topDomain: 'localhost' }
}

export function getCookieDomain(request: NextRequest): string | undefined {
  // Tenancy is the source of truth: in single mode cookies are always
  // host-only on whatever Host the request arrived with, regardless of
  // whether that's localhost or a self-hosted VPS hostname. In multi mode
  // we use the configured top domain so subdomains share the session.
  const tenancy = request.cookies.get('LH_tenancy')?.value || 'single'
  if (tenancy === 'single') return undefined

  const host = request.headers.get('host')
  const { domain, topDomain } = getDomainFromRequest(request)

  if (isLocalhost(host)) return undefined
  if (topDomain === 'localhost') return undefined
  if (isSubdomainOf(host, domain) || isSameHost(host, domain)) {
    return `.${topDomain}`
  }
  // Custom (per-org) domain in multi mode → host-only.
  return undefined
}

/**
 * Is this request served over HTTPS?
 *
 * **Yet to Dawn fork**: `request.nextUrl.protocol` alone is not enough here.
 * Next derives it from `X-Forwarded-Proto`, and this deployment deliberately
 * does NOT send that header to the Web process: Next uses it to build the
 * absolute URL for its internal rewrites, so `https` made it attempt a TLS
 * handshake against the plaintext upstream port and every org page 500'd (see
 * the vhost's `location /` and docs/heyvisions/PRODUCTION.md). nginx therefore
 * signals the original scheme with a dedicated header that Next ignores, and we
 * honor it so session cookies keep the `Secure` attribute they must have in
 * production. Shared with the auth proxy route so setting and clearing cookies
 * use the same judgement.
 */
export function isHttpsRequest(request: NextRequest): boolean {
  return (
    request.nextUrl.protocol === 'https:' ||
    request.headers.get('x-forwarded-scheme') === 'https'
  )
}

export function getCookieOptions(request: NextRequest) {
  const isSecure = isHttpsRequest(request)
  const domain = getCookieDomain(request)
  return {
    httpOnly: true,
    secure: isSecure,
    sameSite: 'lax' as const,
    path: '/',
    ...(domain ? { domain } : {}),
  }
}
