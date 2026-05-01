<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: string
  }>(),
  {
    as: 'div',
  },
)
</script>

<template>
  <component :is="as" class="animate-pulse rounded-[14px] bg-neutral-900" />
</template>
