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
  linux: auth.profile?.links.instruction_linux || docsUrl.value,
}))

const tiles = computed(() => [
  { key: 'ios', label: 'iOS', icon: 'lucide:smartphone', url: platformLinks.value.ios },
  {
    key: 'android',
    label: 'Android',
    icon: 'lucide:smartphone-charging',
    url: platformLinks.value.android,
  },
  { key: 'macos', label: 'macOS', icon: 'lucide:laptop', url: platformLinks.value.macos },
  { key: 'linux', label: 'Linux', icon: 'lucide:terminal', url: platformLinks.value.linux },
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
  if (!docsUrl.value) return
  hapticImpact('light')
  openLink(docsUrl.value)
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-3 pb-6">
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

    <FloatingSubscriptionLink :url="connectUrl" />
  </div>
</template>
