<script setup lang="ts">
import BottomNav from './BottomNav.vue'
</script>

<template>
  <div class="relative h-dvh w-dvw overflow-hidden bg-[#010101]">
    <div
      class="h-[calc(100%-4rem)] overflow-y-auto [-webkit-overflow-scrolling:touch] [scrollbar-width:none]"
    >
      <slot />
    </div>
    <BottomNav />
  </div>
</template>
