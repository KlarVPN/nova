<script setup lang="ts">
import SheetModal from '@/components/common/SheetModal.vue'
import { Button } from '@/components/ui/button'
import type { Locale } from '@/i18n/i18n.ts'
import { AVAILABLE_LOCALES, locale, setLocale } from '@/i18n/i18n.ts'
import { hapticImpact } from '@/lib/telegram'
import { Icon } from '@iconify/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const showLanguageModal = ref(false)

const currentLocaleLabel = computed(
  () =>
    AVAILABLE_LOCALES.find((item) => item.code === locale.value)?.name ??
    locale.value.toUpperCase(),
)

const localeFlagByCode: Record<Locale, string> = {
  en: 'us',
  ru: 'ru',
  uk: 'ua',
  es: 'es',
  tr: 'tr',
  zh: 'cn',
  ko: 'kr',
}

const currentLocaleFlag = computed(() => localeFlagByCode[locale.value] ?? 'un')

function switchTo(lang: Locale) {
  if (locale.value === lang) return
  hapticImpact('light')
  setLocale(lang)
}

function openLanguageModal() {
  hapticImpact('light')
  showLanguageModal.value = true
}

function closeLanguageModal() {
  showLanguageModal.value = false
}

function selectLanguage(lang: Locale) {
  switchTo(lang)
  closeLanguageModal()
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <Button
      class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
      @click="openLanguageModal"
    >
      <span class="font-medium text-white">{{ t('profile.language') }}</span>
      <span class="ml-auto flex items-center gap-1 text-sm text-neutral-400">
        <Icon :icon="`circle-flags:${currentLocaleFlag}`" class="size-4 shrink-0" />
        <span>{{ currentLocaleLabel }}</span>
      </span>
    </Button>
  </div>

  <SheetModal
    :model-value="showLanguageModal"
    show-handle
    desktop-position="end"
    overlay-class="bg-black/70 backdrop-blur-sm"
    panel-class="border-t border-white/10 bg-[#0a0a0a] p-4 pb-6 md:w-full md:max-w-md md:rounded-2xl md:border md:pb-4"
    @close="closeLanguageModal"
  >
    <h2 class="mb-3 text-base font-medium text-white">{{ t('profile.language') }}</h2>
    <div class="flex flex-col gap-2">
      <button
        v-for="item in AVAILABLE_LOCALES"
        :key="item.code"
        class="flex w-full cursor-pointer items-center rounded-[14px] px-4 py-3 text-left transition-colors"
        :class="
          locale === item.code
            ? ' bg-neutral-900 text-white'
            : ' bg-neutral-950 text-white hover:bg-neutral-900'
        "
        @click="selectLanguage(item.code)"
      >
        <Icon :icon="`circle-flags:${localeFlagByCode[item.code]}`" class="mr-3 size-4 shrink-0" />
        <span class="font-medium">{{ item.name }}</span>
        <Icon v-if="locale === item.code" icon="lucide:check" class="ml-auto size-4 text-white" />
      </button>
    </div>
  </SheetModal>
</template>
