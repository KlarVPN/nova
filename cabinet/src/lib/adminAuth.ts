import { getInitData, isTelegramWebApp } from './telegram'

export function getAuthHeaders(): Record<string, string> {
  if (isTelegramWebApp()) {
    return { 'X-Telegram-Init-Data': getInitData() }
  }
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}
