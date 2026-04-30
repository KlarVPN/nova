<script setup lang="ts">
import { hapticImpact } from '@/lib/telegram'
import { setLocale } from '@/i18n/i18n.ts'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const flags: Record<string, string> = {
  ru: '🇷🇺',
  en: '🇬🇧',
}

const nextLocale: Record<string, 'ru' | 'en'> = {
  ru: 'en',
  en: 'ru',
}

const switchLocale = () => {
  const newLocale = nextLocale[locale.value] || 'ru'

  locale.value = newLocale
  setLocale(newLocale)

  hapticImpact('light')
}
</script>

<template>
  <button
    class="flex cursor-pointer items-center gap-1.5 border border-neutral-800 bg-neutral-950/80 px-2.5 py-1.5 backdrop-blur-sm transition-colors hover:border-neutral-600 active:scale-95"
    @click="switchLocale"
  >
    <span class="text-sm leading-none">{{ locale == 'ru' ? flags.en : flags.ru }}</span>
    <span class="font-mono text-[11px] font-semibold tracking-wide text-neutral-400 uppercase">
      {{ locale == 'ru' ? 'EN' : 'RU' }}
    </span>
  </button>
</template>
