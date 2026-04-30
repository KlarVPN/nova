import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, ApiError } from '@/lib/api'
import { getTelegramUser, isTelegramWebApp, twa } from '@/lib/telegram'
import type { UserProfile } from '@/types'

type CachedTelegramUser = {
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
}

export const useAuthStore = defineStore('auth', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const telegramPhotoUrl = ref<string>(localStorage.getItem('tg_photo_url') ?? '')
  const telegramUserCache = ref<CachedTelegramUser>({})

  const isTelegram = isTelegramWebApp()

  const isAuthenticated = computed(() => Boolean(profile.value))
  const user = computed(() => getTelegramUser())
  const hasSubscription = computed(() => profile.value?.has_active_subscription ?? false)
  const subscription = computed(() => profile.value?.subscription ?? null)
  const trialAvailable = computed(() => profile.value?.trial_available ?? false)
  const referralCode = computed(() => profile.value?.referral_code ?? '')

  function loadCachedTelegramUser() {
    try {
      const raw = localStorage.getItem('tg_user_cache')
      telegramUserCache.value = raw ? (JSON.parse(raw) as CachedTelegramUser) : {}
    } catch {
      telegramUserCache.value = {}
    }
  }

  function persistCachedTelegramUser(payload: CachedTelegramUser) {
    telegramUserCache.value = payload
    localStorage.setItem('tg_user_cache', JSON.stringify(payload))
  }

  function syncTelegramPhotoFromMiniApp() {
    const tgUser = getTelegramUser()
    if (!tgUser) return

    persistCachedTelegramUser({
      first_name: tgUser.first_name,
      last_name: tgUser.last_name,
      username: tgUser.username,
      photo_url: tgUser.photo_url,
    })

    const photoUrl = tgUser.photo_url
    if (!photoUrl) return
    telegramPhotoUrl.value = photoUrl
    localStorage.setItem('tg_photo_url', photoUrl)
  }

  async function fetchProfile() {
    loading.value = true
    error.value = null
    syncTelegramPhotoFromMiniApp()
    try {
      profile.value = await api.user.me()
      if (profile.value?.photo_url) {
        telegramPhotoUrl.value = profile.value.photo_url
        localStorage.setItem('tg_photo_url', profile.value.photo_url)
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load profile'
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  async function loginByTelegram(telegramUser: Record<string, unknown>): Promise<{ ok: boolean; error?: string }> {
    try {
      const photoUrl = typeof telegramUser.photo_url === 'string' ? telegramUser.photo_url : ''
      if (photoUrl) {
        telegramPhotoUrl.value = photoUrl
        localStorage.setItem('tg_photo_url', photoUrl)
      }

      const res = await api.auth.loginByTelegram(telegramUser)
      localStorage.setItem('auth_token', res.token)
      await fetchProfile()
      return { ok: true }
    } catch (e: unknown) {
      const detail = e instanceof ApiError ? e.detail : 'Ошибка входа через Telegram'
      return { ok: false, error: detail }
    }
  }

  function logout() {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('tg_photo_url')
    localStorage.removeItem('tg_user_cache')
    telegramPhotoUrl.value = ''
    telegramUserCache.value = {}
    profile.value = null
  }

  function init() {
    loadCachedTelegramUser()
    if (isTelegram) {
      twa?.expand()
      twa?.ready()
      twa?.setBackgroundColor('#010101')
      twa?.setHeaderColor('#010101')
      syncTelegramPhotoFromMiniApp()
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
    telegramPhotoUrl,
    telegramUserCache,
    fetchProfile,
    loginByTelegram,
    logout,
    init,
  }
})
