<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { Button } from '@/components/ui/button'
import { hapticImpact, hapticSuccess } from '@/lib/telegram'
import { copyToClipboard } from '@/lib/utils'

type SetupScene = 1 | 2 | 3
type SetupDevice = 'this' | 'other'
type SetupOS = 'ios' | 'macos' | 'android' | 'windows' | 'linux' | 'other'
type SetupApp = 'happ' | 'flclash' | 'manual'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const subStore = useSubscriptionStore()

const scene = ref<SetupScene>(1)
const device = ref<SetupDevice>('this')
const selectedOS = ref<SetupOS>('other')
const selectedApp = ref<SetupApp>('happ')
const copied = ref(false)

const sub = computed(() => auth.subscription)
const isActive = computed(
  () =>
    auth.hasSubscription &&
    sub.value?.status_from_panel !== 'EXPIRED' &&
    sub.value?.status_from_panel !== 'DISABLED',
)
const connectUrl = computed(() => subStore.connectInfo?.connect_url ?? '')

const osOptions: Array<{ key: SetupOS; label: string }> = [
  { key: 'ios', label: 'iOS' },
  { key: 'macos', label: 'macOS' },
  { key: 'android', label: 'Android' },
  { key: 'windows', label: 'Windows' },
  { key: 'linux', label: 'Linux' },
  { key: 'other', label: 'Other' },
]

const appOptions = computed(() => [
  {
    key: 'happ' as const,
    icon: 'lucide:smartphone',
    title: t('setup.apps.happ.title'),
    desc: t('setup.apps.happ.desc'),
    recommended: true,
    available:
      selectedOS.value === 'ios' || selectedOS.value === 'macos' || selectedOS.value === 'other',
  },
  {
    key: 'flclash' as const,
    icon: 'lucide:zap',
    title: t('setup.apps.flclash.title'),
    desc: t('setup.apps.flclash.desc'),
    recommended: false,
    available:
      selectedOS.value === 'android' ||
      selectedOS.value === 'windows' ||
      selectedOS.value === 'linux' ||
      selectedOS.value === 'other',
  },
  {
    key: 'manual' as const,
    icon: 'lucide:settings-2',
    title: t('setup.apps.manual.title'),
    desc: t('setup.apps.manual.desc'),
    recommended: false,
    available: true,
  },
])

function detectOS(): SetupOS {
  const ua = navigator.userAgent.toLowerCase()
  if (/iphone|ipad|ipod/.test(ua)) return 'ios'
  if (/macintosh|mac os x/.test(ua)) return 'macos'
  if (/android/.test(ua)) return 'android'
  if (/windows/.test(ua)) return 'windows'
  if (/linux/.test(ua)) return 'linux'
  return 'other'
}

onMounted(async () => {
  selectedOS.value = detectOS()
  if (isActive.value && !subStore.connectInfo) {
    await subStore.fetchConnect()
  }
})

function goToScene(next: SetupScene) {
  hapticImpact('light')
  scene.value = next
}

function chooseDevice(next: SetupDevice) {
  device.value = next
  if (next === 'this') {
    selectedApp.value =
      selectedOS.value === 'ios' || selectedOS.value === 'macos' ? 'happ' : 'flclash'
  } else {
    selectedApp.value = 'happ'
  }
  goToScene(2)
}

function selectApp(app: SetupApp) {
  selectedApp.value = app
  goToScene(3)
}

async function handleCopy() {
  if (!connectUrl.value) return
  try {
    await copyToClipboard(connectUrl.value)
    hapticSuccess()
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    hapticImpact('medium')
  }
}

function openApp() {
  if (!connectUrl.value) return
  hapticImpact('medium')
  if (selectedApp.value === 'happ') {
    window.location.href = 'happ://add/sub?url=' + encodeURIComponent(connectUrl.value)
    return
  }
  if (selectedApp.value === 'flclash') {
    window.location.href = 'clash://install-config?url=' + encodeURIComponent(connectUrl.value)
  }
}

function goToPlans() {
  hapticImpact('medium')
  router.push('/plans')
}
</script>

<template>
  <div class="flex w-full flex-col gap-4 pt-3 pb-6">
    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('nav.setup') }}
    </h1>

    <template v-if="!isActive">
      <div class="rounded-2xl border border-neutral-800 bg-neutral-950 p-5 text-center">
        <p class="text-base font-semibold text-white">{{ t('setup.noSubTitle') }}</p>
        <p class="mt-2 text-sm text-neutral-400">{{ t('setup.noSubDesc') }}</p>
        <Button
          class="mt-4 h-11 w-full bg-white text-black hover:bg-neutral-200"
          @click="goToPlans"
        >
          {{ t('home.subscribe') }}
        </Button>
      </div>
    </template>

    <template v-else-if="subStore.loadingConnect">
      <div class="flex h-48 items-center justify-center">
        <Icon icon="lucide:loader-circle" class="size-8 animate-spin text-neutral-400" />
      </div>
    </template>

    <template v-else>
      <div class="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-sm text-neutral-400">{{ t('setup.progress') }}</p>
          <p class="text-sm font-medium text-white">{{ scene }}/3</p>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div class="h-1.5 rounded-full" :class="scene >= 1 ? 'bg-white' : 'bg-neutral-800'" />
          <div class="h-1.5 rounded-full" :class="scene >= 2 ? 'bg-white' : 'bg-neutral-800'" />
          <div class="h-1.5 rounded-full" :class="scene >= 3 ? 'bg-white' : 'bg-neutral-800'" />
        </div>
      </div>

      <section v-if="scene === 1" class="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 class="text-lg font-semibold text-white">{{ t('setup.scene1.title') }}</h2>
        <p class="mt-1 text-sm text-neutral-400">{{ t('setup.scene1.desc') }}</p>
        <div class="mt-4 grid gap-3">
          <button
            class="flex cursor-pointer items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-900 p-3 text-left transition hover:border-white"
            @click="chooseDevice('this')"
          >
            <Icon icon="lucide:smartphone" class="size-5 text-white" />
            <div>
              <p class="font-medium text-white">{{ t('setup.scene1.thisDevice') }}</p>
              <p class="text-xs text-neutral-400">{{ t('setup.scene1.thisDeviceDesc') }}</p>
            </div>
          </button>
          <button
            class="flex cursor-pointer items-center gap-3 rounded-xl border border-neutral-700 bg-neutral-900 p-3 text-left transition hover:border-white"
            @click="chooseDevice('other')"
          >
            <Icon icon="lucide:monitor-smartphone" class="size-5 text-white" />
            <div>
              <p class="font-medium text-white">{{ t('setup.scene1.otherDevice') }}</p>
              <p class="text-xs text-neutral-400">{{ t('setup.scene1.otherDeviceDesc') }}</p>
            </div>
          </button>
        </div>
      </section>

      <section v-if="scene === 2" class="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-lg font-semibold text-white">{{ t('setup.scene2.title') }}</h2>
          <Button
            variant="ghost"
            size="sm"
            class="h-8 px-2 text-neutral-300 hover:text-white"
            @click="goToScene(1)"
          >
            <Icon icon="lucide:arrow-left" class="size-4" />
          </Button>
        </div>
        <p class="mt-1 text-sm text-neutral-400">{{ t('setup.scene2.desc') }}</p>

        <div class="mt-3 grid grid-cols-3 gap-2">
          <button
            v-for="os in osOptions"
            :key="os.key"
            class="cursor-pointer rounded-lg border px-2 py-1.5 text-xs font-semibold"
            :class="
              selectedOS === os.key
                ? 'border-white bg-neutral-900 text-white'
                : 'border-neutral-800 bg-black text-neutral-400'
            "
            @click="selectedOS = os.key"
          >
            {{ os.label }}
          </button>
        </div>

        <div class="mt-4 grid gap-3">
          <button
            v-for="app in appOptions"
            :key="app.key"
            class="relative flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-left transition"
            :class="
              selectedApp === app.key
                ? 'border-white bg-neutral-900'
                : app.available
                  ? 'border-neutral-700 bg-neutral-900 hover:border-neutral-400'
                  : 'border-neutral-800 bg-black/40 opacity-60'
            "
            @click="app.available && selectApp(app.key)"
          >
            <Icon :icon="app.icon" class="mt-0.5 size-5 text-white" />
            <div class="min-w-0">
              <p class="font-medium text-white">{{ app.title }}</p>
              <p class="text-xs text-neutral-400">{{ app.desc }}</p>
            </div>
            <span
              v-if="app.recommended"
              class="ml-auto rounded-full border border-lime-400/60 bg-lime-400/15 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-lime-300 uppercase"
            >
              {{ t('setup.recommended') }}
            </span>
          </button>
        </div>
      </section>

      <section v-if="scene === 3" class="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-lg font-semibold text-white">{{ t('setup.scene3.title') }}</h2>
          <Button
            variant="ghost"
            size="sm"
            class="h-8 px-2 text-neutral-300 hover:text-white"
            @click="goToScene(2)"
          >
            <Icon icon="lucide:arrow-left" class="size-4" />
          </Button>
        </div>
        <p class="mt-1 text-sm text-neutral-400">{{ t('setup.scene3.desc') }}</p>

        <div class="mt-4 rounded-xl border border-neutral-800 bg-black/40 p-3">
          <p class="text-xs text-neutral-400">{{ t('setup.subLink') }}</p>
          <p class="mt-1 truncate text-sm text-white">{{ connectUrl }}</p>
        </div>

        <div class="mt-3 flex gap-2">
          <Button class="h-10 flex-1 border border-neutral-700 bg-neutral-900" @click="handleCopy">
            {{ copied ? t('common.copied') : t('common.copy') }}
          </Button>
          <Button
            v-if="selectedApp !== 'manual'"
            class="h-10 flex-1 border border-neutral-700 bg-white text-black hover:bg-neutral-200"
            @click="openApp"
          >
            {{ selectedApp === 'happ' ? t('configs.openInHapp') : t('configs.openInFlClash') }}
          </Button>
        </div>

        <ol class="mt-4 flex flex-col gap-2">
          <li
            v-for="n in 4"
            :key="`${selectedApp}-${n}`"
            class="flex items-start gap-2 text-sm text-neutral-300"
          >
            <span
              class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-neutral-700 text-xs text-neutral-400"
            >
              {{ n }}
            </span>
            {{ t(`configs.${selectedApp}.step${n}`) }}
          </li>
        </ol>
      </section>
    </template>
  </div>
</template>
