<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import confetti from 'canvas-confetti'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { Button } from '@/components/ui/button'
import { SheetModal } from '@/components/common'
import { hapticImpact } from '@/lib/telegram'

type SetupOS = 'ios' | 'android' | 'macos' | 'linux' | 'windows' | 'other'
type SetupStep = 0 | 1 | 2 | 3

const router = useRouter()
const { t } = useI18n()
const auth = useAuthStore()
const subStore = useSubscriptionStore()

const step = ref<SetupStep>(0)
const os = ref<SetupOS>('other')
const animatedProgress = ref(0)
const showInstallWarning = ref(false)
const progressRingRef = ref<HTMLElement | null>(null)
const pulseOrigin = ref({ x: '50%', y: '50%' })
let progressFrame: number | null = null

const connectUrl = computed(() => subStore.connectInfo?.connect_url ?? '')

const osLabel = computed(() => {
  if (os.value === 'ios') return 'iOS'
  if (os.value === 'android') return 'Android'
  if (os.value === 'macos') return 'macOS'
  if (os.value === 'linux') return 'Linux'
  if (os.value === 'windows') return 'Windows'
  return t('setup.wizard.os.currentDevice')
})

const pageTitle = computed(() => {
  if (step.value === 0) return t('setup.wizard.title.device', { os: osLabel.value })
  if (step.value === 1) return t('setup.wizard.title.app')
  if (step.value === 2) return t('setup.wizard.title.subscription')
  return t('setup.wizard.title.done')
})

const pageSubtitle = computed(() => {
  if (step.value === 0) return t('setup.wizard.subtitle.device')
  if (step.value === 1) return t('setup.wizard.subtitle.app', { os: osLabel.value })
  if (step.value === 2) return t('setup.wizard.subtitle.subscription')
  return t('setup.wizard.subtitle.done')
})

const progressPercent = computed(() => {
  if (step.value === 0) return 0
  if (step.value === 1) return 33
  if (step.value === 2) return 66
  return 100
})

function animateProgressTo(target: number) {
  if (progressFrame) {
    window.cancelAnimationFrame(progressFrame)
    progressFrame = null
  }

  const startValue = animatedProgress.value
  const delta = target - startValue
  if (Math.abs(delta) < 0.1) {
    animatedProgress.value = target
    return
  }

  const duration = 520
  const startTime = performance.now()

  const tick = (now: number) => {
    const t = Math.min(1, (now - startTime) / duration)
    const eased = 1 - Math.pow(1 - t, 3)
    animatedProgress.value = startValue + delta * eased
    if (t < 1) {
      progressFrame = window.requestAnimationFrame(tick)
    } else {
      progressFrame = null
    }
  }

  progressFrame = window.requestAnimationFrame(tick)
}

const circleStyle = computed(() => ({
  background: `conic-gradient(#bdfe00 ${animatedProgress.value}%, #232323 ${animatedProgress.value}% 100%)`,
}))

const screenPulseStyle = computed(() => ({
  '--pulse-x': pulseOrigin.value.x,
  '--pulse-y': pulseOrigin.value.y,
}))

function syncPulseOrigin() {
  const el = progressRingRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  pulseOrigin.value = {
    x: `${rect.left + rect.width / 2}px`,
    y: `${rect.top + rect.height / 2}px`,
  }
}

const centerIcon = computed(() => {
  if (step.value === 0) return 'lucide:power'
  if (step.value === 1) return 'lucide:download'
  if (step.value === 2) return 'lucide:plus'
  return 'lucide:check'
})

const installUrl = computed(() => {
  const links = auth.profile?.links
  if (!links) return ''
  if (os.value === 'ios') return links.instruction_ios
  if (os.value === 'android') return links.instruction_android
  if (os.value === 'macos') return links.instruction_macos
  if (os.value === 'linux') return links.instruction_linux
  if (os.value === 'windows') return links.instruction_windows
  return links.docs
})

function detectOS(): SetupOS {
  const ua = navigator.userAgent.toLowerCase()
  if (/iphone|ipad|ipod/.test(ua)) return 'ios'
  if (/android/.test(ua)) return 'android'
  if (/macintosh|mac os x/.test(ua)) return 'macos'
  if (/linux/.test(ua)) return 'linux'
  if (/windows/.test(ua)) return 'windows'
  return 'other'
}

function openInstall() {
  if (!installUrl.value) return
  hapticImpact('light')
  showInstallWarning.value = true
}

function confirmInstall() {
  if (!installUrl.value) return
  showInstallWarning.value = false
  window.open(installUrl.value, '_blank')
}

function addSubscription() {
  if (!connectUrl.value) return
  hapticImpact('medium')
  if (os.value === 'ios' || os.value === 'macos') {
    window.location.href = 'happ://add/sub?url=' + encodeURIComponent(connectUrl.value)
    return
  }
  window.location.href = 'clash://install-config?url=' + encodeURIComponent(connectUrl.value)
}

function nextStep() {
  hapticImpact('light')
  if (step.value < 3) {
    step.value = (step.value + 1) as SetupStep
  }
}

watch(step, (value) => {
  if (value === 3) {
    confetti({
      particleCount: 110,
      spread: 78,
      startVelocity: 42,
      origin: { y: 0.62 },
      scalar: 0.9,
      ticks: 220,
    })
  }
})

watch(
  progressPercent,
  (value) => {
    animateProgressTo(value)
  },
  { immediate: true },
)

onMounted(async () => {
  os.value = detectOS()
  if (auth.hasSubscription && !subStore.connectInfo) {
    await subStore.fetchConnect()
  }
  syncPulseOrigin()
  window.addEventListener('resize', syncPulseOrigin)
  window.addEventListener('scroll', syncPulseOrigin, true)
})

onBeforeUnmount(() => {
  if (progressFrame) {
    window.cancelAnimationFrame(progressFrame)
    progressFrame = null
  }
  window.removeEventListener('resize', syncPulseOrigin)
  window.removeEventListener('scroll', syncPulseOrigin, true)
})
</script>

<template>
  <div
    class="relative mx-auto flex min-h-[calc(100dvh-9rem)] w-full max-w-5xl flex-col justify-center gap-12 py-4 md:min-h-[calc(100dvh-3rem)]"
  >
    <div class="setup-screen-pulse" :style="screenPulseStyle" aria-hidden="true">
      <span class="wave wave-1" />
      <span class="wave wave-2" />
      <span class="wave wave-3" />
    </div>

    <div class="relative z-10 flex flex-col gap-12">
      <div class="flex flex-col gap-3">
        <h1
          class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white md:text-3xl"
        >
          {{ pageTitle }}
        </h1>
        <p class="mx-auto max-w-[34ch] text-center text-base text-neutral-400">
          {{ pageSubtitle }}
        </p>
      </div>

      <div ref="progressRingRef" class="relative mx-auto mt-1">
        <div class="setup-progress-ring" :style="circleStyle">
          <div class="setup-progress-inner">
            <Icon :icon="centerIcon" class="size-12 text-white" />
          </div>
        </div>
      </div>

      <template v-if="step === 0">
        <div class="grid gap-3">
          <Button class="pulse-cta h-12 bg-white text-black hover:bg-neutral-200" @click="nextStep">
            {{ t('setup.wizard.actions.start') }}
          </Button>
          <Button
            class="h-12 bg-neutral-900/90 text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)] hover:bg-neutral-800"
            @click="router.push({ name: 'support-setup' })"
          >
            {{ t('setup.wizard.actions.otherDevice') }}
          </Button>
        </div>
      </template>

      <template v-else-if="step === 1">
        <div class="grid gap-3">
          <Button
            class="h-12 bg-white text-black hover:bg-neutral-200"
            :disabled="!installUrl"
            @click="openInstall"
          >
            <Icon icon="lucide:download" class="size-4" />
            <span>{{ t('setup.wizard.actions.installApp') }}</span>
          </Button>
          <Button
            class="h-12 bg-neutral-900/90 text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)] hover:bg-neutral-800"
            @click="nextStep"
          >
            <span>{{ t('setup.wizard.actions.nextStep') }}</span>
            <Icon icon="lucide:arrow-right" class="size-4" />
          </Button>
        </div>
      </template>

      <template v-else-if="step === 2">
        <div class="grid gap-3">
          <Button
            class="h-12 bg-white text-black hover:bg-neutral-200"
            :disabled="!connectUrl"
            @click="addSubscription"
          >
            <Icon icon="lucide:plus" class="size-4" />
            <span>{{ t('setup.wizard.actions.addSubscription') }}</span>
          </Button>
          <Button
            class="h-12 bg-neutral-900/90 text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)] hover:bg-neutral-800"
            @click="nextStep"
          >
            <span>{{ t('setup.wizard.actions.nextStep') }}</span>
            <Icon icon="lucide:arrow-right" class="size-4" />
          </Button>
        </div>
      </template>

      <template v-else>
        <Button
          class="h-12 bg-white text-black hover:bg-neutral-200"
          @click="router.push({ name: 'home' })"
        >
          {{ t('setup.wizard.actions.finish') }}
        </Button>
      </template>
    </div>

    <SheetModal
      :model-value="showInstallWarning"
      show-handle
      overlay-class="bg-black/70 backdrop-blur-sm"
      panel-class="bg-[#0a0a0a] p-4 pb-6 shadow-[0_-20px_40px_rgba(0,0,0,0.45)] md:w-full md:max-w-lg md:rounded-2xl md:pb-4"
      @close="showInstallWarning = false"
    >
      <h2 class="mb-3 text-2xl font-semibold text-white">
        {{ t('setup.wizard.warning.title') }}
      </h2>
      <p class="text-base text-neutral-300">
        {{ t('setup.wizard.warning.body') }}
      </p>
      <Button class="mt-4 h-11 bg-white text-black hover:bg-neutral-200" @click="confirmInstall">
        {{ t('setup.wizard.warning.confirm') }}
      </Button>
    </SheetModal>
  </div>
</template>

<style scoped>
.setup-progress-ring {
  position: relative;
  display: grid;
  place-items: center;
  width: 164px;
  height: 164px;
  border-radius: 9999px;
  transition: background 260ms ease;
  animation: progress-pulse 2.1s ease-in-out infinite;
}

.setup-screen-pulse {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.wave {
  position: absolute;
  left: var(--pulse-x, 50%);
  top: var(--pulse-y, 50%);
  width: 110%;
  padding-top: 110%;
  margin-left: -55%;
  margin-top: -55%;
  border: 2px solid rgba(182, 255, 231, 0.2);
  border-radius: 50%;
  opacity: 0;
  animation: 8s cubic-bezier(0, 0.35, 0.03, 0.17) infinite pulse;
}

.wave-1 {
  animation-delay: 0s;
}

.wave-2 {
  animation-delay: 1.67s;
}

.wave-3 {
  animation-delay: 3.34s;
}

.setup-progress-ring::before,
.setup-progress-ring::after {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 9999px;
  border: 0.3px solid #232323;
  opacity: 0;
  pointer-events: none;
}

.setup-progress-ring::before {
  animation: progress-ripple 2.1s ease-out infinite;
}

.setup-progress-ring::after {
  animation: progress-ripple 2.1s ease-out 1.05s infinite;
}

.setup-progress-inner {
  display: grid;
  place-items: center;
  width: 160px;
  height: 160px;
  border-radius: 9999px;
  background: black;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 12px 28px rgba(0, 0, 0, 0.35);
}

.pulse-cta {
  animation: cta-pulse 1.8s ease-in-out infinite;
}

@keyframes cta-pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.45);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 0 14px rgba(255, 255, 255, 0);
  }
}

@keyframes progress-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.012);
  }
}

@keyframes progress-ripple {
  0% {
    transform: scale(1);
    opacity: 0;
  }
  25% {
    opacity: 0.35;
  }
  100% {
    transform: scale(1.18);
    opacity: 0;
  }
}

@keyframes pulse {
  0% {
    opacity: 0;
    transform: scale(0.1);
  }
  10% {
    opacity: 0.45;
  }
  100% {
    opacity: 0;
    transform: scale(1);
  }
}
</style>
