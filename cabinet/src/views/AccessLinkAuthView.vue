<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const { error } = useToast()

onMounted(async () => {
  const uuid = String(route.params.uuid || '').trim()
  if (!uuid) {
    await router.replace({ name: 'login' })
    return
  }

  try {
    const res = await api.auth.loginByAccessLink(uuid)
    localStorage.setItem('auth_token', res.token)
    await auth.fetchProfile()
    if (auth.isAuthenticated) {
      await router.replace({ name: 'home' })
      return
    }
  } catch {
    error(t('accessLinkAuth.invalid'))
  }

  await router.replace({ name: 'login' })
})
</script>

<template>
  <div class="mx-auto flex min-h-dvh w-full max-w-5xl items-center justify-center px-6 py-10">
    <p class="text-sm text-neutral-400">{{ t('accessLinkAuth.loading') }}</p>
  </div>
</template>
