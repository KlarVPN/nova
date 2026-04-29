<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { copyToClipboard, monthsLabel, pluralDays } from '@/lib/utils'
import { hapticSuccess, shareUrl } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'
import { Card } from '@/components/common'
import { Button } from '@/components/ui/button'

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
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-5 pt-2">
    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('referral.title') }}
    </h1>

    <Transition name="content-fade" mode="out-in">
      <div v-if="store.loadingReferral" key="loading" class="flex w-full flex-col gap-3 py-2">
        <div class="grid grid-cols-2 gap-3">
          <div class="h-24 animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900" />
          <div class="h-24 animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900" />
        </div>
        <div
          class="h-32 w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
        <div
          class="h-44 w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
      </div>

      <div v-else-if="store.referralData" key="content" class="w-full">
        <!-- Stats -->
        <div class="grid grid-cols-2 gap-3">
          <Card>
            <span class="flex items-center gap-2 text-sm">
              <Icon icon="lucide:users" class="size-4" />
              {{ t('referral.invited') }}
            </span>
            <span class="text-left text-2xl font-medium text-white">{{
              store.referralData.referred_count
            }}</span>
          </Card>
          <Card>
            <span class="flex items-center gap-2 text-sm">
              <Icon icon="lucide:shopping-cart" class="size-4" />
              {{ t('referral.purchased') }}
            </span>
            <span class="text-left text-2xl font-medium text-white">{{
              store.referralData.purchased_count
            }}</span>
          </Card>
        </div>

        <!-- Referral Link -->
        <div class="flex flex-col gap-3">
          <p class="text-sm font-medium text-neutral-500">
            {{ t('referral.linkLabel') }}
          </p>
          <Card>
            <span class="flex items-center gap-2 text-sm">
              <Icon icon="lucide:link" class="size-4" />
              {{ t('referral.link') }}
            </span>
            <span class="truncate text-left text-sm font-medium text-white">{{
              store.referralData.referral_link
            }}</span>
          </Card>
          <div class="flex gap-3">
            <Button
              class="flex h-10 flex-1 border border-neutral-800 bg-neutral-950 transition-colors hover:border-neutral-700 hover:bg-neutral-900"
              @click="copyLink"
            >
              <Icon
                :icon="copied ? 'lucide:check' : 'lucide:copy'"
                class="size-4 text-neutral-400"
              />
              <span class="text-sm text-neutral-400">{{
                copied ? t('common.copied') : t('common.copy')
              }}</span>
            </Button>
            <Button class="flex h-10 flex-1 transition-colors" @click="shareLink">
              <Icon icon="lucide:share-2" class="size-4" />
              <span class="text-sm">{{ t('common.share') }}</span>
            </Button>
          </div>
        </div>

        <!-- Bonus Table -->
        <div class="flex flex-col gap-3">
          <p class="text-sm font-medium text-neutral-500">
            {{ t('referral.bonusTitle') }}
          </p>
          <div class="overflow-hidden rounded-[14px] border border-neutral-800">
            <!-- Header -->
            <div class="grid grid-cols-3 bg-neutral-900 px-4 py-2">
              <span class="text-xs font-semibold text-neutral-500 uppercase">{{
                t('referral.plan')
              }}</span>
              <span class="text-center text-xs font-semibold text-neutral-500 uppercase">{{
                t('referral.you')
              }}</span>
              <span class="text-center text-xs font-semibold text-neutral-500 uppercase">{{
                t('referral.friend')
              }}</span>
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
          <p class="text-sm font-medium text-neutral-500">
            {{ t('referral.howTitle') }}
          </p>
          <div class="flex flex-col gap-2">
            <div
              v-for="(step, i) in [t('referral.step1'), t('referral.step2'), t('referral.step3')]"
              :key="i"
              class="flex items-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 py-2"
            >
              <span class="shrink-0 text-sm font-bold text-[#bdfe00]">{{ i + 1 }}.</span>
              <p class="text-left text-sm text-neutral-400">{{ step }}</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 240ms ease;
}

.content-fade-enter-from,
.content-fade-leave-to {
  opacity: 0;
}
</style>
