<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import { cn, formatDateE } from '@/lib/utils.ts'
import type { ActiveSubscription } from '@/types'
import { computed } from 'vue'
const { t } = useI18n()

const props = defineProps<{
  type: 'none' | 'expired' | 'disabled' | 'active'
  sub?: ActiveSubscription
}>()

const statusIcon = computed(() => {
  switch (props.type) {
    case 'none':
      return 'lucide:shield-off'
    case 'expired':
      return 'lucide:clock-alert'
    case 'disabled':
      return 'lucide:ban'
    case 'active':
      return 'lucide:check'
  }
})

const noSubTitle = computed(() => {
  switch (props.type) {
    case 'none':
      return t('home.noSubTitle')
    case 'expired':
      return t('status.expired')
    case 'disabled':
      return t('status.disabled')
    case 'active':
      return t('status.active')
  }
})

const noSub = computed(() => {
  switch (props.type) {
    case 'none':
      return t('home.noSub')
    case 'expired':
      return t('home.expiredDesc')
    case 'disabled':
      return t('home.disabledDesc')
    case 'active':
      return t('home.until', { date: formatDateE(props.sub?.end_date || '') })
  }
})
</script>

<template>
  <div class="flex flex-col items-center gap-5 pt-6">
    <span :class="cn('flex rounded-full p-3', props.type ? 'bg-lime-accent' : 'bg-white')">
      <Icon :icon="statusIcon" class="animate-pulse-glow size-12 text-black" />
    </span>
    <div class="flex flex-col gap-1">
      <span class="text-3xl leading-[0.9] font-extrabold tracking-tighter uppercase">
        {{ noSubTitle }}
      </span>
      <p class="text-sm text-neutral-400">{{ noSub }}</p>
    </div>
  </div>
</template>

<style scoped>
@keyframes pulse-glow {
  0%,
  100% {
    filter: drop-shadow(0 0 8px currentColor);
  }
  50% {
    filter: drop-shadow(0 0 20px currentColor) drop-shadow(0 0 35px currentColor);
  }
}

.animate-pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}
</style>
