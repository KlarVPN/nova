<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import Logotype from '@/components/common/Logotype.vue'
import { hapticImpact } from '@/lib/telegram'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const tabs = computed(() => [
  { path: '/', label: t('nav.home'), icon: 'lucide:home' },
  { path: '/setup', icon: 'lucide:settings', label: t('nav.setup') },
  { path: '/locations', icon: 'lucide:map-pin', label: t('nav.locations') },
  { path: '/profile', icon: 'lucide:user', label: t('nav.profile') },
  { path: '/support', icon: 'lucide:headset', label: t('nav.support') },
])

const active = computed(() => route.path)

function navigate(path: string) {
  if (active.value === path) return
  hapticImpact('light')
  router.push(path)
}
</script>

<template>
  <nav
    class="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-center border-t border-white/5 bg-black/10 py-4 backdrop-blur-md md:top-0 md:bottom-auto md:h-dvh md:w-32 md:flex-col md:border-t-0 md:border-r md:border-white/10 md:bg-black/25 md:py-6"
    style="padding-bottom: max(env(safe-area-inset-bottom), 16px)"
  >
    <div class="font-logo hidden flex-row items-center gap-2 text-sm font-bold md:flex">
      <Logotype class="size-6" /> KLAR
    </div>
    <div
      class="flex w-full max-w-md justify-around px-4 md:h-full md:max-w-none md:flex-col md:items-center md:justify-center md:gap-4 md:px-2"
    >
      <button
        v-for="tab in tabs"
        :key="tab.path"
        type="button"
        class="flex min-w-16 cursor-pointer flex-col items-center gap-1 rounded-xl px-2 py-1.5 text-[10px] font-medium transition-all duration-200 md:w-full md:min-w-0 md:gap-1.5 md:py-2"
        :class="active === tab.path ? 'scale-105 text-white' : 'text-neutral-400 active:scale-95'"
        @click="navigate(tab.path)"
      >
        <Icon :icon="tab.icon!" class="size-5" :stroke-width="1.8" />
        <span>{{ tab.label }}</span>
      </button>
    </div>
    <div class="hidden flex-row items-center gap-2 text-xs opacity-20 md:flex">@ 2026 KLAR</div>
  </nav>
</template>
