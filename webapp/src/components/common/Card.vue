<script setup lang="ts">
import { type HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    class="flex w-full flex-col gap-2 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 py-2 text-neutral-400"
    :class="props.class"
  >
    <slot />
  </div>
</template>
