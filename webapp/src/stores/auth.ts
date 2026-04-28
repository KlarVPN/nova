import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import { getTelegramUser, twa } from '@/lib/telegram'
import type { UserProfile } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

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
    } finally {
      loading.value = false
    }
  }

  function init() {
    twa?.expand()
    twa?.ready()
    twa?.setBackgroundColor('#010101')
    twa?.setHeaderColor('#010101')
    return fetchProfile()
  }

  return {
    profile,
    loading,
    error,
    isAuthenticated,
    user,
    hasSubscription,
    subscription,
    trialAvailable,
    referralCode,
    fetchProfile,
    init,
  }
})
