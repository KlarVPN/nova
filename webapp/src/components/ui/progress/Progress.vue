<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  value?: number
  max?: number
  class?: HTMLAttributes['class']
  indicatorClass?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  value: 0,
  max: 100,
})

const percentage = () => Math.min(100, Math.max(0, ((props.value ?? 0) / (props.max ?? 100)) * 100))
</script>

<template>
  <div
    :class="cn('bg-secondary relative h-2 w-full overflow-hidden rounded-full', props.class)"
    role="progressbar"
    :aria-valuenow="value"
    :aria-valuemax="max"
  >
    <div
      :class="cn('bg-accent h-full transition-all duration-500 ease-out', indicatorClass)"
      :style="{ width: `${percentage()}%` }"
    />
  </div>
</template>
