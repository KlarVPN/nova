<script setup lang="ts">
import { Icon } from '@iconify/vue'

defineProps<{
  icon: string
  title: string
  description: string
}>()
</script>

<template>
  <div class="flex flex-col gap-3 rounded-[14px] bg-neutral-950 p-5 pr-25">
    <span class="flex w-fit items-center justify-center rounded-[14px] bg-white/5 p-4">
      <Icon :icon="icon" class="size-8 opacity-60" />
    </span>
    <h1 class="mt-1 text-2xl leading-[0.9] font-medium tracking-tight text-balance text-white">
      {{ title }}
    </h1>
    <p class="text-sm text-balance opacity-60">
      {{ description }}
    </p>
  </div>
</template>
