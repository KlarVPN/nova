<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { motion } from 'motion-v'
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
const tabsContainerRef = ref<HTMLElement | null>(null)
const tabRefs = ref<Record<string, HTMLElement | null>>({})
const bubbleY = ref(0)
const bubbleHeight = ref(0)
const bubbleReady = ref(false)

function setTabRef(path: string, el: unknown) {
  tabRefs.value[path] = (el as HTMLElement | null) ?? null
}

function syncDesktopBubble() {
  const container = tabsContainerRef.value
  const activeEl = tabRefs.value[active.value]
  if (!container || !activeEl) {
    bubbleReady.value = false
    return
  }

  const containerRect = container.getBoundingClientRect()
  const activeRect = activeEl.getBoundingClientRect()
  bubbleY.value = activeRect.top - containerRect.top - 3
  bubbleHeight.value = activeRect.height + 6
  bubbleReady.value = true
}

watch(active, async () => {
  await nextTick()
  syncDesktopBubble()
})

onMounted(() => {
  void nextTick(syncDesktopBubble)
  window.addEventListener('resize', syncDesktopBubble)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncDesktopBubble)
})

function navigate(path: string) {
  if (active.value === path) return
  hapticImpact('light')
  router.push(path)
}
</script>

<template>
  <nav
    class="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-center bg-black/10 py-4 backdrop-blur-md md:top-0 md:bottom-auto md:h-dvh md:w-48 md:flex-col md:items-start md:bg-black/25 md:px-6 md:py-6"
    style="padding-bottom: max(env(safe-area-inset-bottom), 16px)"
  >
    <div class="font-logo hidden flex-row items-center gap-2 text-sm font-bold md:flex">
      <Logotype class="size-6" /> KLAR
    </div>
    <div
      ref="tabsContainerRef"
      class="relative flex w-full max-w-md justify-around px-4 md:h-full md:max-w-none md:flex-col md:items-start md:justify-center md:gap-4 md:px-0"
    >
      <motion.div
        v-if="bubbleReady"
        class="pointer-events-none absolute hidden rounded-xl bg-neutral-900/80 shadow-[0_10px_30px_rgba(0,0,0,0.45)] md:block"
        :initial="false"
        :animate="{ y: bubbleY, height: bubbleHeight, opacity: 1 }"
        :transition="{ type: 'spring', stiffness: 380, damping: 34, mass: 0.52 }"
        style="left: -6px; right: -6px; top: 0"
      />
      <button
        v-for="tab in tabs"
        :key="tab.path"
        :ref="(el) => setTabRef(tab.path, el)"
        type="button"
        class="relative flex min-w-16 cursor-pointer flex-col items-center gap-1 overflow-hidden rounded-xl px-2 py-1.5 text-[10px] font-medium transition-all duration-200 md:w-full md:min-w-0 md:flex-row md:gap-1.5 md:gap-2 md:py-2 md:text-sm"
        :class="active === tab.path ? 'text-white' : 'text-neutral-400'"
        @click="navigate(tab.path)"
      >
        <Icon :icon="tab.icon!" class="relative z-10 size-5" :stroke-width="1.8" />
        <span class="relative z-10">{{ tab.label }}</span>
      </button>
    </div>
    <div class="hidden flex-row items-center gap-2 text-xs opacity-20 md:flex">@ 2026 KLAR</div>
  </nav>
</template>
