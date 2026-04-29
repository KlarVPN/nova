<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { formatDaysRemaining } from '@/lib/utils'
import { Card } from '@/components/common'
import { hapticImpact, hapticSuccess, hapticError } from '@/lib/telegram'
import type { Device } from '@/types'
import { Button } from '@/components/ui/button'
import SubscriptionBadge from '@/components/common/SubscriptionBadge.vue'
import { useToast } from '@/components/ui/toast'

const auth = useAuthStore()
const subStore = useSubscriptionStore()
const router = useRouter()
const { t } = useI18n()
const { loading } = useToast()

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

onMounted(() => {
  if (statusKey.value === 'active') {
    Promise.all([subStore.fetchConnect(), subStore.fetchDevices()])
  }
})

watch(
  () => auth.profile,
  (profile) => {
    if (profile?.has_active_subscription && statusKey.value === 'active') {
      if (!subStore.connectInfo) subStore.fetchConnect()
      if (!subStore.devicesData) subStore.fetchDevices()
    }
  },
)

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

function goToPlans() {
  hapticImpact()
  router.push('/plans')
}

async function activateTrial() {
  hapticImpact()
  const dismiss = loading(t('common.loading'))
  await subStore.activateTrial()
  dismiss()
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
    class="flex min-h-[calc(100dvh-4.75rem)] w-full flex-col items-center justify-center gap-5 text-center"
  >
    <Transition name="content-fade" mode="out-in">
      <div :key="statusKey" class="flex w-full flex-col items-center justify-center gap-5">
        <!-- LOADING SKELETON -->
        <template v-if="statusKey === 'loading'">
          <div class="flex flex-col items-center gap-5 pt-6">
            <span class="flex animate-pulse rounded-full bg-neutral-900 p-3">
              <span class="block size-12" />
            </span>
            <div class="flex w-full flex-col items-center gap-2">
              <div class="h-7 w-32 animate-pulse bg-neutral-900" />
              <div class="h-4 w-24 animate-pulse bg-neutral-900" />
            </div>
          </div>
          <div class="flex w-full flex-col gap-3">
            <div class="h-14 w-full animate-pulse border border-neutral-800 bg-neutral-900" />
            <div class="h-14 w-full animate-pulse border border-neutral-800 bg-neutral-900" />
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
            class="flex h-12 w-full cursor-pointer items-center justify-center gap-3 border border-neutral-800 bg-neutral-900 p-2"
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
            <Button
              v-if="auth.trialAvailable"
              class="flex h-12 w-full cursor-pointer items-center justify-center gap-3 border border-neutral-800 bg-neutral-900 p-2"
              :disabled="subStore.processingTrial"
              @click="activateTrial"
            >
              <Icon icon="lucide:gift" class="size-5 text-neutral-400" />
              <span
                class="text-left font-sans text-sm leading-4 font-extrabold text-white uppercase"
                >{{ t('home.trialBtn') }}</span
              >
            </Button>
            <Button
              class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black"
              @click="goToPlans"
            >
              <span class="flex bg-black p-2">
                <Icon icon="lucide:shield" class="size-5 text-white" />
              </span>
              <span class="flex flex-col items-start">
                <span class="text-left font-sans text-sm leading-4 font-bold uppercase">{{
                  t('home.subscribe')
                }}</span>
              </span>
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
                <div v-if="subStore.loadingDevices" class="flex items-center gap-2">
                  <Icon icon="lucide:loader-circle" class="size-4 animate-spin text-neutral-400" />
                </div>
                <div v-else-if="subStore.devicesData" class="flex items-center justify-between">
                  <span class="font-medium text-white">
                    {{ subStore.devicesData.current_count }}
                    <span class="text-white/50">
                      / {{ subStore.devicesData.max_devices ?? '∞' }}
                    </span>
                  </span>
                </div>
                <div v-else class="text-sm text-neutral-500">—</div>
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
                {{ t('home.connect') }}
                <Icon icon="lucide:chevron-right" class="size-4" />
              </Button>
            </div>
            <Button class="bg-neutral-900 text-white hover:bg-neutral-800" @click="goToPlans">
              {{ t('home.renewSub') }}
            </Button>
          </div>
        </template>
      </div>
    </Transition>
  </div>

  <!-- Device Management Bottom Sheet -->
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="showDevices" class="fixed inset-0 z-50 flex flex-col justify-end">
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeDevicesModal" />
        <div
          class="sheet-panel relative flex max-h-[90vh] flex-col border-t border-white/10 bg-[#0a0a0a]"
        >
          <div class="flex justify-center pt-3 pb-1">
            <div class="h-1 w-10 rounded-full bg-neutral-700" />
          </div>
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
                class="flex items-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 py-3"
              >
                <div
                  class="flex size-9 shrink-0 items-center justify-center rounded-[14px] border border-neutral-800 bg-neutral-900"
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
                  class="flex shrink-0 cursor-pointer items-center justify-center rounded-[14px] border border-red-700 bg-red-950 px-2 py-1.5 text-xs font-semibold text-red-400 uppercase transition-opacity active:opacity-50 disabled:cursor-not-allowed disabled:opacity-30"
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
          <div style="height: max(env(safe-area-inset-bottom), 12px)" />
        </div>
      </div>
    </Transition>
  </Teleport>
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

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;
}
.sheet-enter-active .sheet-panel,
.sheet-leave-active .sheet-panel {
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet-panel,
.sheet-leave-to .sheet-panel {
  transform: translateY(100%);
}
</style>
