import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, ApiError } from '@/lib/api'
import { getTelegramUser, isTelegramWebApp, twa } from '@/lib/telegram'
import type { UserProfile } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isTelegram = isTelegramWebApp()

  const isAuthenticated = computed(() => Boolean(profile.value))
  const user = computed(() => getTelegramUser())
  const hasSubscription = computed(() => profile.value?.has_active_subscription ?? false)
  const subscription = computed(() => profile.value?.subscription ?? null)
  const trialAvailable = computed(() => profile.value?.trial_available ?? false)
  const referralCode = computed(() => profile.value?.referral_code ?? '')

  async function fetchProfile() {
    loading.value = true
    error.value = null
    try {
      profile.value = await api.user.me()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load profile'
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  async function loginByKey(key: string): Promise<{ ok: boolean; error?: string }> {
    try {
      const res = await api.auth.loginByKey(key)
      localStorage.setItem('auth_token', res.token)
      await fetchProfile()
      return { ok: true }
    } catch (e: unknown) {
      const detail = e instanceof ApiError ? e.detail : 'Ошибка входа'
      return { ok: false, error: detail }
    }
  }

  async function loginByTelegram(telegramUser: Record<string, unknown>): Promise<{ ok: boolean; error?: string }> {
    try {
      const res = await api.auth.loginByTelegram(telegramUser)
      localStorage.setItem('auth_token', res.token)
      await fetchProfile()
      return { ok: true }
    } catch (e: unknown) {
      const detail = e instanceof ApiError ? e.detail : 'Ошибка входа через Telegram'
      return { ok: false, error: detail }
    }
  }

  async function generateKey(): Promise<{ ok: boolean; key?: string; error?: string; status?: number }> {
    try {
      const res = await api.auth.generateKey()
      return { ok: true, key: res.key }
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        return { ok: false, error: e.detail, status: e.status }
      }
      return { ok: false, error: 'Ошибка генерации ключа' }
    }
  }

  function logout() {
    localStorage.removeItem('auth_token')
    profile.value = null
  }

  function init() {
    if (isTelegram) {
      twa?.expand()
      twa?.ready()
      twa?.setBackgroundColor('#010101')
      twa?.setHeaderColor('#010101')
    }
    return fetchProfile()
  }

  return {
    profile,
    loading,
    error,
    isAuthenticated,
    isTelegram,
    user,
    hasSubscription,
    subscription,
    trialAvailable,
    referralCode,
    fetchProfile,
    loginByKey,
    loginByTelegram,
    generateKey,
    logout,
    init,
  }
})
