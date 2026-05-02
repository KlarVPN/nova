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
  AdminOverviewData,
  AdminPromoItem,
  AdminUserItem,
  AdminAdItem,
  AdminLogItem,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
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

  admin: {
    overview: () => request<AdminOverviewData>('/admin/overview'),
    sync: () => request<{ status: string; details?: string }>('/admin/sync', { method: 'POST' }),
    payments: (page = 0, pageSize = 20) =>
      request<{
        total: number
        items: Array<{
          payment_id: number
          user_id: number
          username: string | null
          first_name: string | null
          amount: number
          currency: string
          status: string
          provider: string | null
          months: number | null
          created_at: string | null
        }>
      }>(`/admin/payments?page=${page}&page_size=${pageSize}`),
    paymentsCsvUrl: () => `${BASE_URL}/admin/payments.csv`,
    promoActivationsCsvUrl: (promoId: number) => `${BASE_URL}/admin/promos/${promoId}/activations.csv`,
    promos: (page = 0, pageSize = 20) =>
      request<{ total: number; items: AdminPromoItem[] }>(`/admin/promos?page=${page}&page_size=${pageSize}`),
    createPromo: (payload: Record<string, unknown>) =>
      request<{ promo_code_id: number; code: string }>('/admin/promos', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    updatePromo: (promoId: number, payload: Record<string, unknown>) =>
      request<{ ok: boolean }>(`/admin/promos/${promoId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    deletePromo: (promoId: number) =>
      request<{ ok: boolean }>(`/admin/promos/${promoId}`, { method: 'DELETE' }),
    users: (page = 0, pageSize = 20) =>
      request<{ total: number; items: AdminUserItem[] }>(`/admin/users?page=${page}&page_size=${pageSize}`),
    banUser: (userId: number) => request<{ ok: boolean }>(`/admin/users/${userId}/ban`, { method: 'POST' }),
    unbanUser: (userId: number) => request<{ ok: boolean }>(`/admin/users/${userId}/unban`, { method: 'POST' }),
    ads: (page = 0, pageSize = 20) =>
      request<{ total: number; items: AdminAdItem[] }>(`/admin/ads?page=${page}&page_size=${pageSize}`),
    createAd: (payload: Record<string, unknown>) =>
      request<{ ad_campaign_id: number }>('/admin/ads', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    toggleAd: (campaignId: number, isActive: boolean) =>
      request<{ ok: boolean }>(`/admin/ads/${campaignId}/toggle`, {
        method: 'POST',
        body: JSON.stringify({ is_active: isActive }),
      }),
    deleteAd: (campaignId: number) => request<{ ok: boolean }>(`/admin/ads/${campaignId}`, { method: 'DELETE' }),
    logs: (page = 0, pageSize = 50, userId?: number) => {
      const userPart = typeof userId === 'number' ? `&user_id=${userId}` : ''
      return request<{ total: number; items: AdminLogItem[] }>(
        `/admin/logs?page=${page}&page_size=${pageSize}${userPart}`,
      )
    },
    broadcast: (text: string, target: 'all' | 'active' | 'inactive' = 'all') =>
      request<{ queued: number; target: string }>('/admin/broadcast', {
        method: 'POST',
        body: JSON.stringify({ text, target }),
      }),
  },
}

export { ApiError }
