<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { locale, setLocale } from '@/i18n/i18n.ts'
import { hapticImpact, openLink } from '@/lib/telegram'

const auth = useAuthStore()
const { t } = useI18n()

const botUsername = import.meta.env.VITE_BOT_USERNAME
const channelUsername = import.meta.env.VITE_CHANNEL_USERNAME
const docsUrl = import.meta.env.VITE_DOCS_URL
const statusUrl = import.meta.env.VITE_STATUS_URL

const displayName = computed(() => {
  const p = auth.profile
  if (!p) return ''
  return [p.first_name, p.last_name].filter(Boolean).join(' ')
})

const userInitial = computed(() => displayName.value.charAt(0).toUpperCase() || '?')

function switchTo(lang: 'ru' | 'en') {
  if (locale.value === lang) return
  hapticImpact('light')
  setLocale(lang)
}

function openExternal(url: string) {
  hapticImpact('light')
  openLink(url)
}
</script>

<template>
  <div class="flex w-full flex-col gap-6 pt-4 pb-6">
    <h1 class="font-extrabold uppercase text-3xl leading-[0.9] tracking-tighter text-white">
      {{ t('nav.profile') }}
    </h1>

    <!-- User info -->
    <div
      v-if="auth.profile"
      class="flex items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3"
    >
      <div class="flex size-10 shrink-0 items-center justify-center bg-white">
        <span class="text-lg font-bold text-black">{{ userInitial }}</span>
      </div>
      <div class="min-w-0">
        <p class="truncate font-semibold text-white">{{ displayName }}</p>
        <p v-if="auth.profile.username" class="font-mono text-sm text-neutral-400">
          @{{ auth.profile.username }}
        </p>
      </div>
    </div>

    <!-- Language -->
    <div class="flex flex-col gap-3">
      <p class="font-mono text-xs uppercase tracking-wide text-neutral-500">
        {{ t('profile.language') }}
      </p>
      <div class="flex gap-2">
        <button
          class="flex h-10 flex-1 cursor-pointer items-center justify-center gap-2 border font-mono text-sm font-semibold uppercase tracking-wide transition-colors"
          :class="
            locale === 'ru'
              ? 'border-[#bdfe00] bg-neutral-900 text-[#bdfe00]'
              : 'border-neutral-800 bg-neutral-950 text-neutral-400'
          "
          @click="switchTo('ru')"
        >
          🇷🇺 RU
        </button>
        <button
          class="flex h-10 flex-1 cursor-pointer items-center justify-center gap-2 border font-mono text-sm font-semibold uppercase tracking-wide transition-colors"
          :class="
            locale === 'en'
              ? 'border-[#bdfe00] bg-neutral-900 text-[#bdfe00]'
              : 'border-neutral-800 bg-neutral-950 text-neutral-400'
          "
          @click="switchTo('en')"
        >
          🇬🇧 EN
        </button>
      </div>
    </div>

    <!-- Links -->
    <div class="flex flex-col gap-3">
      <p class="font-mono text-xs uppercase tracking-wide text-neutral-500">
        {{ t('profile.links') }}
      </p>
      <div class="flex flex-col gap-2">
        <button
          v-if="botUsername"
          class="flex h-12 w-full cursor-pointer items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:border-neutral-700"
          @click="openExternal(`https://t.me/${botUsername}`)"
        >
          <Icon icon="lucide:message-circle" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.support') }}</span>
          <Icon icon="lucide:external-link" class="ml-auto size-3 text-neutral-600" />
        </button>

        <button
          v-if="channelUsername"
          class="flex h-12 w-full cursor-pointer items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:border-neutral-700"
          @click="openExternal(`https://t.me/${channelUsername}`)"
        >
          <Icon icon="lucide:newspaper" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.news') }}</span>
          <Icon icon="lucide:external-link" class="ml-auto size-3 text-neutral-600" />
        </button>

        <button
          v-if="docsUrl"
          class="flex h-12 w-full cursor-pointer items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:border-neutral-700"
          @click="openExternal(docsUrl)"
        >
          <Icon icon="lucide:file-text" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.docs') }}</span>
          <Icon icon="lucide:external-link" class="ml-auto size-3 text-neutral-600" />
        </button>

        <button
          v-if="statusUrl"
          class="flex h-12 w-full cursor-pointer items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:border-neutral-700"
          @click="openExternal(statusUrl)"
        >
          <Icon icon="lucide:activity" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.status') }}</span>
          <Icon icon="lucide:external-link" class="ml-auto size-3 text-neutral-600" />
        </button>
      </div>
    </div>
  </div>
</template>
