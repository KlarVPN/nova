<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { copyToClipboard, monthsLabel, pluralDays } from '@/lib/utils'
import { hapticSuccess, shareUrl } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'

const store = useSubscriptionStore()
const { t } = useI18n()
const { success } = useToast()
const copied = ref(false)

onMounted(() => store.fetchReferral())

async function copyLink() {
  if (!store.referralData?.referral_link) return
  await copyToClipboard(store.referralData.referral_link)
  hapticSuccess()
  copied.value = true
  success(t('common.copied'))
  setTimeout(() => (copied.value = false), 2000)
}

function shareLink() {
  if (!store.referralData?.referral_link) return
  shareUrl(store.referralData.referral_link, t('referral.shareText'))
}

const monthOrder = [1, 3, 6, 12]
</script>

<template>
  <div class="flex flex-col gap-5 w-full pt-2">
    <h1 class="font-extrabold uppercase text-3xl leading-[0.9] tracking-tighter text-white">
      {{ t('referral.title') }}
    </h1>

    <div v-if="store.loadingReferral" class="flex items-center justify-center py-12">
      <LoadingSpinner :text="t('common.loading')" />
    </div>

    <template v-else-if="store.referralData">
      <!-- Stats -->
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-neutral-950 border border-neutral-800 py-2 px-4 flex flex-col gap-2 text-neutral-400">
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:users" class="size-4" />
            {{ t('referral.invited') }}
          </span>
          <span class="text-white text-left font-mono font-medium text-2xl">{{ store.referralData.referred_count }}</span>
        </div>
        <div class="bg-neutral-950 border border-neutral-800 py-2 px-4 flex flex-col gap-2 text-neutral-400">
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:shopping-cart" class="size-4" />
            {{ t('referral.purchased') }}
          </span>
          <span class="text-white text-left font-mono font-medium text-2xl">{{ store.referralData.purchased_count }}</span>
        </div>
      </div>

      <!-- Referral Link -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">{{ t('referral.linkLabel') }}</p>
        <div class="bg-neutral-950 border border-neutral-800 py-2 px-4 flex flex-col gap-2 text-neutral-400">
          <span class="flex items-center gap-2 font-mono text-sm uppercase">
            <Icon icon="lucide:link" class="size-4" />
            {{ t('referral.link') }}
          </span>
          <span class="text-white text-left font-mono font-medium text-xs truncate">{{ store.referralData.referral_link }}</span>
        </div>
        <div class="flex gap-3">
          <button
            class="flex-1 h-10 bg-neutral-900 border border-neutral-800 flex items-center justify-center gap-2 cursor-pointer hover:border-neutral-700 transition-colors"
            @click="copyLink"
          >
            <Icon :icon="copied ? 'lucide:check' : 'lucide:copy'" class="size-4 text-neutral-400" />
            <span class="text-xs font-semibold uppercase text-neutral-400">{{ copied ? t('common.copied') : t('common.copy') }}</span>
          </button>
          <button
            class="flex-1 h-10 bg-white text-black flex items-center justify-center gap-2 cursor-pointer"
            @click="shareLink"
          >
            <Icon icon="lucide:share-2" class="size-4" />
            <span class="text-xs font-semibold uppercase">{{ t('common.share') }}</span>
          </button>
        </div>
      </div>

      <!-- Bonus Table -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">{{ t('referral.bonusTitle') }}</p>
        <div class="border border-neutral-800">
          <!-- Header -->
          <div class="grid grid-cols-3 bg-neutral-900 px-4 py-2">
            <span class="text-xs font-semibold uppercase text-neutral-500">{{ t('referral.plan') }}</span>
            <span class="text-center text-xs font-semibold uppercase text-neutral-500">{{ t('referral.you') }}</span>
            <span class="text-center text-xs font-semibold uppercase text-neutral-500">{{ t('referral.friend') }}</span>
          </div>
          <div
            v-for="(months, idx) in monthOrder"
            :key="months"
            class="grid grid-cols-3 border-t border-neutral-800 px-4 py-2.5"
            :class="idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/50'"
          >
            <span class="font-mono text-sm text-white">{{ monthsLabel(months) }}</span>
            <span class="text-center font-mono text-sm text-[#bdfe00]">
              +{{ pluralDays(store.referralData.bonus_structure[months]?.inviter_days ?? 0) }}
            </span>
            <span class="text-center font-mono text-sm text-neutral-400">
              +{{ pluralDays(store.referralData.bonus_structure[months]?.referee_days ?? 0) }}
            </span>
          </div>
        </div>
      </div>

      <!-- How it works -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">{{ t('referral.howTitle') }}</p>
        <div class="flex flex-col gap-2">
          <div
            v-for="(step, i) in [t('referral.step1'), t('referral.step2'), t('referral.step3')]"
            :key="i"
            class="bg-neutral-950 border border-neutral-800 py-2 px-4 flex items-start gap-3"
          >
            <span class="font-mono text-sm font-bold text-[#bdfe00] shrink-0">{{ i + 1 }}.</span>
            <p class="text-sm text-neutral-400 text-left">{{ step }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
