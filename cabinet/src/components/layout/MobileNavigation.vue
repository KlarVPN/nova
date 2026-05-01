<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { motion } from 'motion-v'
import { hapticImpact } from '@/lib/telegram'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const tabs = computed(() => [
  { path: '/', label: t('nav.home'), icon: 'lucide:home' },
  { path: '/setup', icon: 'lucide:settings', label: t('nav.setup') },
  { path: '/locations', icon: 'lucide:map', label: t('nav.locations') },
  { path: '/profile', icon: 'lucide:user', label: t('nav.profile') },
  { path: '/support', icon: 'lucide:headset', label: t('nav.support') },
])

const active = computed(() => route.path)
const tabsContainerRef = ref<HTMLElement | null>(null)
const tabRefs = ref<Record<string, HTMLElement | null>>({})
const bubbleX = ref(0)
const bubbleWidth = ref(0)
const bubbleReady = ref(false)

function setTabRef(path: string, el: unknown) {
  tabRefs.value[path] = (el as HTMLElement | null) ?? null
}

function syncBubble() {
  const container = tabsContainerRef.value
  const activeEl = tabRefs.value[active.value]
  if (!container || !activeEl) {
    bubbleReady.value = false
    return
  }

  const containerRect = container.getBoundingClientRect()
  const activeRect = activeEl.getBoundingClientRect()
  bubbleX.value = activeRect.left - containerRect.left - 3
  bubbleWidth.value = activeRect.width + 6
  bubbleReady.value = true
}

watch(active, async () => {
  await nextTick()
  syncBubble()
})

onMounted(() => {
  void nextTick(syncBubble)
  window.addEventListener('resize', syncBubble)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncBubble)
})

function navigate(path: string) {
  if (active.value === path) return
  hapticImpact('light')
  router.push(path)
}
</script>

<template>
  <nav
    class="fixed right-3 bottom-3 left-3 z-50 flex items-center justify-center rounded-full bg-neutral-900/45 p-1 backdrop-blur-xl"
  >
    <div
      class="pointer-events-none absolute top-full right-0 left-0 h-16 rounded-b-full bg-linear-to-b from-transparent to-black/80"
    />

    <div ref="tabsContainerRef" class="relative flex w-full max-w-md justify-around px-1">
      <motion.div
        v-if="bubbleReady"
        class="pointer-events-none absolute rounded-full bg-white/12"
        :initial="false"
        :animate="{ x: bubbleX, width: bubbleWidth, opacity: 1 }"
        :transition="{ type: 'spring', stiffness: 380, damping: 34, mass: 0.52 }"
        style="top: 0; bottom: 0; left: 0"
      />

      <button
        v-for="tab in tabs"
        :key="tab.path"
        :ref="(el) => setTabRef(tab.path, el)"
        type="button"
        class="relative flex flex-1 cursor-pointer flex-col items-center gap-1 overflow-hidden rounded-2xl px-3 py-4 text-[10px] font-medium transition-all duration-200"
        :class="active === tab.path ? 'text-white' : 'text-neutral-400'"
        @click="navigate(tab.path)"
      >
        <Icon :icon="tab.icon!" class="relative z-10 size-5" :stroke-width="1.8" />
      </button>
    </div>
  </nav>
</template>
