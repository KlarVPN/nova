<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { isTelegramWebApp } from '@/lib/telegram'
import { locale, initLocale } from '@/i18n/i18n.ts'
import AppLayout from '@/components/layout/AppLayout.vue'
import AuthErrorView from '@/views/AuthErrorView.vue'
import Toaster from '@/components/ui/toast/Toaster.vue'
import { i18n } from '@/i18n/i18n.ts'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const isTelegram = isTelegramWebApp() || import.meta.env.DEV

watch(
  () => locale.value,
  (locale) => {
    i18n.global.locale.value = locale
  },
  { immediate: true },
)

onMounted(async () => {
  initLocale()
  if (!isTelegram) return

  try {
    await auth.init()
  } finally {
    await router.replace({ name: 'home' })
  }
})
</script>

<template>
  <template v-if="!isTelegram">
    <AuthErrorView />
  </template>

  <template v-else>
    <AppLayout>
      <RouterView v-slot="{ Component, route }">
        <Transition name="page-transition" mode="out-in">
          <div :key="route.fullPath" class="page-transition-view">
            <component :is="Component" />
          </div>
        </Transition>
      </RouterView>
    </AppLayout>
  </template>

  <Toaster />
</template>

<style scoped>
.page-transition-enter-active,
.page-transition-leave-active {
  transition:
    opacity 220ms ease,
    transform 220ms ease;
  will-change: opacity, transform;
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.page-transition-view {
  min-height: 100%;
}
</style>
