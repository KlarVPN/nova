import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { i18n } from '@/i18n/i18n.ts'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string): string {
  const lang = i18n.global.locale.value
  return new Date(dateStr).toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 GB'
  const gb = bytes / (1024 * 1024 * 1024)
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 * 1024)).toFixed(0)} MB`
}

export function formatPrice(price: number, currency: 'RUB' | 'STARS' = 'RUB'): string {
  if (currency === 'STARS') return `⭐ ${price}`
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(price)
}

export function pluralDays(n: number): string {
  return i18n.global.t('common.day', n)
}

export function formatExpiryDate(dateStr: string, daysRemaining?: number): string {
  const date = new Date(dateStr)
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()
  const formatted = `${dd}.${mm}.${yyyy}`
  if (daysRemaining !== undefined) {
    return `${formatted} (${pluralDays(daysRemaining)})`
  }
  return formatted
}

export function monthsLabel(months: number): string {
  return i18n.global.t('common.month', months)
}

export function daysUntil(dateStr: string): number {
  const now = new Date()
  const target = new Date(dateStr)
  return Math.max(0, Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)))
}

export function minutesUntil(dateStr: string): number {
  const now = new Date()
  const target = new Date(dateStr)
  return Math.max(0, Math.ceil((target.getTime() - now.getTime()) / (1000 * 60)))
}

export function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard) {
    return navigator.clipboard.writeText(text)
  }
  const el = document.createElement('textarea')
  el.value = text
  el.style.position = 'fixed'
  el.style.opacity = '0'
  document.body.appendChild(el)
  el.select()
  document.execCommand('copy')
  document.body.removeChild(el)
  return Promise.resolve()
}

export function providerLabel(provider: string): string {
  return i18n.global.t(`providers.${provider}`, provider)
}

export function providerIcon(provider: string): string {
  const map: Record<string, string> = {
    yookassa: 'credit-card',
    stars: 'star',
    cryptopay: 'bitcoin',
    freekassa: 'banknote',
    platega: 'wallet',
    severpay: 'shield',
  }
  return map[provider] ?? 'credit-card'
}
