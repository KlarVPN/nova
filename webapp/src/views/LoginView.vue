<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/components/ui/toast'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import Logotype from '@/components/common/Logotype.vue'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const { error: toastError } = useToast()

const key = ref('')
const submitting = ref(false)
const fieldError = ref('')

const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME as string | undefined
const telegramWidgetRef = ref<HTMLDivElement | null>(null)

type TelegramAuthUser = Record<string, unknown>

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramAuthUser) => void
  }
}

async function submit() {
  fieldError.value = ''
  const trimmed = key.value.trim()

  if (trimmed.split(/[-\s]+/).filter(Boolean).length !== 6) {
    fieldError.value = t('login.error')
    return
  }

  submitting.value = true
  const result = await auth.loginByKey(trimmed)
  submitting.value = false

  if (result.ok) {
    router.replace({ name: 'home' })
  } else {
    fieldError.value = result.error ?? t('login.error')
    toastError(fieldError.value)
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
  if (!BOT_USERNAME || !telegramWidgetRef.value) return

  window.onTelegramAuth = (user: TelegramAuthUser) => {
    void loginWithTelegram(user)
  }

  const script = document.createElement('script')
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.async = true
  script.setAttribute('data-telegram-login', BOT_USERNAME)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '12')
  script.setAttribute('data-request-access', 'write')
  script.setAttribute('data-userpic', 'false')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')

  telegramWidgetRef.value.innerHTML = ''
  telegramWidgetRef.value.appendChild(script)
})

onBeforeUnmount(() => {
  delete window.onTelegramAuth
})
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

    <!-- Key form -->
    <form class="flex w-full max-w-sm flex-col gap-3" @submit.prevent="submit">
      <div class="flex flex-col gap-1.5">
        <label class="text-foreground text-sm font-medium">
          {{ t('login.keyLabel') }}
        </label>
        <Input
          v-model="key"
          :placeholder="t('login.keyPlaceholder')"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="none"
          spellcheck="false"
          class="font-mono text-sm"
          :class="{ 'border-destructive': fieldError }"
          @input="fieldError = ''"
        />
        <p v-if="fieldError" class="text-destructive text-xs">{{ fieldError }}</p>
        <p v-else-if="t('login.keyHint')" class="text-muted-foreground text-xs">{{ t('login.keyHint') }}</p>
      </div>

      <Button type="submit" class="w-full" :disabled="submitting || !key.trim()">
        <Icon v-if="submitting" icon="lucide:loader-circle" class="mr-2 h-4 w-4 animate-spin" />
        {{ submitting ? t('login.submitting') : t('login.submit') }}
      </Button>
    </form>

    <!-- Divider -->
    <div class="flex w-full max-w-sm items-center gap-3">
      <div class="bg-border h-px flex-1" />
      <span class="text-muted-foreground text-xs">{{ t('login.orTelegram') }}</span>
      <div class="bg-border h-px flex-1" />
    </div>

    <!-- Telegram OAuth -->
    <div class="flex w-full max-w-sm flex-col items-center gap-3">
      <div ref="telegramWidgetRef" class="telegram-login-widget flex w-full justify-center" />

      <p v-if="t('login.noKey')" class="text-muted-foreground text-center text-xs leading-relaxed">
        {{ t('login.noKey') }}
      </p>
    </div>
  </div>
</template>

<style scoped>
:deep(.telegram-login-widget iframe) {
  width: 100% !important;
  max-width: 22rem;
}
</style>
