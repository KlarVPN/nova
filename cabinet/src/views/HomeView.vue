<script setup lang="ts">
import { Card, SheetModal, Skeleton, SubscriptionBadge } from '@/components/common'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { hapticError, hapticImpact, hapticSuccess, openLink, twa } from '@/lib/telegram'
import { formatDaysRemaining, formatPrice } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import type { Device } from '@/types'
import { Icon } from '@iconify/vue'
import NumberFlow from '@number-flow/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const subStore = useSubscriptionStore()
const router = useRouter()
const { t } = useI18n()
const { loading, error: toastError, info: toastInfo } = useToast()

const sub = computed(() => auth.subscription)

const statusKey = computed(() => {
  if (auth.loading && !auth.profile) return 'loading'
  if (auth.error && !auth.profile) return 'error'
  if (!auth.hasSubscription || !sub.value) return 'none'
  if (sub.value.status_from_panel === 'EXPIRED') return 'expired'
  if (sub.value.status_from_panel === 'DISABLED') return 'disabled'
  return 'active'
})

const showDevices = ref(false)
const showTrialGate = ref(false)
const trialGateLoading = ref(false)
const trialChannelLink = ref('')

onMounted(() => {
  if (!subStore.plansData) {
    void subStore.fetchPlans()
  }
  if (statusKey.value === 'active') {
    Promise.all([subStore.fetchConnect(), subStore.fetchDevices()])
  }
})

watch(
  () => auth.profile,
  (profile) => {
    if (!profile?.has_active_subscription && !subStore.plansData) {
      void subStore.fetchPlans()
    }
    if (profile?.has_active_subscription && statusKey.value === 'active') {
      if (!subStore.connectInfo) subStore.fetchConnect()
      if (!subStore.devicesData) subStore.fetchDevices()
    }
  },
)

const subscribeFromLabel = computed(() => {
  if (!subStore.activePlans.length) return ''

  const minRub = subStore.activePlans
    .map((plan) => plan.price_rub)
    .filter((price): price is number => price != null)
    .reduce<number | null>((min, price) => (min == null || price < min ? price : min), null)

  if (minRub != null) return `${t('home.from')} ${formatPrice(minRub)}`

  const minStars = subStore.activePlans
    .map((plan) => plan.price_stars)
    .filter((price): price is number => price != null)
    .reduce<number | null>((min, price) => (min == null || price < min ? price : min), null)

  if (minStars != null) return `${t('home.from')} ${minStars} ⭐`
  return ''
})

const currentDeviceIcon = computed(() => {
  const p = String(twa?.platform || '').toLowerCase()
  if (p.includes('ios') || p.includes('macos') || p.includes('mac')) return 'lucide:laptop'
  if (p.includes('android')) return 'lucide:smartphone'
  if (p.includes('web') || p.includes('tdesktop')) return 'lucide:monitor'

  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('android') || ua.includes('iphone')) return 'lucide:smartphone'
  if (ua.includes('ipad')) return 'lucide:tablet'
  if (ua.includes('mac os') || ua.includes('windows') || ua.includes('linux'))
    return 'lucide:monitor'
  return 'lucide:laptop'
})

async function openDevicesModal() {
  hapticImpact('light')
  if (!subStore.devicesData) {
    await subStore.fetchDevices()
  }
  showDevices.value = true
}

function closeDevicesModal() {
  hapticImpact('light')
  showDevices.value = false
}

async function handleDisconnect(hwid: string) {
  hapticImpact('medium')
  const ok = await subStore.disconnectDevice(hwid)
  if (ok) hapticSuccess()
  else hapticError()
}

function platformIcon(platform: string | null): string {
  if (!platform) return 'lucide:smartphone'
  const p = platform.toLowerCase()
  if (p.includes('windows')) return 'lucide:monitor'
  if (p.includes('mac') || p.includes('ios') || p.includes('iphone') || p.includes('ipad'))
    return 'lucide:tablet-smartphone'
  if (p.includes('android')) return 'lucide:smartphone'
  if (p.includes('linux')) return 'lucide:terminal'
  return 'lucide:laptop'
}

function deviceDisplayName(device: Device): string {
  if (device.deviceModel) return device.deviceModel
  if (device.platform) return device.platform
  if (device.userAgent) {
    const ua = device.userAgent
    return ua.length > 32 ? ua.slice(0, 32) + '…' : ua
  }
  return t('devices.unknown')
}

function formatDeviceDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return '—'
  }
}

const deviceCountLabel = computed(() => {
  const d = subStore.devicesData
  if (!d) return null
  if (d.max_devices) return t('devices.countOf', { current: d.current_count, max: d.max_devices })
  return t('devices.countFree', { current: d.current_count })
})

const devicesCurrentCount = computed(() => {
  if (subStore.loadingDevices) return 0
  return subStore.devicesData?.current_count ?? 0
})

const devicesMaxCount = computed(() => {
  if (subStore.loadingDevices) return 0
  return subStore.devicesData?.max_devices ?? 0
})

const devicesUnlimited = computed(() => {
  if (subStore.loadingDevices) return false
  return devicesMaxCount.value === 0
})

function goToPlans() {
  hapticImpact()
  router.push('/plans')
}

async function activateTrial() {
  hapticImpact()
  const dismiss = loading(t('common.loading'))
  const ok = await subStore.activateTrial()
  dismiss()
  if (!ok) toastError(t('home.trialActivateFailed'))
}

async function openTrialGate() {
  hapticImpact()
  trialGateLoading.value = true
  showTrialGate.value = true
  try {
    const status = await api.channel.status()
    trialChannelLink.value = status.channel_link || ''
  } catch {
    toastError(t('home.trialCheckFailed'))
  } finally {
    trialGateLoading.value = false
  }
}

function goToChannel() {
  hapticImpact('light')
  if (!trialChannelLink.value) {
    toastError(t('home.channelLinkUnavailable'))
    return
  }
  openLink(trialChannelLink.value)
}

async function checkChannelAndActivateTrial() {
  hapticImpact('medium')
  trialGateLoading.value = true
  try {
    const status = await api.channel.status()
    trialChannelLink.value = status.channel_link || trialChannelLink.value
    if (!status.subscribed) {
      toastInfo(t('home.trialNeedChannel'))
      return
    }

    showTrialGate.value = false
    await activateTrial()
  } catch {
    toastError(t('home.trialCheckFailed'))
  } finally {
    trialGateLoading.value = false
  }
}

const botUsername = import.meta.env.VITE_BOT_USERNAME
const supportLink = botUsername ? `https://t.me/${botUsername}` : 'https://t.me'

const trafficUsedPct = computed(() => {
  if (!sub.value?.traffic_limit_gb || !sub.value?.traffic_used_gb) return 0
  return Math.min(100, (sub.value.traffic_used_gb / sub.value.traffic_limit_gb) * 100)
})

const trafficBarColor = computed(() => {
  const pct = trafficUsedPct.value
  if (pct >= 80) return 'bg-red-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-green-500'
})

const isUnlimitedTraffic = computed(() => !sub.value?.traffic_limit_gb)
</script>

<template>
  <div
    class="mx-auto flex h-[calc(100dvh-4.5rem)] w-full max-w-5xl flex-col items-center justify-center gap-5 py-6 text-center md:h-[calc(100dvh-2rem)]"
  >
    <Transition name="content-fade" mode="out-in">
      <div :key="statusKey" class="flex h-full w-full flex-col items-center justify-between gap-5">
        <!-- LOADING SKELETON -->
        <template v-if="statusKey === 'loading'">
          <div class="flex flex-col items-center gap-5 pt-6">
            <span class="flex rounded-full bg-neutral-900 p-3">
              <span class="block size-12" />
            </span>
            <div class="flex w-full flex-col items-center gap-2">
              <Skeleton class="h-7 w-32 rounded-none" />
              <Skeleton class="h-4 w-24 rounded-none" />
            </div>
          </div>
          <div class="flex w-full flex-col gap-3">
            <Skeleton class="h-14 w-full rounded-none" />
            <Skeleton class="h-14 w-full rounded-none" />
          </div>
        </template>

        <!-- ERROR -->
        <template v-else-if="statusKey === 'error'">
          <div class="flex flex-col items-center gap-5 pt-6">
            <span class="flex rounded-full bg-neutral-900 p-3">
              <Icon icon="lucide:wifi-off" class="size-12 text-neutral-400" />
            </span>
            <div>
              <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
                {{ t('common.error') }}
              </span>
              <p class="mt-2 text-sm text-neutral-400">{{ auth.error }}</p>
            </div>
          </div>
          <Button
            class="flex h-12 w-full cursor-pointer items-center justify-center gap-3 bg-neutral-900 p-2"
            @click="auth.init()"
          >
            <Icon icon="lucide:refresh-cw" class="size-5 text-neutral-400" />
            <span class="font-sans text-sm font-extrabold text-white uppercase">{{
              t('common.retry')
            }}</span>
          </Button>
        </template>

        <!-- NO SUBSCRIPTION -->
        <template v-else-if="statusKey === 'none'">
          <SubscriptionBadge :type="statusKey" />
          <div class="flex w-full flex-col gap-3">
            <Button class="h-12" @click="goToPlans">
              <Icon icon="lucide:coins" class="size-5 text-black" />
              <span class="text-left font-sans text-base">{{ t('home.subscribe') }}</span>
              <span v-if="subscribeFromLabel" class="ml-auto text-sm font-medium text-black/80">
                {{ subscribeFromLabel }}
              </span>
            </Button>
            <Button
              v-if="auth.trialAvailable"
              class="h-12 bg-neutral-900 text-white"
              :disabled="subStore.processingTrial"
              @click="openTrialGate"
            >
              <Icon icon="lucide:gift" class="size-5" />
              <span class="text-left font-sans text-base">{{ t('home.trialBtn') }}</span>
            </Button>
          </div>
        </template>

        <!-- EXPIRED -->
        <template v-else-if="statusKey === 'expired'">
          <SubscriptionBadge :type="statusKey" />
          <Button
            class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black"
            @click="goToPlans"
          >
            <span class="flex bg-black p-2">
              <Icon icon="lucide:shield" class="size-5 text-white" />
            </span>
            <span class="flex flex-col items-start">
              <span class="text-left font-sans text-sm leading-4 font-bold uppercase">{{
                t('home.renewSub')
              }}</span>
            </span>
          </Button>
        </template>

        <!-- DISABLED -->
        <template v-else-if="statusKey === 'disabled'">
          <SubscriptionBadge :type="statusKey" />

          <a
            :href="supportLink"
            target="_blank"
            class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black no-underline"
          >
            <span class="flex bg-black p-2">
              <Icon icon="lucide:message-circle" class="size-5 text-white" />
            </span>
            <span class="flex flex-col items-start">
              <span class="text-left font-sans text-sm leading-4 font-bold uppercase">{{
                t('profile.support')
              }}</span>
            </span>
          </a>
        </template>

        <!-- ACTIVE -->
        <template v-else-if="statusKey === 'active' && sub">
          <SubscriptionBadge :type="statusKey" :sub="sub" />

          <!-- Data Cards -->
          <div class="flex w-full flex-col gap-5">
            <div class="flex w-full flex-col gap-3">
              <div class="flex items-center gap-3">
                <!-- Expires / Days remaining -->
                <Card class="h-18">
                  <span class="flex items-center gap-2 text-sm">
                    <Icon icon="lucide:calendar" class="size-4" />
                    {{ t('home.expires') }}
                  </span>
                  <span class="text-left font-medium text-white">
                    {{ formatDaysRemaining(sub.days_remaining) }}
                  </span>
                </Card>

                <!-- Devices -->
                <Card @click="openDevicesModal" class="h-18 cursor-pointer">
                  <span class="flex items-center gap-2 text-sm">
                    <Icon icon="lucide:monitor-smartphone" class="size-4" />
                    {{ t('devices.title') }}
                    <Icon icon="lucide:chevron-right" class="size-3" />
                  </span>
                  <div class="flex items-center justify-between">
                    <span class="flex items-center gap-1 font-medium text-white">
                      <NumberFlow :value="devicesCurrentCount" />
                      <span class="text-white/50">/</span>
                      <span v-if="devicesUnlimited" class="text-white/50">∞</span>
                      <NumberFlow v-else :value="devicesMaxCount" class="text-white/50" />
                    </span>
                  </div>
                </Card>
              </div>
              <!-- Traffic -->
              <Card>
                <span class="flex items-center gap-2 text-sm">
                  <Icon icon="lucide:activity" class="size-4" />
                  {{ t('home.traffic') }}
                </span>
                <template v-if="isUnlimitedTraffic">
                  <div class="flex items-center justify-between">
                    <span class="font-medium text-white">{{ t('plans.unlimitedTraffic') }}</span>
                    <span class="text-xs text-neutral-500">∞</span>
                  </div>
                  <div class="h-1 w-full overflow-hidden rounded-full bg-neutral-800">
                    <div
                      class="h-full w-full rounded-full bg-green-500 transition-all duration-500"
                    />
                  </div>
                </template>
                <template v-else>
                  <div class="flex items-center justify-between">
                    <span class="font-medium text-white">
                      {{ sub.traffic_used_gb?.toFixed(1) ?? '0' }} /
                      {{ sub.traffic_limit_gb?.toFixed(0) ?? '0' }} GB
                    </span>
                    <span class="text-xs text-neutral-500">
                      {{ (100 - (sub.traffic_remaining_pct ?? 0)).toFixed(0) }}%
                    </span>
                  </div>
                  <div class="h-1 w-full overflow-hidden rounded-full bg-neutral-800">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      :class="trafficBarColor"
                      :style="{ width: trafficUsedPct + '%' }"
                    />
                  </div>
                </template>
              </Card>
            </div>

            <!-- Action Buttons -->
            <div class="flex w-full flex-col gap-3">
              <div class="flex w-full items-center gap-2">
                <Button
                  :disabled="subStore.loadingConnect || !subStore.connectInfo"
                  @click="router.push({ name: 'setup' })"
                >
                  <Icon icon="lucide:plug-zap" class="size-5" />
                  {{ t('home.connect') }}
                  <Icon icon="lucide:chevron-right" class="ml-auto size-5 text-black/40" />
                </Button>
              </div>
              <Button class="bg-neutral-900 text-white hover:bg-neutral-800" @click="goToPlans">
                <Icon icon="lucide:refresh-cw" class="size-5" />
                {{ t('home.renewSub') }}
                <span v-if="subscribeFromLabel" class="ml-auto text-sm font-medium text-white/40">
                  {{ subscribeFromLabel }}
                </span>
              </Button>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </div>

  <!-- Device Management Bottom Sheet -->
  <SheetModal
    :model-value="showDevices"
    desktop-position="end"
    show-handle
    panel-class="flex max-h-[90vh] flex-col bg-[#0a0a0a] md:w-full md:max-w-2xl md:rounded-2xl md:shadow-2xl"
    overlay-class="bg-black/70 backdrop-blur-sm"
    @close="closeDevicesModal"
  >
    <div class="flex items-center justify-between px-4 py-3">
      <div>
        <h2 class="text-base font-medium text-white">
          {{ t('devices.manage') }}
        </h2>
        <p v-if="deviceCountLabel" class="mt-0.5 text-xs text-neutral-400">
          {{ deviceCountLabel }}
        </p>
      </div>
    </div>
    <div class="h-px bg-neutral-900" />
    <div class="flex-1 overflow-y-auto p-4">
      <div
        v-if="subStore.loadingDevices"
        class="flex flex-col items-center gap-3 py-10 text-neutral-400"
      >
        <Icon icon="lucide:loader-circle" class="size-8 animate-spin" />
        <span class="text-sm">{{ t('devices.loading') }}</span>
      </div>
      <div
        v-else-if="!subStore.devicesData?.devices?.length"
        class="flex flex-col items-center gap-3 rounded-[14px] py-10 text-neutral-400"
      >
        <Icon icon="lucide:monitor-smartphone" class="size-10" />
        <span class="text-sm">{{ t('devices.noDevices') }}</span>
      </div>
      <div v-else class="flex flex-col gap-2">
        <div
          v-for="device in subStore.devicesData.devices"
          :key="device.hwid"
          class="flex items-start gap-3 rounded-[14px] bg-neutral-950 px-4 py-3"
        >
          <div
            class="flex size-9 shrink-0 items-center justify-center rounded-[14px] bg-neutral-900"
          >
            <Icon :icon="platformIcon(device.platform)" class="size-4 text-neutral-300" />
          </div>
          <div class="flex min-w-0 flex-1 flex-col gap-px">
            <p class="truncate font-sans text-sm leading-tight font-semibold text-white">
              {{ deviceDisplayName(device) }}
            </p>
            <p class="text-xs text-neutral-500">
              <template v-if="device.platform">
                {{ device.platform
                }}<template v-if="device.osVersion"> {{ device.osVersion }}</template>
              </template>
            </p>
            <p class="text-xs text-neutral-500">
              {{ t('devices.firstSeen') }} {{ formatDeviceDate(device.createdAt) }}
            </p>
          </div>
          <button
            class="flex shrink-0 cursor-pointer items-center justify-center rounded-[14px] bg-red-950 px-2 py-1.5 text-xs font-semibold text-red-400 uppercase transition-opacity active:opacity-50 disabled:cursor-not-allowed disabled:opacity-30"
            :disabled="subStore.disconnectingHwid === device.hwid"
            @click="handleDisconnect(device.hwid)"
          >
            <Icon
              v-if="subStore.disconnectingHwid === device.hwid"
              icon="lucide:loader-circle"
              class="size-3.5 animate-spin"
            />
            <template v-else>{{ t('devices.disconnect') }}</template>
          </button>
        </div>
      </div>
    </div>
    <div class="md:hidden" style="height: max(env(safe-area-inset-bottom), 12px)" />
  </SheetModal>

  <SheetModal
    v-model="showTrialGate"
    desktop-position="end"
    :show-handle="true"
    panel-class="mx-3 rounded-2xl border border-neutral-800 bg-neutral-950 p-4 md:mx-0 md:w-full md:max-w-md"
  >
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Icon icon="lucide:gift" class="size-5 text-white" />
        <p class="text-base font-semibold text-white">{{ t('home.trialModalTitle') }}</p>
      </div>
      <p class="text-sm text-neutral-400">{{ t('home.trialModalDesc') }}</p>

      <Button class="h-11" :disabled="trialGateLoading" @click="goToChannel">
        <Icon icon="lucide:external-link" class="size-4 text-black" />
        <span>{{ t('home.goToChannel') }}</span>
      </Button>

      <Button
        class="h-11 bg-neutral-900 text-white"
        :disabled="trialGateLoading || subStore.processingTrial"
        @click="checkChannelAndActivateTrial"
      >
        <Icon
          :icon="trialGateLoading ? 'lucide:loader-circle' : 'lucide:badge-check'"
          class="size-4"
          :class="trialGateLoading ? 'animate-spin' : ''"
        />
        <span>{{ t('home.checkSubscription') }}</span>
      </Button>
    </div>
  </SheetModal>
</template>

<style scoped>
.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 220ms ease;
}

.content-fade-enter-from,
.content-fade-leave-to {
  opacity: 0;
}
</style>
