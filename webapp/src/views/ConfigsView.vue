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

const auth = useAuthStore()
const subStore = useSubscriptionStore()
const router = useRouter()
const { t } = useI18n()

const sub = computed(() => auth.subscription)
const isActive = computed(
  () => auth.hasSubscription && sub.value?.status_from_panel !== 'EXPIRED' && sub.value?.status_from_panel !== 'DISABLED',
)
const connectUrl = computed(() => subStore.connectInfo?.connect_url ?? '')

const copied = ref(false)
const showInstructions = ref(false)

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
    setTimeout(() => { copied.value = false }, 2000)
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
</script>

<template>
  <div class="flex w-full flex-col items-center gap-5 pt-2">
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
      <div class="flex w-full items-center justify-center border border-neutral-800 bg-neutral-950 p-4">
        <QRCode :url="connectUrl" :size="220" level="H" />
      </div>

      <!-- Subscription link -->
      <div class="flex w-full flex-col gap-2 border border-neutral-800 bg-neutral-950 px-4 py-3 text-neutral-400">
        <span class="flex items-center gap-2 font-mono text-xs uppercase">
          <Icon icon="lucide:link" class="size-3.5" />
          {{ t('configs.subLink') }}
        </span>
        <span class="truncate font-mono text-xs font-medium text-white">{{ connectUrl }}</span>
      </div>

      <!-- Copy button -->
      <button
        class="flex h-12 w-full cursor-pointer items-center gap-3 bg-white p-2 text-black transition-opacity active:opacity-70"
        @click="handleCopy"
      >
        <span class="flex bg-black p-2">
          <Icon
            :icon="copied ? 'lucide:check' : 'lucide:copy'"
            class="size-5 text-white"
          />
        </span>
        <span class="text-left font-sans text-sm leading-4 font-bold uppercase">
          {{ copied ? t('configs.copied') : t('configs.copyLink') }}
        </span>
      </button>

      <!-- Quick connect -->
      <div class="flex w-full flex-col gap-3">
        <h2 class="font-mono text-xs font-semibold uppercase tracking-wider text-neutral-400">
          {{ t('configs.quickSetup') }}
        </h2>
        <div class="flex gap-3">
          <!-- Happ -->
          <button
            class="flex h-12 flex-1 cursor-pointer items-center justify-center gap-2 border border-neutral-800 bg-neutral-950 p-2 transition-opacity active:opacity-70"
            @click="openInHapp"
          >
            <Icon icon="lucide:smartphone" class="size-4 text-neutral-400" />
            <span class="font-sans text-sm font-extrabold text-white uppercase">
              {{ t('configs.openInHapp') }}
            </span>
          </button>
          <!-- FlClashX -->
          <button
            class="flex h-12 flex-1 cursor-pointer items-center justify-center gap-2 border border-neutral-800 bg-neutral-950 p-2 transition-opacity active:opacity-70"
            @click="openInFlClash"
          >
            <Icon icon="lucide:zap" class="size-4 text-neutral-400" />
            <span class="font-sans text-sm font-extrabold text-white uppercase">
              {{ t('configs.openInFlClash') }}
            </span>
          </button>
        </div>
      </div>

      <!-- Instructions toggle -->
      <button
        class="flex h-12 w-full cursor-pointer items-center justify-between gap-3 border border-neutral-800 bg-neutral-950 px-4 py-2 transition-opacity active:opacity-70"
        @click="showInstructions = !showInstructions"
      >
        <span class="flex items-center gap-2">
          <Icon icon="lucide:book-open" class="size-4 text-neutral-400" />
          <span class="font-sans text-sm font-extrabold text-white uppercase">
            {{ t('configs.instructions') }}
          </span>
        </span>
        <Icon
          :icon="showInstructions ? 'lucide:chevron-up' : 'lucide:chevron-down'"
          class="size-4 text-neutral-400"
        />
      </button>

      <!-- Instructions content -->
      <div v-if="showInstructions" class="flex w-full flex-col gap-4">
        <!-- Happ instructions -->
        <div class="flex flex-col gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3">
          <div class="flex items-center gap-2">
            <Icon icon="lucide:smartphone" class="size-4 text-white" />
            <h3 class="font-mono text-sm font-bold uppercase text-white">
              {{ t('configs.happ.title') }}
            </h3>
          </div>
          <ol class="flex flex-col gap-2">
            <li
              v-for="n in 4"
              :key="n"
              class="flex items-start gap-3 text-sm text-neutral-300"
            >
              <span class="flex size-5 shrink-0 items-center justify-center border border-neutral-700 font-mono text-xs text-neutral-400">
                {{ n }}
              </span>
              {{ t(`configs.happ.step${n}`) }}
            </li>
          </ol>
        </div>

        <!-- FlClash instructions -->
        <div class="flex flex-col gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3">
          <div class="flex items-center gap-2">
            <Icon icon="lucide:zap" class="size-4 text-white" />
            <h3 class="font-mono text-sm font-bold uppercase text-white">
              {{ t('configs.flclash.title') }}
            </h3>
          </div>
          <ol class="flex flex-col gap-2">
            <li
              v-for="n in 4"
              :key="n"
              class="flex items-start gap-3 text-sm text-neutral-300"
            >
              <span class="flex size-5 shrink-0 items-center justify-center border border-neutral-700 font-mono text-xs text-neutral-400">
                {{ n }}
              </span>
              {{ t(`configs.flclash.step${n}`) }}
            </li>
          </ol>
        </div>

        <!-- Manual instructions -->
        <div class="flex flex-col gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3">
          <div class="flex items-center gap-2">
            <Icon icon="lucide:settings" class="size-4 text-white" />
            <h3 class="font-mono text-sm font-bold uppercase text-white">
              {{ t('configs.manual.title') }}
            </h3>
          </div>
          <ol class="flex flex-col gap-2">
            <li
              v-for="n in 4"
              :key="n"
              class="flex items-start gap-3 text-sm text-neutral-300"
            >
              <span class="flex size-5 shrink-0 items-center justify-center border border-neutral-700 font-mono text-xs text-neutral-400">
                {{ n }}
              </span>
              {{ t(`configs.manual.step${n}`) }}
            </li>
          </ol>
        </div>
      </div>
    </template>
  </div>
</template>
