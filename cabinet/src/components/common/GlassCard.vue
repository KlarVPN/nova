<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

defineProps<{
  class?: HTMLAttributes['class']
  glow?: boolean
  subtle?: boolean
}>()
</script>

<template>
  <div
    :class="
      cn(
        'rounded-2xl p-4 transition-all duration-200',
        subtle ? 'glass-subtle' : 'glass',
        glow && 'glow-accent',
        $props.class,
      )
    "
  >
    <slot />
  </div>
</template>
