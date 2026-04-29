<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { locale, initLocale } from '@/i18n/i18n.ts'
import AppLayout from '@/components/layout/AppLayout.vue'
import Toaster from '@/components/ui/toast/Toaster.vue'
import { i18n } from '@/i18n/i18n.ts'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

watch(
  () => locale.value,
  (locale) => {
    i18n.global.locale.value = locale
  },
  { immediate: true },
)

onMounted(async () => {
  initLocale()

  if (auth.isTelegram || import.meta.env.DEV) {
    await auth.init()
    if (auth.isAuthenticated) {
      await router.replace({ name: 'home' })
    } else {
      await router.replace({ name: 'login' })
    }
    return
  }

  // Standalone mode: try to restore session from localStorage token
  const token = localStorage.getItem('auth_token')
  if (token) {
    await auth.fetchProfile()
    if (auth.isAuthenticated) {
      await router.replace({ name: 'home' })
      return
    }
    // Token expired or invalid — clear it
    auth.logout()
  }

  await router.replace({ name: 'login' })
})
</script>

<template>
  <AppLayout>
    <RouterView v-slot="{ Component, route }">
      <Transition name="page-transition" mode="out-in">
        <div :key="route.fullPath" class="page-transition-view">
          <component :is="Component" />
        </div>
      </Transition>
    </RouterView>
  </AppLayout>

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
