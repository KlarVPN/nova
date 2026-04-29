<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'

const { t } = useI18n()

const BOT_URL = import.meta.env.VITE_BOT_USERNAME
  ? `https://t.me/${import.meta.env.VITE_BOT_USERNAME}`
  : 'https://t.me'
</script>

<template>
  <div class="flex min-h-dvh flex-col items-center justify-center gap-8 px-6 text-center">
    <!-- Animated lock icon -->
    <div class="relative flex items-center justify-center">
      <div class="bg-accent/10 absolute h-32 w-32 animate-ping rounded-full" />
      <div class="bg-accent/10 absolute h-24 w-24 rounded-full" />
      <div
        class="border-border bg-card relative flex h-20 w-20 items-center justify-center rounded-full border"
      >
        <Icon icon="lucide:lock" class="text-accent h-9 w-9" />
      </div>
    </div>

    <!-- Text -->
    <div class="space-y-3">
      <h1 class="text-foreground font-sans text-2xl font-semibold tracking-tight">
        {{ t('auth.title') }}
      </h1>
      <p class="text-muted-foreground max-w-xs text-sm leading-relaxed">
        {{ t('auth.desc') }}
      </p>
    </div>

    <!-- Button -->
    <a
      :href="BOT_URL"
      class="press-scale bg-accent text-accent-foreground inline-flex h-12 cursor-pointer items-center gap-2.5 rounded-xl px-8 text-sm font-semibold transition-opacity hover:opacity-90"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Icon icon="lucide:send" class="h-4 w-4" />
      {{ t('auth.button') }}
    </a>
  </div>
</template>
