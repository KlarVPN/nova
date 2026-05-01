<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import PageHeroCard from '@/components/common/PageHeroCard.vue'

const { t } = useI18n()
const openIndex = ref(0)
const isSwitching = ref(false)
let switchTimer: number | null = null

const faqItems = computed(() => [
  { question: t('faq.q1'), answer: t('faq.a1') },
  { question: t('faq.q2'), answer: t('faq.a2') },
  { question: t('faq.q3'), answer: t('faq.a3') },
  { question: t('faq.q4'), answer: t('faq.a4') },
  { question: t('faq.q5'), answer: t('faq.a5') },
  { question: t('faq.q6'), answer: t('faq.a6') },
])

function openItem(index: number) {
  if (openIndex.value === index || isSwitching.value) return
  isSwitching.value = true
  openIndex.value = -1

  if (switchTimer) window.clearTimeout(switchTimer)
  switchTimer = window.setTimeout(() => {
    openIndex.value = index
    isSwitching.value = false
    switchTimer = null
  }, 280)
}

onBeforeUnmount(() => {
  if (switchTimer) window.clearTimeout(switchTimer)
})
</script>

<template>
  <div
    class="relative mx-auto flex h-full w-full max-w-5xl flex-col items-center justify-center gap-4 pt-2 pb-6"
  >
    <PageHeroCard
      :title="t('faq.title')"
      :description="t('faq.subtitle')"
      icon="lucide:help-circle"
    />
    <div class="relative mt-2 flex flex-col gap-2">
      <details
        v-for="(item, idx) in faqItems"
        :key="idx"
        class="faq-item group overflow-hidden rounded-[14px] bg-neutral-950/85 backdrop-blur-sm"
        :open="openIndex === idx"
      >
        <summary
          class="flex cursor-pointer list-none items-center gap-3 px-4 py-3"
          @click.prevent="openItem(idx)"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-[10px] bg-neutral-900 text-xs font-semibold"
          >
            {{ idx + 1 }}
          </span>
          <span class="text-sm font-medium text-white">{{ item.question }}</span>
          <Icon
            icon="lucide:chevron-down"
            class="faq-icon ml-auto size-4 shrink-0 text-neutral-500 transition-transform duration-300"
          />
        </summary>
        <div class="faq-content grid border-t border-neutral-800/50 px-4">
          <p class="overflow-hidden py-3 text-sm leading-relaxed text-neutral-300">
            {{ item.answer }}
          </p>
        </div>
      </details>
    </div>
  </div>
</template>

<style scoped>
.faq-item {
  transition: border-color 0.2s ease;
}

.faq-item[open] {
  border-color: rgb(101 163 13 / 0.65);
}

.faq-item .faq-content {
  grid-template-rows: 0fr;
}

.faq-item[open] .faq-content {
  grid-template-rows: 1fr;
}

.faq-item[open] .faq-icon {
  transform: rotate(180deg);
}
</style>
