<script lang="ts" setup>
const props = defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<template>
  <div class="flex w-full flex-col gap-2">
    <h1 class="text-3xl leading-[0.9] font-extrabold tracking-tighter text-white uppercase">
      {{ props.title }}
    </h1>
    <p v-if="props.subtitle" class="text-sm text-neutral-400">{{ props.subtitle }}</p>
  </div>
</template>
