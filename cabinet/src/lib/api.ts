import { getInitData, isTelegramWebApp } from './telegram'
import type {
  UserProfile,
  PlansData,
  ReferralData,
  PromoResult,
  PaymentResult,
  DevicesData,
  LocationStatus,
  ProxyItem,
  OperationsHistoryData,
  ChannelSubscriptionStatus,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

function getAuthHeaders(): Record<string, string> {
  if (isTelegramWebApp()) {
    return { 'X-Telegram-Init-Data': getInitData() }
  }
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const err = await res.json()
      detail = err.detail ?? detail
    } catch {}
    throw new ApiError(res.status, detail)
  }

  return res.json() as Promise<T>
}

export const api = {
  user: {
    me: () => request<UserProfile>('/user/me'),
  },

  auth: {
    loginByTelegram: (telegramUser: Record<string, unknown>) =>
      request<{ token: string; user_id: number }>('/auth/telegram', {
        method: 'POST',
        body: JSON.stringify({ telegram_user: telegramUser }),
      }),
    loginByAccessLink: (uuid: string) =>
      request<{ token: string; user_id: number }>('/auth/access-link-login', {
        method: 'POST',
        body: JSON.stringify({ uuid }),
      }),
    accessLink: () =>
      request<{ uuid: string; url: string }>('/auth/access-link'),
  },

  plans: {
    list: () => request<PlansData>('/plans'),
  },

  referral: {
    info: () => request<ReferralData>('/referral'),
  },

  promo: {
    apply: (code: string) =>
      request<PromoResult>('/promo/apply', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
  },

  payment: {
    create: (params: { months?: number; gb?: number; provider: string }) =>
      request<PaymentResult>('/payment/create', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    trial: () =>
      request<{ success: boolean; end_date: string }>('/payment/trial', {
        method: 'POST',
      }),
  },

  subscription: {
    connect: () => request<{ connect_url: string; config_link: string }>('/subscription/connect'),
  },

  devices: {
    list: () => request<DevicesData>('/devices'),
    disconnect: (hwid: string) =>
      request<{ success: boolean }>('/devices/disconnect', {
        method: 'POST',
        body: JSON.stringify({ hwid }),
      }),
  },

  channel: {
    status: () => request<ChannelSubscriptionStatus>('/channel/subscription-status'),
  },

  locations: {
    list: () => request<{ locations: LocationStatus[] }>('/locations'),
  },

  proxies: {
    list: () => request<{ proxies: ProxyItem[] }>('/proxies'),
  },

  operations: {
    list: () => request<OperationsHistoryData>('/operations'),
  },
}

export { ApiError }
