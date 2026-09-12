import Image from 'next/image'
import Link from 'next/link'
import upstreamWordmark from '@public/upstream/learnhouse-wordmark.svg'
import React from 'react'
import { useOrg } from '../Contexts/OrgContext'
import { useTranslation } from 'react-i18next'
import { usePlan } from '@components/Hooks/usePlan'
import { getDeploymentMode } from '@services/config/config'
import { isBrandWatermarkEnabled } from '@services/config/brand'

function Watermark() {
    const { t } = useTranslation()
    const org = useOrg() as any

    const mode = getDeploymentMode()
    const plan = usePlan()
    const watermarkConfig = org?.config?.config?.customization?.general?.watermark ?? org?.config?.config?.general?.watermark

    // HeyVisions fork: 平台以自有品牌对外交付，默认不展示上游推广位。
    // 保留组件与开关，需要反向标注上游时用 NEXT_PUBLIC_BRAND_WATERMARK=true 打开。
    if (!isBrandWatermarkEnabled()) return null

    // Visibility rules, in priority order:
    //   1. EE         → always hidden (white-label is part of the EE license).
    //   2. SaaS free  → always shown (free tier is branded).
    //   3. Otherwise  → respect the admin's toggle (default on).
    if (mode === 'ee') return null
    const showWatermark = plan === 'free' || watermarkConfig !== false
    if (!showWatermark) return null

    return (
        <div className='fixed bottom-8 end-8 z-50'>
            <Link href={`https://www.learnhouse.app/?source=in-app`} className="flex items-center cursor-pointer bg-white/80 backdrop-blur-lg text-gray-700 rounded-2xl p-2 light-shadow text-xs px-5 font-semibold space-x-2">
                <p>{t('common.made_with')}</p>
                <Image unoptimized src={upstreamWordmark} alt="LearnHouse" quality={100} width={95} />
            </Link>
        </div>
    )
}

export default Watermark