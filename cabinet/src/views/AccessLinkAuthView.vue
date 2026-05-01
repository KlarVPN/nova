<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/components/ui/toast'
import { api, ApiError } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const { error } = useToast()

onMounted(async () => {
  const uuid = String(route.params.uuid || '').trim()
  if (!uuid) {
    console.error('[access-link-auth] Missing access UUID', {
      path: route.fullPath,
      params: route.params,
    })
    error(t('accessLinkAuth.missing'))
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
  } catch (e: unknown) {
    const detail = e instanceof ApiError ? e.detail : e instanceof Error ? e.message : String(e)
    const message = e instanceof ApiError && e.status === 401 ? t('accessLinkAuth.invalid') : t('accessLinkAuth.failed')
    console.error('[access-link-auth] Login failed', {
      uuid,
      path: route.fullPath,
      error: e,
      detail,
    })
    error(message)
  }

  await router.replace({ name: 'login' })
})
</script>

<template>
  <div class="mx-auto flex min-h-dvh w-full max-w-5xl items-center justify-center px-6 py-10">
    <p class="text-sm text-neutral-400">{{ t('accessLinkAuth.loading') }}</p>
  </div>
</template>
