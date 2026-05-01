<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { copyToClipboard, monthsLabel, pluralDays } from '@/lib/utils'
import { hapticSuccess, shareUrl } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'
import { Card } from '@/components/common'
import { Button } from '@/components/ui/button'
import PageHeroCard from '@/components/common/PageHeroCard.vue'
import FloatingLink from '@/components/common/FloatingLink.vue'
import Skeleton from '@/components/common/Skeleton.vue'

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
const openFaqIndex = ref<number | null>(0)

const referralSteps = computed(() => [
  {
    icon: 'lucide:share-2',
    title: t('referral.timeline.shareTitle'),
    subtitle: store.referralData?.referral_link || t('referral.timeline.shareSubtitle'),
    canCopy: Boolean(store.referralData?.referral_link),
  },
  {
    icon: 'lucide:circle-dollar-sign',
    title: t('referral.timeline.waitTitle'),
    subtitle: t('referral.timeline.waitSubtitle'),
    canCopy: false,
  },
  {
    icon: 'lucide:smile',
    title: t('referral.timeline.friendBonusTitle'),
    subtitle: t('referral.timeline.friendBonusSubtitle'),
    canCopy: false,
  },
  {
    icon: 'lucide:gift',
    title: t('referral.timeline.yourBonusTitle'),
    subtitle: t('referral.timeline.yourBonusSubtitle'),
    canCopy: false,
  },
])

const referralFaq = computed(() => [
  {
    q: t('referral.faq.q1'),
    a: t('referral.faq.a1'),
  },
  {
    q: t('referral.faq.q2'),
    a: t('referral.faq.a2'),
  },
  {
    q: t('referral.faq.q3'),
    a: t('referral.faq.a3'),
  },
  {
    q: t('referral.faq.q4'),
    a: t('referral.faq.a4'),
  },
  {
    q: t('referral.faq.q5'),
    a: t('referral.faq.a5'),
  },
  {
    q: t('referral.faq.q6'),
    a: t('referral.faq.a6'),
  },
])

function toggleFaq(index: number) {
  openFaqIndex.value = openFaqIndex.value === index ? null : index
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-5 pt-2 pb-22 md:pb-6">
    <PageHeroCard
      :title="t('referral.title')"
      :description="t('referral.description')"
      icon="mdi:account-group"
    />
    <Transition name="content-fade" mode="out-in">
      <div v-if="store.loadingReferral" key="loading" class="flex w-full flex-col gap-3 py-2">
        <div class="grid grid-cols-2 gap-3">
          <Skeleton class="h-24 border border-neutral-800" />
          <Skeleton class="h-24 border border-neutral-800" />
        </div>
        <Skeleton class="h-32 w-full border border-neutral-800" />
        <Skeleton class="h-44 w-full border border-neutral-800" />
      </div>

      <div v-else-if="store.referralData" key="content" class="flex w-full flex-col gap-3">
        <!-- How it works -->
        <div class="flex flex-col gap-3">
          <div class="relative overflow-hidden rounded-[14px] bg-neutral-950 px-4 py-3">
            <div
              class="absolute top-6 bottom-6 left-8 w-px border-l border-dashed border-white/25"
            />
            <div
              v-for="(step, i) in referralSteps"
              :key="i"
              class="relative flex items-start gap-3 py-2"
              :class="i === referralSteps.length - 1 ? 'bg-neutral-950' : ''"
            >
              <span
                class="relative z-10 flex size-8 shrink-0 items-center justify-center rounded-xl border border-white/15 bg-neutral-900 ring-3 ring-neutral-950"
              >
                <Icon :icon="step.icon" class="size-4 text-white/90" />
              </span>
              <div class="min-w-0 flex-1 text-left">
                <p class="text-base font-medium text-white">{{ step.title }}</p>
                <p class="text-sm text-white/55">{{ step.subtitle }}</p>
                <button
                  v-if="step.canCopy"
                  type="button"
                  class="mt-1 inline-flex cursor-pointer items-center gap-1 text-sm text-neutral-200"
                  @click="copyLink"
                >
                  {{ copied ? t('common.copied') : t('common.copy') }}
                  <Icon :icon="copied ? 'lucide:check' : 'lucide:copy'" class="size-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
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

        <!-- Bonus Table -->
        <div class="flex flex-col gap-3">
          <p class="py-1 text-base font-medium text-white">
            {{ t('referral.bonusTitle') }}
          </p>
          <div class="overflow-hidden rounded-[14px]">
            <!-- Header -->
            <div class="grid grid-cols-3 bg-neutral-900 px-4 py-2">
              <span class="text-xs font-semibold text-neutral-500">{{ t('referral.plan') }}</span>
              <span class="text-center text-xs font-semibold text-neutral-500">
                {{ t('referral.you') }}
              </span>
              <span class="text-center text-xs font-semibold text-neutral-500">
                {{ t('referral.friend') }}
              </span>
            </div>
            <div
              v-for="(months, idx) in monthOrder"
              :key="months"
              class="grid grid-cols-3 border-t border-neutral-800 px-4 py-2.5"
              :class="idx % 2 === 0 ? 'bg-neutral-950' : 'bg-neutral-900/50'"
            >
              <span class="text-sm text-white">{{ monthsLabel(months) }}</span>
              <span class="text-center text-sm font-bold text-white">
                +{{ pluralDays(store.referralData.bonus_structure[months]?.inviter_days ?? 0) }}
              </span>
              <span class="text-center text-sm text-neutral-400">
                +{{ pluralDays(store.referralData.bonus_structure[months]?.referee_days ?? 0) }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <p class="py-1 text-base font-medium text-white">{{ t('referral.faq.title') }}</p>
          <div class="flex flex-col gap-2">
            <div
              v-for="(item, idx) in referralFaq"
              :key="idx"
              class="overflow-hidden rounded-[14px] bg-neutral-950"
            >
              <button
                type="button"
                class="flex w-full cursor-pointer items-start justify-between gap-3 px-4 py-3 text-left"
                @click="toggleFaq(idx)"
              >
                <span class="text-base font-medium text-white">{{ item.q }}</span>
                <Icon
                  :icon="openFaqIndex === idx ? 'lucide:chevron-up' : 'lucide:chevron-down'"
                  class="mt-0.5 size-4 shrink-0 text-white"
                />
              </button>
              <div v-if="openFaqIndex === idx" class="border-t border-white/10 px-4 py-3">
                <p class="text-sm text-white/90">{{ item.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else key="empty" class="w-full rounded-[14px] bg-neutral-950 px-4 py-6">
        <p class="text-sm text-neutral-400">{{ t('common.error') }}</p>
      </div>
    </Transition>
  </div>
  <FloatingLink text="Ваша реферальная ссылка" :url="store.referralData?.referral_link || ''" />
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
