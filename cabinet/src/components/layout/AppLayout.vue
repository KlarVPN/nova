<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BottomNav from './BottomNav.vue'

const route = useRoute()
const auth = useAuthStore()
const isDesktop = ref(false)

function syncViewport() {
  isDesktop.value = window.matchMedia('(min-width: 768px)').matches
}

onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewport)
})

const showBottomNav = computed(
  () => auth.isAuthenticated && (route.name !== 'plans' || isDesktop.value),
)
</script>

<template>
  <div class="relative h-dvh w-full overflow-hidden bg-[#010101]">
    <div
      class="h-dvh overflow-y-auto px-4 pt-3 [-webkit-overflow-scrolling:touch] [scrollbar-width:none] md:px-12"
      :class="showBottomNav ? 'pb-16 md:pb-4 md:pl-32' : 'pb-3'"
    >
      <div class="mx-auto w-full max-w-lg">
        <slot />
      </div>
    </div>
    <BottomNav v-if="showBottomNav" />
  </div>
</template>
