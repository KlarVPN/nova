<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { hapticImpact, hapticSuccess } from '@/lib/telegram'
import { copyToClipboard } from '@/lib/utils'
import QRCode from '@/components/common/QRCode.vue'
import { Card } from '@/components/common'
import { Button } from '@/components/ui/button'

const auth = useAuthStore()
const subStore = useSubscriptionStore()
const router = useRouter()
const { t } = useI18n()

const sub = computed(() => auth.subscription)
const isActive = computed(
  () =>
    auth.hasSubscription &&
    sub.value?.status_from_panel !== 'EXPIRED' &&
    sub.value?.status_from_panel !== 'DISABLED',
)
const connectUrl = computed(() => subStore.connectInfo?.connect_url ?? '')

const copied = ref(false)

onMounted(async () => {
  if (isActive.value && !subStore.connectInfo) {
    await subStore.fetchConnect()
  }
})

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

function openInHapp() {
  if (!connectUrl.value) return
  hapticImpact('medium')
  window.location.href = 'happ://add/sub?url=' + encodeURIComponent(connectUrl.value)
}

function openInFlClash() {
  if (!connectUrl.value) return
  hapticImpact('medium')
  window.location.href = 'clash://install-config?url=' + encodeURIComponent(connectUrl.value)
}

function goToPlans() {
  hapticImpact()
  router.push('/plans')
}

function goToSetup() {
  hapticImpact('light')
  router.push('/setup')
}
</script>

<template>
  <div class="flex w-full flex-col items-center gap-5 pt-2">
    <h1 class="text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('configs.title') }}
    </h1>
    <!-- NO SUBSCRIPTION -->
    <template v-if="!isActive">
      <div class="flex flex-col items-center gap-5 pt-6 text-center">
        <span class="flex rounded-full bg-white p-3">
          <Icon icon="lucide:qr-code" class="size-12 text-black" />
        </span>
        <div>
          <h1 class="text-3xl leading-[0.9] font-extrabold tracking-tighter text-white uppercase">
            {{ t('configs.noSub') }}
          </h1>
          <p class="mt-2 text-sm text-neutral-400">{{ t('configs.noSubDesc') }}</p>
        </div>
      </div>
      <button
        class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black"
        @click="goToPlans"
      >
        <span class="flex bg-black p-2">
          <Icon icon="lucide:shield" class="size-5 text-white" />
        </span>
        <span class="text-left font-sans text-sm leading-4 font-bold uppercase">
          {{ t('home.subscribe') }}
        </span>
      </button>
    </template>

    <!-- LOADING -->
    <template v-else-if="subStore.loadingConnect">
      <div class="flex h-48 items-center justify-center">
        <Icon icon="lucide:loader-circle" class="size-8 animate-spin text-neutral-400" />
      </div>
    </template>

    <!-- ACTIVE WITH CONNECT URL -->
    <template v-else-if="connectUrl">
      <!-- QR Code -->
      <div
        class="flex w-full items-center justify-center rounded-[14px] border border-neutral-800 bg-neutral-950 p-4"
      >
        <QRCode :url="connectUrl" :size="220" level="H" />
      </div>

      <!-- Subscription link -->
      <Card>
        <span class="flex items-center gap-2 text-xs">
          <Icon icon="lucide:link" class="size-3.5" />
          {{ t('configs.subLink') }}
        </span>
        <span class="truncate text-xs font-medium text-white">{{ connectUrl }}</span>
      </Card>

      <!-- Copy button -->
      <Button
        class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black transition-opacity active:opacity-70"
        @click="handleCopy"
      >
        <Icon :icon="copied ? 'lucide:check' : 'lucide:copy'" class="size-5" />
        <span class="font-sans text-sm">
          {{ copied ? t('configs.copied') : t('configs.copyLink') }}
        </span>
      </Button>

      <!-- Quick connect -->
      <div class="flex w-full flex-col gap-3">
        <h2 class="text-xs font-medium text-neutral-400">
          {{ t('configs.quickSetup') }}
        </h2>
        <div class="flex gap-3">
          <!-- Happ -->
          <Button
            class="flex h-12 flex-1 cursor-pointer items-center justify-center gap-2 border border-neutral-800 bg-neutral-950 p-2 hover:bg-neutral-900 active:opacity-70"
            @click="openInHapp"
          >
            <Icon icon="lucide:smartphone" class="size-4 text-neutral-400" />
            <span class="font-sans text-sm text-white">
              {{ t('configs.openInHapp') }}
            </span>
          </Button>
          <!-- FlClashX -->
          <Button
            class="flex h-12 flex-1 cursor-pointer items-center justify-center gap-2 border border-neutral-800 bg-neutral-950 p-2 hover:bg-neutral-900 active:opacity-70"
            @click="openInFlClash"
          >
            <Icon icon="lucide:zap" class="size-4 text-neutral-400" />
            <span class="font-sans text-sm text-white">
              {{ t('configs.openInFlClash') }}
            </span>
          </Button>
        </div>
      </div>

      <!-- Instructions button -->
      <Button
        class="flex h-12 w-full cursor-pointer items-center justify-between gap-3 border border-neutral-800 bg-neutral-950 px-4 py-2 hover:bg-neutral-900 active:opacity-70"
        @click="goToSetup"
      >
        <span class="flex items-center gap-2">
          <Icon icon="lucide:book-open" class="size-4 text-neutral-400" />
          <span class="font-sans text-sm text-white">
            {{ t('configs.instructions') }}
          </span>
        </span>
        <Icon icon="lucide:chevron-right" class="size-4 text-neutral-400" />
      </Button>
    </template>
  </div>
</template>
