'use client'

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from '../locales/en.json';
import { loadDateLocale } from './format';
import { getDefaultLanguage } from '@services/config/brand';

const LOCALE_LOADERS: Record<string, () => Promise<{ default: any }>> = {
  fr: () => import('../locales/fr.json'),
  de: () => import('../locales/de.json'),
  es: () => import('../locales/es.json'),
  ar: () => import('../locales/ar.json'),
  ja: () => import('../locales/ja.json'),
  pt: () => import('../locales/pt.json'),
  ru: () => import('../locales/ru.json'),
  zh: () => import('../locales/zh.json'),
  hi: () => import('../locales/hi.json'),
  ko: () => import('../locales/ko.json'),
  it: () => import('../locales/it.json'),
  tr: () => import('../locales/tr.json'),
  vi: () => import('../locales/vi.json'),
  id: () => import('../locales/id.json'),
  pl: () => import('../locales/pl.json'),
  uk: () => import('../locales/uk.json'),
  nl: () => import('../locales/nl.json'),
  th: () => import('../locales/th.json'),
  bn: () => import('../locales/bn.json'),
  fa: () => import('../locales/fa.json'),
  sk: () => import('../locales/sk.json'),
};

// Only bundle English; lazy-load all other locales on demand
const resources = {
  en: { common: en },
};

async function loadLocale(lng: string) {
  const code = lng.split('-')[0]
  if (code === 'en' || !LOCALE_LOADERS[code]) return;
  if (i18n.hasResourceBundle(code, 'common')) return;

  try {
    const mod = await LOCALE_LOADERS[code]();
    i18n.addResourceBundle(code, 'common', mod.default, true, true);
  } catch (e) {
    console.warn(`Failed to load locale: ${lng}`, e);
  }
}

/** 用户显式选过语言的标记，由 LanguageSwitcher 写入。 */
const USER_PICKED_KEY = 'i18nextLng_userPicked'

/**
 * 首帧用什么语言。
 *
 * 上游直接用浏览器语言（探测顺序里 navigator 在 cookie 之后）。平台面向
 * 中文学习者、课程正文也是中文，用浏览器语言意味着英文浏览器的学习者
 * 先看到英文界面，等组织配置取回后再翻成中文 —— 实测这段约 4 秒，
 * 期间内容是可见的。
 *
 * 所以没被用户显式选过时，直接用平台默认语言，首帧就是对的。
 * 用户显式选过（LanguageSwitcher 写了标记）则返回 undefined，
 * 交给探测走 localStorage，尊重用户选择。
 */
function initialLanguage(): string | undefined {
  if (typeof window === 'undefined') return undefined
  try {
    if (localStorage.getItem(USER_PICKED_KEY)) return undefined
  } catch {
    // localStorage 不可用（隐私模式等）：按平台默认走，不影响渲染
  }
  return getDefaultLanguage()
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: initialLanguage(),
    fallbackLng: 'en',
    ns: ['common'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
    detection: {
      order: ['localStorage', 'cookie', 'querystring', 'navigator', 'path', 'subdomain'],
      caches: ['localStorage', 'cookie'],
      lookupLocalStorage: 'i18nextLng',
      lookupCookie: 'i18next',
    },
    react: {
      useSuspense: false,
    }
  });

// Load the detected language if it's not English — export the promise
// so I18nProvider can wait for resources before rendering.
// The date locale rides along: dayjs keeps its own registry, and without this
// every "2 hours ago" renders in English no matter the language.
export const initialLocaleReady = Promise.all([
  loadLocale(i18n.language.split('-')[0]),
  loadDateLocale(i18n.language),
]).then(() => undefined);

/**
 * Switch language safely — preloads the bundle before switching
 * so the UI never flashes English as a fallback.
 */
export async function changeLanguage(lng: string) {
  await Promise.all([loadLocale(lng), loadDateLocale(lng)])
  return i18n.changeLanguage(lng)
}

export default i18n;
