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
      return 'lucide:x'
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
  <div class="flex flex-1 flex-col items-center justify-center gap-5 pt-6">
    <span
      :class="
        cn(
          'flex rounded-full',
          props.type === 'active' ? 'animate-pulse-glow bg-lime-accent p-4' : 'bg-white p-6',
        )
      "
    >
      <Icon
        :icon="statusIcon"
        :class="cn('text-black', props.type === 'active' ? 'size-12' : 'size-10')"
      />
    </span>
    <div :class="cn('flex flex-col', props.type === 'active' ? 'gap-1' : 'gap-3')">
      <span class="text-4xl leading-[0.9] font-extrabold tracking-tighter uppercase">
        {{ noSubTitle }}
      </span>
      <p class="text-base text-neutral-400">{{ noSub }}</p>
    </div>
  </div>
</template>

<style scoped>
@keyframes pulse-glow {
  0%,
  100% {
    filter: drop-shadow(0 0 8px oklch(0.319 0.234351 126.141));
  }
  50% {
    filter: drop-shadow(0 0 20px oklch(0.319 0.234351 126.141))
      drop-shadow(0 0 35px oklch(0.319 0.234351 126.141));
  }
}

.animate-pulse-glow {
  animation: pulse-glow 4s ease-in-out infinite;
}
</style>
