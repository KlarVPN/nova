import messages from '@intlify/unplugin-vue-i18n/messages'
import { ref, watch } from 'vue'
import { createI18n } from 'vue-i18n'
import { getTelegramUser } from '@/lib/telegram'
import type en from './locales/en.json'

export const AVAILABLE_LOCALES = [
  { code: 'en', name: 'English' },
  { code: 'ru', name: 'Русский' },
  { code: 'uk', name: 'Українська' },
  { code: 'es', name: 'Español' },
  { code: 'tr', name: 'Türkçe' },
  { code: 'zh', name: '中文' },
  { code: 'ko', name: '한국어' },
] as const

type ValidLocale = (typeof AVAILABLE_LOCALES)[number]['code']
type Lang = typeof en

export type Locale = 'ru' | 'en' | 'uk' | 'es' | 'tr' | 'zh' | 'ko'

export const SUPPORTED_LOCALES: Locale[] = ['ru', 'en', 'uk', 'es', 'tr', 'zh', 'ko']

declare module 'vue-i18n' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  export interface DefineLocaleMessage extends Lang {}
}

function ruPlural(choice: number, choicesLength: number): number {
  if (choice === 0) return 0
  const n = Math.abs(choice)
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 1
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 2
  return Math.min(3, choicesLength - 1)
}

export function detectLocale(langCode?: string): Locale {
  if (!langCode) return 'ru'
  const lang = langCode.split('-')[0].toLowerCase()
  return (SUPPORTED_LOCALES.includes(lang as Locale) ? lang : 'ru') as Locale
}

function getSavedLocale(): ValidLocale {
  const saved = localStorage.getItem('lang')
  if (saved && AVAILABLE_LOCALES.some((l) => l.code === saved)) {
    return saved as ValidLocale
  }
  return 'ru'
}

export const locale = ref<ValidLocale>(getSavedLocale())

export const i18n = createI18n({
  legacy: false,
  locale: locale.value,
  fallbackLocale: 'en',
  messages,
  pluralRules: { ru: ruPlural, uk: ruPlural },
})

watch(locale, (newLocale) => {
  localStorage.setItem('lang', newLocale)
  i18n.global.locale.value = newLocale
})

export function setLocale(newLocale: ValidLocale) {
  locale.value = newLocale
}

export function initLocale() {
  const saved = localStorage.getItem('lang')
  if (!saved || !AVAILABLE_LOCALES.some((l) => l.code === saved)) {
    const tgUser = getTelegramUser()
    locale.value = detectLocale(tgUser?.language_code)
  }
}
