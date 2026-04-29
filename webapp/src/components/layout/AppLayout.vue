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
  <div class="relative h-dvh w-full overflow-hidden bg-[#010101]">
    <div
      class="h-dvh overflow-y-auto px-3 pt-3 [-webkit-overflow-scrolling:touch] [scrollbar-width:none]"
      :class="showBottomNav ? 'pb-16 md:pb-4 md:pl-28' : 'pb-3'"
    >
      <div class="mx-auto w-full max-w-6xl">
        <slot />
      </div>
    </div>
    <BottomNav v-if="showBottomNav" />
  </div>
</template>
