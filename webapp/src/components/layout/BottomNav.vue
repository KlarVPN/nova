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
  { path: '/', label: t('nav.home'), isLogotype: true },
  { path: '/setup', icon: 'lucide:settings', label: t('nav.setup') },
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
    class="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-center border-t border-white/5 bg-black/10 py-4 backdrop-blur-md"
    style="padding-bottom: max(env(safe-area-inset-bottom), 16px)"
  >
    <div class="flex w-full max-w-md justify-around px-4">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        type="button"
        class="flex min-w-16 cursor-pointer flex-col items-center gap-1 text-xs font-medium transition-all duration-200"
        :class="active === tab.path ? 'scale-105 text-white' : 'text-neutral-400 active:scale-95'"
        @click="navigate(tab.path)"
      >
        <Logotype v-if="tab.isLogotype" :size="20" />
        <Icon v-else :icon="tab.icon!" class="size-5" :stroke-width="1.8" />
        <span>{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>
