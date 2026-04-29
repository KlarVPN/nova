<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import BottomNav from './BottomNav.vue'

const route = useRoute()
const showBottomNav = computed(() => route.name !== 'plans')
</script>

<template>
  <div class="relative h-dvh w-dvw overflow-hidden bg-[#010101]">
    <div
      class="h-dvh overflow-y-auto p-3 [-webkit-overflow-scrolling:touch] [scrollbar-width:none]"
      :class="showBottomNav ? 'pb-16' : 'pb-3'"
    >
      <slot />
    </div>
    <BottomNav v-if="showBottomNav" />
  </div>
</template>
