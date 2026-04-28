<script setup lang="ts">
import { Icon } from '@iconify/vue'
</script>
<template>
  <div class="flex fixed top-2 left-1/2 -translate-x-1/2 w-[calc(100%-1rem)] border border-red-500 bg-red-500/10 text-white gap-2 p-2 pr-3 items-center z-50">
    <Icon icon="lucide:info" class="size-4 shrink-0" />
    <span class="text-xs font-semibold leading-[0.9]">VPN отключён, реальный IP и локация видны!</span>
  </div>
</template>
