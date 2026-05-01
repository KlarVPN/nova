<script setup lang="ts">
import { FloatingLink, PageHeroCard } from '@/components/common'
import { Button } from '@/components/ui/button'
import { hapticImpact, openLink } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { Icon } from '@iconify/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

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
  <div class="mx-auto flex min-h-[calc(100dvh-9rem)] w-full max-w-5xl flex-col gap-4 pt-3 pb-24">
    <PageHeroCard
      icon="lucide:settings"
      :title="t('support.setupOtherDevice')"
      :description="t('support.setupOtherDeviceDesc')"
    />

    <div class="grid grid-cols-2 gap-3">
      <button
        v-for="tile in tiles"
        :key="tile.key"
        :disabled="!tile.url"
        class="flex min-h-24 cursor-pointer flex-col items-start justify-center gap-2 rounded-[14px] bg-neutral-950 p-5 text-white transition-colors hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-40"
        @click="openPlatform(tile.url)"
      >
        <span class="rounded-[14px] bg-white/5 p-3">
          <Icon :icon="tile.icon" class="size-10 text-white" />
        </span>

        <div class="flex flex-col items-start gap-px text-white/60">
          <span class="leading-none">{{ t('support.instruction') }}</span>
          <span class="text-lg leading-none font-medium text-white">
            {{ t('support.forPlatform', { platform: tile.label }) }}
          </span>
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

    <FloatingLink :text="t('home.subLink')" :url="connectUrl" />
  </div>
</template>
