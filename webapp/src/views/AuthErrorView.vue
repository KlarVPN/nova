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
      <div class="absolute h-32 w-32 animate-ping rounded-full bg-accent/10" />
      <div class="absolute h-24 w-24 rounded-full bg-accent/10" />
      <div class="relative flex h-20 w-20 items-center justify-center rounded-full border border-border bg-card">
        <Icon icon="lucide:lock" class="h-9 w-9 text-accent" />
      </div>
    </div>

    <!-- Text -->
    <div class="space-y-3">
      <h1 class="font-sans text-2xl font-semibold tracking-tight text-foreground">
        {{ t('auth.title') }}
      </h1>
      <p class="max-w-xs text-sm leading-relaxed text-muted-foreground">
        {{ t('auth.desc') }}
      </p>
    </div>

    <!-- Button -->
    <a
      :href="BOT_URL"
      class="press-scale inline-flex h-12 cursor-pointer items-center gap-2.5 rounded-xl bg-accent px-8 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Icon icon="lucide:send" class="h-4 w-4" />
      {{ t('auth.button') }}
    </a>
  </div>
</template>
