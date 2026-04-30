<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
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
const telegramWidgetHost = ref<HTMLDivElement | null>(null)

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME as string | undefined

type TelegramAuthUser = Record<string, unknown>

declare global {
  interface Window {
    TelegramOnAuthCb?: (user: TelegramAuthUser) => void
  }
}

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
  if (TELEGRAM_BOT_USERNAME && telegramWidgetHost.value) {
    window.TelegramOnAuthCb = (user: TelegramAuthUser) => {
      void loginWithTelegram(user)
    }

    const script = document.createElement('script')
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.async = true
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME)
    script.setAttribute('data-size', 'large')
    script.setAttribute('data-radius', '12')
    script.setAttribute('data-request-access', 'write')
    script.setAttribute('data-onauth', 'TelegramOnAuthCb(user)')
    script.setAttribute('data-userpic', 'false')

    telegramWidgetHost.value.innerHTML = ''
    telegramWidgetHost.value.appendChild(script)
  }

  const params = new URLSearchParams(window.location.search)
  if (!params.get('hash') && window.location.hash.includes('?')) {
    const hashQuery = window.location.hash.split('?')[1] ?? ''
    const hashParams = new URLSearchParams(hashQuery)
    hashParams.forEach((value, key) => params.set(key, value))
  }

  if (!params.get('hash')) {
    const tgAuthRaw = window.location.hash.match(/tgAuthResult=([^&]+)/)?.[1]
    if (tgAuthRaw) {
      try {
        const decoded = decodeURIComponent(tgAuthRaw)

        // Variant 1: query-like payload (k=v&k2=v2)
        const tgParams = new URLSearchParams(decoded)
        if (tgParams.get('hash')) {
          tgParams.forEach((value, key) => params.set(key, value))
        } else {
          // Variant 2: base64/base64url JSON payload
          const normalized = decoded.replace(/-/g, '+').replace(/_/g, '/')
          const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
          const jsonText = atob(padded)
          const data = JSON.parse(jsonText) as Record<string, unknown>
          Object.entries(data).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
              params.set(key, String(value))
            }
          })
        }
      } catch {
        // leave params as-is; normal validation below will stop auth flow
      }
    }
  }
  if (!params.get('hash') || !params.get('id') || !params.get('auth_date')) return

  const authPayload: TelegramAuthUser = {}
  params.forEach((value, key) => {
    authPayload[key] = value
  })

  window.history.replaceState({}, '', `${window.location.pathname}${window.location.hash}`)

  void loginWithTelegram(authPayload)
})

onBeforeUnmount(() => {
  delete window.TelegramOnAuthCb
})

function startTelegramOauthFallback() {
  const botId = import.meta.env.VITE_TELEGRAM_BOT_ID as string | undefined
  if (!botId) {
    toastError('VITE_BOT_USERNAME or VITE_TELEGRAM_BOT_ID is not configured')
    return
  }

  const origin = window.location.origin
  const returnTo = `${origin}/app/login`
  const url = new URL('https://oauth.telegram.org/auth')
  url.searchParams.set('bot_id', botId)
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
    <div class="relative flex w-full max-w-sm flex-col items-center gap-3">
      <div ref="telegramWidgetHost" class="telegram-widget-hitbox" />
      <Button type="button" class="w-full" :disabled="submitting" @click="startTelegramOauthFallback">
        <Icon icon="lucide:send" class="mr-2 h-4 w-4" />
        {{ t('login.telegramBtn') }}
      </Button>

      <p v-if="t('login.noKey')" class="text-muted-foreground text-center text-xs leading-relaxed">
        {{ t('login.noKey') }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.telegram-widget-hitbox {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  opacity: 0.001;
  overflow: hidden;
  z-index: 2;
}

.telegram-widget-hitbox :deep(iframe) {
  width: 100% !important;
  min-width: 100% !important;
}
</style>
