<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { motion } from 'motion-v'
import Logotype from '@/components/common/Logotype.vue'
import { hapticImpact } from '@/lib/telegram'
import { getActiveNavPath, getNavigationTabs, isNavTabActive } from '@/lib/navigation'
import packageJson from '../../../package.json'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const tabs = computed(() => getNavigationTabs(t))

const active = computed(() => getActiveNavPath(route.path, tabs.value.map((tab) => tab.path)))
const appVersion = packageJson.version
const tabsContainerRef = ref<HTMLElement | null>(null)
const tabRefs = ref<Record<string, HTMLElement | null>>({})
const bubbleY = ref(0)
const bubbleHeight = ref(0)
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
  bubbleY.value = activeRect.top - containerRect.top - 3
  bubbleHeight.value = activeRect.height + 6
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
    class="fixed top-0 left-0 z-50 flex h-dvh w-48 flex-col items-start bg-black/25 px-6 py-6 backdrop-blur-md"
  >
    <div class="font-logo flex flex-row items-center gap-2 text-sm font-bold">
      <Logotype class="size-6" /> KLAR
    </div>

    <div
      ref="tabsContainerRef"
      class="relative flex h-full w-full max-w-none flex-col items-start justify-center gap-4 px-0"
    >
      <motion.div
        v-if="bubbleReady"
        class="pointer-events-none absolute rounded-xl bg-neutral-900/80 shadow-[0_10px_30px_rgba(0,0,0,0.45)]"
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
        class="relative flex w-full min-w-0 cursor-pointer flex-row items-center gap-2 overflow-hidden rounded-xl px-2 py-2 text-sm font-medium transition-all duration-200"
        :class="isNavTabActive(route.path, tab.path) ? 'text-white' : 'text-neutral-400'"
        @click="navigate(tab.path)"
      >
        <Icon :icon="tab.icon!" class="relative z-10 size-5" :stroke-width="1.8" />
        <span class="relative z-10">{{ tab.label }}</span>
      </button>
    </div>

    <div class="flex flex-col items-start text-xs opacity-20">
      <div>v{{ appVersion }}</div>
      <div>@ 2026 KLAR</div>
    </div>
  </nav>
</template>
