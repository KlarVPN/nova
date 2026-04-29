<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { AVAILABLE_LOCALES, locale, setLocale } from '@/i18n/i18n.ts'
import { hapticError, hapticImpact, hapticSuccess, openLink } from '@/lib/telegram'
import { Button } from '@/components/ui/button'
import { useRouter } from 'vue-router'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { pluralDays } from '@/lib/utils'
import type { PromoResult } from '@/types'

const auth = useAuthStore()
const store = useSubscriptionStore()
const { t, te } = useI18n()
const { success, error } = useToast()

const botUsername = import.meta.env.VITE_BOT_USERNAME
const channelUsername = import.meta.env.VITE_CHANNEL_USERNAME
const docsUrl = import.meta.env.VITE_DOCS_URL
const privacyUrl = import.meta.env.VITE_PRIVACY_POLICY_URL
const termsUrl = import.meta.env.VITE_TERMS_OR_SERVICE_URL
const statusUrl = import.meta.env.VITE_STATUS_URL

const displayName = computed(() => {
  const p = auth.profile
  if (!p) return ''
  return [p.first_name, p.last_name].filter(Boolean).join(' ')
})

const userInitial = computed(() => displayName.value.charAt(0).toUpperCase() || '?')
const showLanguageModal = ref(false)
const showPromoModal = ref(false)
const promoCode = ref('')
const promoLoading = ref(false)
const promoApplied = ref(false)
const promoResult = ref<PromoResult | null>(null)
const currentLocaleLabel = computed(
  () =>
    AVAILABLE_LOCALES.find((item) => item.code === locale.value)?.name ??
    locale.value.toUpperCase(),
)

function switchTo(lang: 'ru' | 'en') {
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

function selectLanguage(lang: 'ru' | 'en') {
  switchTo(lang)
  closeLanguageModal()
}

function openPromoModal() {
  hapticImpact('light')
  showPromoModal.value = true
}

function closePromoModal() {
  showPromoModal.value = false
}

async function applyPromo() {
  const trimmed = promoCode.value.trim().toUpperCase()
  if (!trimmed) return
  promoLoading.value = true
  promoResult.value = null
  try {
    const res = await api.promo.apply(trimmed)
    promoResult.value = res
    if (res.success) {
      hapticSuccess()
      promoApplied.value = true
      if (res.type === 'bonus_days') {
        success(t('promo.addedDays', { days: pluralDays(res.bonus_days ?? 0) }))
        await auth.fetchProfile()
      } else if (res.type === 'discount') {
        success(t('promo.discountActivated'))
        await store.fetchPlans()
      }
    } else {
      hapticError()
      const errKey = `promo.errors.${res.error}`
      error(te(errKey) ? t(errKey as never) : t('promo.failed'))
    }
  } catch {
    hapticError()
    error(t('promo.failed'))
  } finally {
    promoLoading.value = false
  }
}

function resetPromo() {
  promoCode.value = ''
  promoResult.value = null
  promoApplied.value = false
}

function openExternal(url: string) {
  hapticImpact('light')
  openLink(url)
}
const router = useRouter()
</script>

<template>
  <div class="flex w-full flex-col gap-6 pt-4 pb-6">
    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('nav.profile') }}
    </h1>

    <!-- User info -->
    <div
      v-if="auth.profile"
      class="items-base flex gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 py-3"
    >
      <img
        :src="`https://api.dicebear.com/9.x/notionists/svg?seed=${auth.profile.user_id}`"
        class="size-10 shrink-0 rounded-[14px] bg-neutral-700"
        alt="avatar"
      />
      <div class="min-w-0">
        <p class="truncate font-semibold text-white">{{ displayName }}</p>
        <p v-if="auth.profile.username" class="text-sm text-neutral-400">
          @{{ auth.profile.username }} / ID: {{ auth.profile.user_id }}
        </p>
      </div>
    </div>

    <!-- Links -->
    <div class="flex flex-col gap-3">
      <div
        class="flex flex-col divide-y divide-neutral-800 overflow-hidden rounded-[14px] border border-neutral-800 bg-neutral-950"
      >
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'configs' })"
        >
          <Icon icon="lucide:qr-code" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.config') }}</span>
        </Button>

        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'referral' })"
        >
          <Icon icon="lucide:users-round" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.referral') }}</span>
        </Button>
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openPromoModal"
        >
          <Icon icon="lucide:ticket-percent" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.promo') }}</span>
        </Button>
      </div>

      <div
        class="flex flex-col divide-y divide-neutral-800 overflow-hidden rounded-[14px] border border-neutral-800 bg-neutral-950"
      >
        <Button
          v-if="channelUsername"
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(`https://t.me/${channelUsername}`)"
        >
          <Icon icon="lucide:newspaper" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.news') }}</span>
        </Button>

        <Button
          v-if="docsUrl"
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(docsUrl)"
        >
          <Icon icon="lucide:book-text" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.docs') }}</span>
        </Button>

        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'faq' })"
        >
          <Icon icon="lucide:circle-help" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.faq') }}</span>
        </Button>
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'locations' })"
        >
          <Icon icon="lucide:map-pin" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.status') }}</span>
        </Button>
      </div>
      <div
        class="flex flex-col divide-y divide-neutral-800 overflow-hidden rounded-[14px] border border-neutral-800 bg-neutral-950"
      >
        <Button
          v-if="termsUrl"
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(termsUrl)"
        >
          <Icon icon="lucide:file-text" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.terms') }}</span>
        </Button>

        <Button
          v-if="privacyUrl"
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(privacyUrl)"
        >
          <Icon icon="lucide:book-lock" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.privacy') }}</span>
        </Button>
      </div>
    </div>

    <!-- Language -->
    <div class="flex flex-col gap-3">
      <Button
        class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
        @click="openLanguageModal"
      >
        <Icon icon="lucide:languages" class="size-4 shrink-0 text-neutral-500" />
        <span class="font-medium text-white">{{ t('profile.language') }}</span>
        <span class="ml-auto text-sm text-neutral-400">{{ currentLocaleLabel }}</span>
      </Button>
    </div>

    <div class="flex flex-col items-center gap-2">
      <span>{{ t('profile.questions') }}</span>
      <Button
        v-if="botUsername"
        class="w-fit border border-neutral-700 bg-transparent p-2 px-4 text-sm text-white hover:bg-white/10"
        @click="openExternal(`https://t.me/${botUsername}`)"
      >
        {{ t('profile.support') }}
      </Button>
    </div>

    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showLanguageModal" class="fixed inset-0 z-50 flex flex-col justify-end">
          <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closeLanguageModal" />
          <div class="relative border-t border-white/10 bg-[#0a0a0a] p-4 pb-6">
            <div class="mb-4 flex justify-center">
              <div class="h-1 w-10 rounded-full bg-neutral-700" />
            </div>
            <h2 class="mb-3 text-base font-medium text-white">{{ t('profile.language') }}</h2>
            <div class="flex flex-col gap-2">
              <button
                v-for="item in AVAILABLE_LOCALES"
                :key="item.code"
                class="flex w-full cursor-pointer items-center rounded-[14px] border px-4 py-3 text-left transition-colors"
                :class="
                  locale === item.code
                    ? 'border-[#bdfe00] bg-neutral-900 text-[#bdfe00]'
                    : 'border-neutral-800 bg-neutral-950 text-white hover:bg-neutral-900'
                "
                @click="selectLanguage(item.code)"
              >
                <span class="font-medium">{{ item.name }}</span>
                <Icon
                  v-if="locale === item.code"
                  icon="lucide:check"
                  class="ml-auto size-4 text-[#bdfe00]"
                />
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showPromoModal" class="fixed inset-0 z-50 flex flex-col justify-end">
          <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="closePromoModal" />
          <div class="relative border-t border-white/10 bg-[#0a0a0a] p-4 pb-6">
            <div class="mb-4 flex justify-center">
              <div class="h-1 w-10 rounded-full bg-neutral-700" />
            </div>
            <h2 class="mb-3 text-base font-medium text-white">{{ t('promo.title') }}</h2>
            <div class="flex flex-col gap-3">
              <input
                v-model="promoCode"
                :placeholder="t('promo.placeholder')"
                class="min-w-0 rounded-[14px] border border-neutral-800 bg-neutral-950 px-3 py-2 font-mono text-sm tracking-widest text-white uppercase outline-none placeholder:text-neutral-600 focus:border-neutral-600 disabled:opacity-40"
                autocomplete="off"
                :disabled="promoLoading || promoApplied"
                @keydown.enter="applyPromo"
              />
              <div class="flex gap-2">
                <Button
                  class="flex h-10 flex-1 cursor-pointer items-center justify-center bg-white px-4 text-sm font-medium text-black transition-opacity disabled:opacity-40"
                  :disabled="!promoCode.trim() || promoLoading || promoApplied"
                  @click="applyPromo"
                >
                  <Icon
                    v-if="promoLoading"
                    icon="lucide:loader-circle"
                    class="size-4 animate-spin"
                  />
                  <span v-else>{{ t('common.apply') }}</span>
                </Button>
              </div>
              <p v-if="promoResult?.success" class="text-xs text-[#bdfe00]">
                <template v-if="promoResult.type === 'bonus_days'">
                  {{ t('promo.addedDays', { days: pluralDays(promoResult.bonus_days ?? 0) }) }}
                </template>
                <template v-else-if="promoResult.type === 'discount'">
                  {{ t('promo.discountApplied', { n: promoResult.discount_percentage }) }}
                </template>
              </p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;
}

.sheet-enter-active > div:last-child,
.sheet-leave-active > div:last-child {
  transition: transform 0.25s ease;
}

.sheet-enter-from > div:last-child,
.sheet-leave-to > div:last-child {
  transform: translateY(100%);
}
</style>
