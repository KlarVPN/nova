<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BottomNav from './BottomNav.vue'

const route = useRoute()
const auth = useAuthStore()
const showBottomNav = computed(() => route.name !== 'plans' && auth.isAuthenticated)
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
