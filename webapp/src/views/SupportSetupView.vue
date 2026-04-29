<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { Button } from '@/components/ui/button'
import FloatingSubscriptionLink from '@/components/common/FloatingSubscriptionLink.vue'
import { hapticImpact, openLink } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const subStore = useSubscriptionStore()

const docsUrl = computed(() => auth.profile?.links.docs || '')
const platformLinks = computed(() => ({
  ios: auth.profile?.links.instruction_ios || docsUrl.value,
  android: auth.profile?.links.instruction_android || docsUrl.value,
  macos: auth.profile?.links.instruction_macos || docsUrl.value,
  windows: auth.profile?.links.instruction_windows || docsUrl.value,
}))

const tiles = computed(() => [
  { key: 'ios', label: 'iOS', icon: 'simple-icons:ios', url: platformLinks.value.ios },
  {
    key: 'android',
    label: 'Android',
    icon: 'ic:sharp-android',
    url: platformLinks.value.android,
  },
  { key: 'macos', label: 'macOS', icon: 'simple-icons:macos', url: platformLinks.value.macos },
  { key: 'windows', label: 'Windows', icon: 'raphael:windows', url: platformLinks.value.windows },
])
const connectUrl = computed(
  () => subStore.connectInfo?.config_link || subStore.connectInfo?.connect_url || '',
)

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
  if (!docsUrl.value) return
  hapticImpact('light')
  openLink(docsUrl.value)
}
</script>

<template>
  <div
    class="mx-auto flex min-h-[calc(100dvh-9rem)] w-full max-w-5xl flex-col justify-center gap-4 pt-3 pb-24"
  >
    <div class="bg-wh flex flex-col gap-3 rounded-[14px] bg-neutral-950 p-5 pr-25">
      <span class="flex w-fit items-center justify-center rounded-[7px] bg-white/10 p-4">
        <Icon icon="lucide:settings" class="size-8 opacity-60" />
      </span>
      <h1 class="mt-1 text-2xl leading-[0.9] font-medium tracking-tight text-balance text-white">
        {{ t('support.setupOtherDevice') }}
      </h1>
      <p class="text-sm text-balance opacity-60">
        Выберите платформу для подключения на другом устройстве
      </p>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <button
        v-for="tile in tiles"
        :key="tile.key"
        :disabled="!tile.url"
        class="flex min-h-24 cursor-pointer flex-col items-start justify-center gap-2 rounded-[14px] bg-neutral-950 p-5 text-white transition-colors hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-40"
        @click="openPlatform(tile.url)"
      >
        <span class="rounded-[14px] bg-white p-3"
          ><Icon :icon="tile.icon" class="size-10 text-black"
        /></span>

        <div class="flex flex-col items-start text-white/60">
          Инструкция <span class="font-semibold text-white">для {{ tile.label }}</span>
        </div>
      </button>
    </div>

    <Button
      :disabled="!docsUrl"
      class="mt-1 h-12 w-full rounded-[14px] bg-neutral-950 text-white hover:bg-neutral-900"
      @click="openOtherPlatforms"
    >
      {{ t('support.otherPlatforms') }}
    </Button>

    <FloatingSubscriptionLink :url="connectUrl" />
  </div>
</template>
