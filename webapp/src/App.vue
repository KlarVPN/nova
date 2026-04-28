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

const { t } = useI18n()
const auth = useAuthStore()

const isTelegram = isTelegramWebApp() || import.meta.env.DEV

watch(
  () => locale.value,
  (locale) => {
    i18n.global.locale.value = locale
  },
  { immediate: true },
)

onMounted(() => {
  initLocale()
  if (isTelegram) auth.init()
})
</script>

<template>
  <template v-if="!isTelegram">
    <AuthErrorView />
  </template>

  <template v-else>
    <AppLayout>
      <RouterView />
    </AppLayout>
  </template>

  <Toaster />
</template>
