<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { Button } from '@/components/ui/button'
import { hapticError, hapticImpact, hapticSuccess, openLink } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { copyToClipboard } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const subStore = useSubscriptionStore()
const { success, error } = useToast()

const docsUrl = import.meta.env.VITE_DOCS_URL || ''
const platformLinks = {
  ios: import.meta.env.VITE_INSTRUCTION_IOS_URL || docsUrl,
  android: import.meta.env.VITE_INSTRUCTION_ANDROID_URL || docsUrl,
  macos: import.meta.env.VITE_INSTRUCTION_MACOS_URL || docsUrl,
  linux: import.meta.env.VITE_INSTRUCTION_LINUX_URL || docsUrl,
}

const tiles = computed(() => [
  { key: 'ios', label: 'iOS', icon: 'lucide:smartphone', url: platformLinks.ios },
  { key: 'android', label: 'Android', icon: 'lucide:smartphone-charging', url: platformLinks.android },
  { key: 'macos', label: 'macOS', icon: 'lucide:laptop', url: platformLinks.macos },
  { key: 'linux', label: 'Linux', icon: 'lucide:terminal', url: platformLinks.linux },
])
const connectUrl = computed(() => subStore.connectInfo?.config_link || subStore.connectInfo?.connect_url || '')

onMounted(async () => {
  if (auth.hasSubscription && !subStore.connectInfo) {
    await subStore.fetchConnect()
  }
})

function goBack() {
  hapticImpact('light')
  router.push({ name: 'support' })
}

function openPlatform(url: string) {
  if (!url) return
  hapticImpact('light')
  openLink(url)
}

function openOtherPlatforms() {
  if (!docsUrl) return
  hapticImpact('light')
  openLink(docsUrl)
}

async function copySubscriptionLink() {
  if (!connectUrl.value) return
  try {
    await copyToClipboard(connectUrl.value)
    hapticSuccess()
    success(t('common.copied'))
  } catch {
    hapticError()
    error(t('common.error'))
  }
}
</script>

<template>
  <div class="flex w-full flex-col gap-4 pt-3 pb-6">
    <button class="-mb-1 flex cursor-pointer items-center gap-2 text-sm text-neutral-400" @click="goBack">
      <Icon icon="lucide:arrow-left" class="size-4" />
      {{ t('common.back') }}
    </button>

    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('support.setupOtherDevice') }}
    </h1>

    <div class="grid grid-cols-2 gap-3">
      <button
        v-for="tile in tiles"
        :key="tile.key"
        :disabled="!tile.url"
        class="flex min-h-24 cursor-pointer flex-col items-center justify-center gap-2 rounded-[14px] border border-neutral-800 bg-neutral-950 text-white transition-colors hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-40"
        @click="openPlatform(tile.url)"
      >
        <Icon :icon="tile.icon" class="size-5 text-neutral-300" />
        <span class="text-sm font-medium">{{ tile.label }}</span>
      </button>
    </div>

    <Button
      :disabled="!docsUrl"
      class="mt-1 h-12 w-full rounded-[14px] border border-neutral-800 bg-neutral-950 text-white hover:bg-neutral-900"
      @click="openOtherPlatforms"
    >
      {{ t('support.otherPlatforms') }}
    </Button>

    <Transition name="floating-link">
      <div
        v-if="connectUrl"
        class="pointer-events-none fixed inset-x-0 z-40 px-4"
        style="bottom: calc(env(safe-area-inset-bottom) + 80px)"
      >
        <button
          class="pointer-events-auto mx-auto flex w-full max-w-md cursor-pointer items-center gap-3 rounded-[14px] border border-neutral-700 bg-neutral-950/95 px-4 py-3 text-left backdrop-blur"
          @click="copySubscriptionLink"
        >
          <div class="min-w-0 flex-1">
            <p class="text-xs text-neutral-500">{{ t('home.subLink') }}</p>
            <p class="truncate text-sm text-white">{{ connectUrl }}</p>
          </div>
          <Icon icon="lucide:copy" class="size-4 shrink-0 text-neutral-300" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.floating-link-enter-active,
.floating-link-leave-active {
  transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.floating-link-enter-from,
.floating-link-leave-to {
  opacity: 0;
  transform: translateY(18px);
}
</style>
