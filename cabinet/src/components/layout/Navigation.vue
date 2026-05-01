<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import MobileNavigation from './MobileNavigation.vue'
import DesktopNavigation from './DesktopNavigation.vue'

const isDesktop = ref(false)
let mediaQuery: MediaQueryList | null = null

function syncViewport() {
  isDesktop.value = window.matchMedia('(min-width: 768px)').matches
}

onMounted(() => {
  mediaQuery = window.matchMedia('(min-width: 768px)')
  isDesktop.value = mediaQuery.matches
  mediaQuery.addEventListener('change', syncViewport)
})

onUnmounted(() => {
  mediaQuery?.removeEventListener('change', syncViewport)
  mediaQuery = null
})
</script>

<template>
  <DesktopNavigation v-if="isDesktop" />
  <MobileNavigation v-else />
</template>
