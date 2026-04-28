<script setup lang="ts">
import BottomNav from './BottomNav.vue'
</script>

<template>
  <div class="relative h-dvh w-dvw overflow-hidden bg-[#010101]">
    <div
      class="h-dvh overflow-y-auto p-3 [-webkit-overflow-scrolling:touch] [scrollbar-width:none]"
    >
      <slot />
    </div>
    <BottomNav />
  </div>
</template>
