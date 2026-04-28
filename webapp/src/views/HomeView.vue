<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { formatDateE, formatDaysRemaining } from '@/lib/utils'
import { hapticImpact, hapticSuccess, hapticError, openLink } from '@/lib/telegram'
import type { Device } from '@/types'

const auth = useAuthStore()
const subStore = useSubscriptionStore()
const router = useRouter()
const { t } = useI18n()

const sub = computed(() => auth.subscription)

const statusKey = computed(() => {
  if (!auth.hasSubscription || !sub.value) return 'none'
  if (sub.value.status_from_panel === 'EXPIRED') return 'expired'
  if (sub.value.status_from_panel === 'DISABLED') return 'disabled'
  return 'active'
})

const showDevices = ref(false)

onMounted(async () => {
  if (auth.hasSubscription && statusKey.value === 'active') {
    await Promise.all([subStore.fetchConnect(), subStore.fetchDevices()])
  }
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

function goToPlans() {
  hapticImpact()
  router.push('/plans')
}

async function activateTrial() {
  hapticImpact()
  await subStore.activateTrial()
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
</script>

<template>
  <div class="flex h-full w-full flex-col items-center justify-center gap-5 pt-2 text-center">
    <!-- NO SUBSCRIPTION -->
    <template v-if="statusKey === 'none'">
      <div class="flex flex-col items-center gap-5 pt-6">
        <span class="flex rounded-full bg-white p-3">
          <Icon icon="lucide:shield-off" class="size-12 text-black" />
        </span>
        <div>
          <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
            {{ t('home.noSubTitle') }}
          </span>
          <p class="mt-2 text-sm text-neutral-400">{{ t('home.noSub') }}</p>
        </div>
      </div>
      <div class="flex w-full flex-col gap-3">
        <button
          v-if="auth.trialAvailable"
          class="flex h-12 w-full cursor-pointer items-center justify-center gap-3 border border-neutral-800 bg-neutral-900 p-2"
          :disabled="subStore.processingTrial"
          @click="activateTrial"
        >
          <Icon icon="lucide:gift" class="size-5 text-neutral-400" />
          <span class="text-left font-sans text-sm leading-4 font-extrabold text-white uppercase">{{
            t('home.trialBtn')
          }}</span>
        </button>
        <button
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
        </button>
      </div>
    </template>

    <!-- EXPIRED -->
    <template v-else-if="statusKey === 'expired'">
      <div class="flex flex-col items-center gap-5 pt-6">
        <span class="flex rounded-full bg-white p-3">
          <Icon icon="lucide:clock-alert" class="size-12 text-black" />
        </span>
        <div>
          <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
            {{ t('status.expired') }}
          </span>
          <p class="mt-2 text-sm text-neutral-400">{{ t('home.expiredDesc') }}</p>
        </div>
      </div>
      <button
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
      </button>
    </template>

    <!-- DISABLED -->
    <template v-else-if="statusKey === 'disabled'">
      <div class="flex flex-col items-center gap-5 pt-6">
        <span class="flex rounded-full bg-white p-3">
          <Icon icon="lucide:ban" class="size-12 text-black" />
        </span>

        <div>
          <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
            {{ t('status.disabled') }}
          </span>
          <p class="mt-2 text-sm text-neutral-400">{{ t('home.disabledDesc') }}</p>
        </div>
      </div>
      <a
        :href="supportLink"
        target="_blank"
        class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black no-underline"
      >
        <span class="flex bg-black p-2">
          <Icon icon="lucide:message-circle" class="size-5 text-white" />
        </span>
        <span class="flex flex-col items-start">
          <span class="text-left font-sans text-sm leading-4 font-bold uppercase">Поддержка</span>
        </span>
      </a>
    </template>

    <!-- ACTIVE -->
    <template v-else-if="statusKey === 'active' && sub">
      <div class="flex flex-col items-center gap-5 pt-4">
        <span class="flex rounded-full bg-primary p-3">
          <Icon icon="lucide:check" class="size-12 text-black" />
        </span>
        <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
          {{ t('status.active') }}
        </span>
      </div>

      <!-- Data Cards -->
      <div class="flex w-full flex-col gap-3">
        <!-- Expires -->
        <div
          class="flex w-full flex-col gap-2 border border-neutral-800 bg-neutral-950 px-4 py-2 text-neutral-400"
        >
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:calendar" class="size-4" />
            {{ t('home.expires') }}
          </span>
          <div class="flex items-center gap-2">
            <span class="text-left font-mono font-medium text-white">
              {{ formatDateE(sub.end_date) }}
            </span>
            <span class="text-left font-mono font-medium text-white/50">
              ({{ formatDaysRemaining(sub.days_remaining) }})
            </span>
          </div>
        </div>
        <!-- Traffic -->
        <div
          v-if="sub.traffic_limit_gb"
          class="flex w-full flex-col gap-2 border border-neutral-800 bg-neutral-950 px-4 py-2 text-neutral-400"
        >
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:activity" class="size-4" />
            {{ t('home.traffic') }}
          </span>
          <div class="flex items-center justify-between">
            <span class="font-mono font-medium text-white">
              {{ sub.traffic_used_gb?.toFixed(1) ?? '0' }} /
              {{ sub.traffic_limit_gb?.toFixed(0) }} GB
            </span>
            <span class="font-mono text-xs text-neutral-500">
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
        </div>

        <div
          v-if="subStore.connectInfo?.connect_url"
          class="flex w-full flex-col gap-2 border border-neutral-800 bg-neutral-950 px-4 py-2 text-neutral-400"
        >
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:link" class="size-4" />
            {{ t('home.subLink') }}
          </span>
          <span class="text-left font-mono font-medium text-white">
            {{ subStore.connectInfo?.connect_url }}
          </span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex w-full flex-col gap-3">
        <div class="flex w-full items-center gap-2">
          <button
            class="flex h-14 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black"
            :disabled="subStore.loadingConnect || !subStore.connectInfo"
            @click="router.push({ name: 'configs' })"
          >
            <span class="flex bg-black p-2">
              <Icon icon="lucide:monitor-smartphone" class="size-5 text-white" />
            </span>
            <span class="flex flex-col items-start">
              <span class="text-left font-sans text-sm leading-4 font-bold uppercase">
                {{ t('home.connect') }}
              </span>
              <span class="text-left text-sm leading-4"
                >{{ deviceCountLabel }} из - подключено</span
              >
            </span>
          </button>
          <button
            class="flex h-14 cursor-pointer items-center justify-center gap-3 border border-neutral-800 bg-neutral-900 p-2"
            @click="openDevicesModal"
          >
            <span class="text-left font-sans text-sm leading-4 font-extrabold uppercase">
              {{ t('devices.title') }}
            </span>

            <span class="flex bg-white p-2">
              <Icon icon="lucide:monitor-cog" class="size-5 text-black" />
            </span>
          </button>
        </div>
        <button
          class="flex h-12 w-full cursor-pointer items-center justify-center gap-3 border border-neutral-800 bg-neutral-900 p-2"
          @click="goToPlans"
        >
          <span class="text-left font-sans text-sm leading-4 font-extrabold text-white uppercase">{{
            t('home.changePlan')
          }}</span>
        </button>
      </div>
    </template>
  </div>

  <!-- Device Management Bottom Sheet -->
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="showDevices" class="fixed inset-0 z-50 flex flex-col justify-end">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeDevicesModal" />

        <!-- Sheet panel -->
        <div
          class="sheet-panel relative flex max-h-[82vh] flex-col border-t border-white/10 bg-[#0a0a0a]"
        >
          <!-- Handle bar -->
          <div class="flex justify-center pt-3 pb-1">
            <div class="h-1 w-10 rounded-full bg-neutral-700" />
          </div>

          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <h2 class="font-mono text-base font-bold text-white uppercase">
                {{ t('devices.manage') }}
              </h2>
              <p v-if="deviceCountLabel" class="mt-0.5 font-mono text-xs text-neutral-400">
                {{ deviceCountLabel }}
              </p>
            </div>
            <button
              class="flex size-8 cursor-pointer items-center justify-center border border-neutral-800 text-neutral-400 transition-opacity active:opacity-70"
              @click="closeDevicesModal"
            >
              <Icon icon="lucide:x" class="size-4" />
            </button>
          </div>

          <div class="h-px bg-neutral-900" />

          <!-- Content -->
          <div class="flex-1 overflow-y-auto p-4">
            <!-- Loading -->
            <div
              v-if="subStore.loadingDevices"
              class="flex flex-col items-center gap-3 py-10 text-neutral-400"
            >
              <Icon icon="lucide:loader-circle" class="size-8 animate-spin" />
              <span class="font-mono text-sm">{{ t('devices.loading') }}</span>
            </div>

            <!-- Empty -->
            <div
              v-else-if="!subStore.devicesData?.devices?.length"
              class="flex flex-col items-center gap-3 py-10 text-neutral-400"
            >
              <Icon icon="lucide:monitor-smartphone" class="size-10" />
              <span class="font-mono text-sm">{{ t('devices.noDevices') }}</span>
            </div>

            <!-- Device list -->
            <div v-else class="flex flex-col gap-2">
              <div
                v-for="device in subStore.devicesData.devices"
                :key="device.hwid"
                class="flex items-start gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3"
              >
                <!-- Platform icon -->
                <div
                  class="flex size-9 shrink-0 items-center justify-center border border-neutral-800 bg-neutral-900"
                >
                  <Icon :icon="platformIcon(device.platform)" class="size-4 text-neutral-300" />
                </div>

                <!-- Info -->
                <div class="flex min-w-0 flex-1 flex-col gap-px">
                  <p class="truncate font-sans text-sm leading-tight font-semibold text-white">
                    {{ deviceDisplayName(device) }}
                  </p>
                  <p class="font-mono text-xs text-neutral-500">
                    <template v-if="device.platform"
                      >{{ device.platform
                      }}<template v-if="device.osVersion">
                        {{ device.osVersion }}</template
                      ></template
                    >
                  </p>
                  <p class="font-mono text-xs text-neutral-500">
                    {{ t('devices.firstSeen') }} {{ formatDeviceDate(device.createdAt) }}
                  </p>
                </div>

                <!-- Disconnect button -->
                <button
                  class="flex shrink-0 cursor-pointer items-center justify-center border border-red-700 bg-red-950 px-2 py-1.5 font-mono text-xs font-semibold text-red-400 uppercase transition-opacity active:opacity-50 disabled:cursor-not-allowed disabled:opacity-30"
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

          <!-- Safe area bottom padding -->
          <div style="height: max(env(safe-area-inset-bottom), 12px)" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
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
