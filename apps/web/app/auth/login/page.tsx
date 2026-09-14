import { getOrganizationContextInfo } from '@services/organizations/orgs'
import { getAuthOrgSlug } from '@services/org/orgResolution'
import LoginClient from './login'
import { Metadata } from 'next'
import OrgNotFound from '@components/Objects/StyledElements/Error/OrgNotFound'
import { getBrandName } from '@services/config/brand'
import { getAuthCapabilities } from '@services/auth/authCapabilities'

export async function generateMetadata(): Promise<Metadata> {
  const orgslug = await getAuthOrgSlug()

  if (!orgslug) {
    // Apex (org-less) login.
    return { title: `Login — ${getBrandName()}`, robots: { index: false, follow: false } }
  }

  let org: any = null
  try {
    org = await getOrganizationContextInfo(orgslug, {
      revalidate: 60,
      tags: ['organizations'],
    })
  } catch {
    // Stale cookie or unknown org — fall back to generic title
  }

  return {
    title: 'Login' + ` — ${org?.name || getBrandName()}`,
    robots: { index: false, follow: false },
  }
}

const Login = async () => {
  const orgslug = await getAuthOrgSlug()

  // No org slug → bare apex (learn.io) → generic, org-less login.
  let org: any = null
  if (orgslug) {
    try {
      org = await getOrganizationContextInfo(orgslug, {
        revalidate: 60,
        tags: ['organizations'],
      })
    } catch {
      org = null
    }
    // A subdomain (or single-tenancy) slug that can't be resolved is a real error.
    if (!org) {
      return <OrgNotFound />
    }
  }

  return (
    <div>
      {/* 环境里配了什么，只有在服务端才读得到 —— 算好传下去，
          由客户端决定摆不摆 Google / 邮件入口。理由见 authCapabilities.ts。 */}
      <LoginClient org={org} capabilities={getAuthCapabilities()}></LoginClient>
    </div>
  )
}

export default Login
