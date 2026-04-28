<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { isTelegramWebApp } from '@/lib/telegram'
import { locale, initLocale } from '@/i18n/i18n.ts'
import AppLayout from '@/components/layout/AppLayout.vue'
import AuthErrorView from '@/views/AuthErrorView.vue'
import Toaster from '@/components/ui/toast/Toaster.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
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
      <template v-if="auth.loading && !auth.profile">
        <div class="flex min-h-[80vh] items-center justify-center">
          <LoadingSpinner size="lg" :text="t('common.loading')" />
        </div>
      </template>
      <template v-else-if="auth.error && !auth.profile">
        <div class="flex min-h-[80vh] flex-col items-center justify-center gap-5 px-8 text-center">
          <span class="flex rounded-full bg-neutral-900 p-4">
            <Icon icon="lucide:wifi-off" class="size-10 text-neutral-400" />
          </span>
          <div>
            <h2 class="text-xl font-extrabold uppercase tracking-tighter text-white">
              {{ t('common.error') }}
            </h2>
            <p class="mt-1 text-sm text-neutral-400">{{ auth.error }}</p>
          </div>
          <button
            class="h-10 cursor-pointer bg-white px-6 text-sm font-bold uppercase text-black"
            @click="auth.init()"
          >
            {{ t('common.retry') }}
          </button>
        </div>
      </template>
      <template v-else>
        <RouterView />
      </template>
    </AppLayout>
  </template>

  <Toaster />
</template>
