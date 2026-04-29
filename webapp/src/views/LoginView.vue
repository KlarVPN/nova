<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import Logotype from '@/components/common/Logotype.vue'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const { error: toastError } = useToast()

const submitting = ref(false)

const TELEGRAM_BOT_ID = import.meta.env.VITE_TELEGRAM_BOT_ID as string | undefined

type TelegramAuthUser = Record<string, unknown>

async function loginWithTelegram(user: TelegramAuthUser) {
  submitting.value = true
  const result = await auth.loginByTelegram(user)
  submitting.value = false

  if (result.ok) {
    router.replace({ name: 'home' })
  } else {
    const msg = result.error ?? t('login.error')
    toastError(msg)
  }
}


onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  if (!params.get('hash') || !params.get('id') || !params.get('auth_date')) return

  const authPayload: TelegramAuthUser = {}
  params.forEach((value, key) => {
    authPayload[key] = value
  })

  window.history.replaceState({}, '', `${window.location.pathname}${window.location.hash}`)

  void loginWithTelegram(authPayload)
})
function startTelegramOauth() {
  if (!TELEGRAM_BOT_ID) {
    toastError('VITE_TELEGRAM_BOT_ID is not configured')
    return
  }

  const origin = window.location.origin
  const returnTo = `${origin}${window.location.pathname}#/login`
  const url = new URL('https://oauth.telegram.org/auth')
  url.searchParams.set('bot_id', TELEGRAM_BOT_ID)
  url.searchParams.set('origin', origin)
  url.searchParams.set('return_to', returnTo)
  url.searchParams.set('request_access', 'write')
  window.location.assign(url.toString())
}
</script>

<template>
  <div class="mx-auto flex min-h-dvh w-full max-w-5xl flex-col items-center justify-center gap-8 px-6 py-10">
    <!-- Logo -->
    <Logotype class="h-10" />

    <!-- Heading -->
    <div class="space-y-1.5 text-center">
      <h1 class="text-foreground text-2xl font-semibold tracking-tight">
        {{ t('login.title') }}
      </h1>
      <p class="text-muted-foreground text-sm">
        {{ t('login.subtitle') }}
      </p>
    </div>

    <!-- Telegram OAuth 2.0 -->
    <div class="flex w-full max-w-sm flex-col items-center gap-3">
      <Button type="button" class="w-full" :disabled="submitting" @click="startTelegramOauth">
        <Icon icon="lucide:send" class="mr-2 h-4 w-4" />
        {{ t('login.telegramBtn') }}
      </Button>

      <p v-if="t('login.noKey')" class="text-muted-foreground text-center text-xs leading-relaxed">
        {{ t('login.noKey') }}
      </p>
    </div>
  </div>
</template>
