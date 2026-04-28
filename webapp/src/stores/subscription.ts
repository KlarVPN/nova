import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'
import type { PlansData, ReferralData, PaymentResult, PaymentProvider, DevicesData } from '@/types'
import { hapticSuccess, hapticError, openInvoice, openLink } from '@/lib/telegram'
import { useAuthStore } from './auth'

export const useSubscriptionStore = defineStore('subscription', () => {
  const plansData = ref<PlansData | null>(null)
  const referralData = ref<ReferralData | null>(null)
  const connectInfo = ref<{ connect_url: string; config_link: string } | null>(null)

  const devicesData = ref<DevicesData | null>(null)

  const loadingPlans = ref(false)
  const loadingReferral = ref(false)
  const loadingConnect = ref(false)
  const loadingDevices = ref(false)
  const disconnectingHwid = ref<string | null>(null)
  const processingPayment = ref(false)
  const processingTrial = ref(false)

  const activePlans = computed(() =>
    (plansData.value?.plans ?? []).filter((p) => p.enabled && (p.price_rub !== null || p.price_stars !== null)),
  )
  const activeTrafficPackages = computed(
    () => (plansData.value?.traffic_packages ?? []).filter((p) => p.price_rub !== null || p.price_stars !== null),
  )
  const isTrafficMode = computed(() => plansData.value?.traffic_sale_mode ?? false)
  const availableProviders = computed(() => plansData.value?.payment_methods ?? [])
  const activeDiscount = computed(() => plansData.value?.active_discount ?? null)

  async function fetchPlans() {
    loadingPlans.value = true
    try {
      plansData.value = await api.plans.list()
    } finally {
      loadingPlans.value = false
    }
  }

  async function fetchReferral() {
    loadingReferral.value = true
    try {
      referralData.value = await api.referral.info()
    } finally {
      loadingReferral.value = false
    }
  }

  async function fetchDevices() {
    loadingDevices.value = true
    try {
      devicesData.value = await api.devices.list()
    } catch {
      devicesData.value = null
    } finally {
      loadingDevices.value = false
    }
  }

  async function disconnectDevice(hwid: string): Promise<boolean> {
    disconnectingHwid.value = hwid
    try {
      const result = await api.devices.disconnect(hwid)
      if (result.success && devicesData.value) {
        devicesData.value.devices = devicesData.value.devices.filter(d => d.hwid !== hwid)
        devicesData.value.current_count = devicesData.value.devices.length
      }
      return result.success
    } catch {
      return false
    } finally {
      disconnectingHwid.value = null
    }
  }

  async function fetchConnect() {
    if (!useAuthStore().hasSubscription) return
    loadingConnect.value = true
    try {
      connectInfo.value = await api.subscription.connect()
    } finally {
      loadingConnect.value = false
    }
  }

  async function createPayment(
    params: { months?: number; gb?: number },
    provider: PaymentProvider,
  ): Promise<PaymentResult | null> {
    processingPayment.value = true
    try {
      const result = await api.payment.create({ ...params, provider })
      if (provider === 'stars' && result.invoice_link) {
        openInvoice(result.invoice_link, (status) => {
          if (status === 'paid') {
            hapticSuccess()
            useAuthStore().fetchProfile()
          } else if (status === 'failed' || status === 'cancelled') {
            hapticError()
          }
        })
      } else if (result.payment_url) {
        openLink(result.payment_url)
      }
      return result
    } catch {
      hapticError()
      return null
    } finally {
      processingPayment.value = false
    }
  }

  async function activateTrial(): Promise<boolean> {
    processingTrial.value = true
    try {
      const res = await api.payment.trial()
      if (res.success) {
        hapticSuccess()
        await useAuthStore().fetchProfile()
        return true
      }
      return false
    } catch {
      hapticError()
      return false
    } finally {
      processingTrial.value = false
    }
  }

  return {
    plansData,
    referralData,
    connectInfo,
    devicesData,
    loadingPlans,
    loadingReferral,
    loadingConnect,
    loadingDevices,
    disconnectingHwid,
    processingPayment,
    processingTrial,
    activePlans,
    activeTrafficPackages,
    isTrafficMode,
    availableProviders,
    activeDiscount,
    fetchPlans,
    fetchReferral,
    fetchConnect,
    fetchDevices,
    disconnectDevice,
    createPayment,
    activateTrial,
  }
})
