<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    class?: HTMLAttributes['class']
    disabled?: boolean
    loading?: boolean
  }>(),
  {
    disabled: false,
    loading: false,
  },
)
</script>

<template>
  <button
    :class="
      cn(
        'flex w-full cursor-pointer items-center justify-center gap-2 rounded-full bg-white px-4.5 py-3 font-sans font-medium tracking-tight text-black transition-all hover:bg-neutral-200',
        props.disabled ? 'cursor-not-allowed opacity-50' : '',
        props.class,
      )
    "
  >
    <slot />
  </button>
</template>
