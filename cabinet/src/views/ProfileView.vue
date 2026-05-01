<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'
import { AVAILABLE_LOCALES, locale, setLocale } from '@/i18n/i18n.ts'
import { hapticError, hapticImpact, hapticSuccess, openLink } from '@/lib/telegram'
import { Button } from '@/components/ui/button'
import FloatingSubscriptionLink from '@/components/common/FloatingSubscriptionLink.vue'
import SheetModal from '@/components/common/SheetModal.vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { pluralDays } from '@/lib/utils'
import type { PromoResult } from '@/types'
import type { Locale } from '@/i18n/i18n.ts'

const auth = useAuthStore()
const store = useSubscriptionStore()
const { t, te } = useI18n()
const { success, error } = useToast()

const reviewsUrl = computed(() => auth.profile?.links.reviews || '')
const docsUrl = computed(() => auth.profile?.links.docs || '')
const termsUrl = computed(() => auth.profile?.links.terms || '')
const privacyUrl = computed(() => auth.profile?.links.privacy || '')

const displayName = computed(() => {
  const p = auth.profile
  const firstName = p?.first_name || auth.telegramUserCache.first_name || ''
  const lastName = p?.last_name || auth.telegramUserCache.last_name || ''
  return [firstName, lastName].filter(Boolean).join(' ')
})

const displayUsername = computed(
  () => auth.profile?.username || auth.telegramUserCache.username || '',
)

const userInitial = computed(() => displayName.value.charAt(0).toUpperCase() || '?')
const randomAvatarSeed = ref(`rnd-${Math.random().toString(36).slice(2, 10)}`)
const telegramAvatarUrl = computed(
  () => auth.profile?.photo_url || auth.user?.photo_url || auth.telegramPhotoUrl || '',
)
const fallbackAvatarUrl = computed(() => {
  const seed = `${auth.profile?.user_id ?? randomAvatarSeed.value}-${randomAvatarSeed.value}`
  return `https://api.dicebear.com/9.x/notionists/svg?seed=${encodeURIComponent(seed)}`
})
const resolvedAvatarUrl = computed(() => telegramAvatarUrl.value || fallbackAvatarUrl.value)
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
const connectUrl = computed(
  () => store.connectInfo?.config_link || store.connectInfo?.connect_url || '',
)

onMounted(async () => {
  if (auth.hasSubscription && !store.connectInfo) {
    await store.fetchConnect()
  }
})

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
  if (!url) return
  hapticImpact('light')
  openLink(url)
}

async function handleLogout() {
  hapticImpact('light')
  auth.logout()
  await router.replace({ name: 'login' })
}

async function copyTelegramId() {
  if (!auth.profile) return
  try {
    await navigator.clipboard.writeText(String(auth.profile.user_id))
    hapticSuccess()
    success(t('common.copied'))
  } catch {
    hapticError()
    error(t('common.error'))
  }
}

const router = useRouter()
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-4 pb-24 md:pb-6">
    <!-- User info -->
    <div
      v-if="auth.profile"
      class="flex cursor-pointer items-center gap-3 rounded-[14px] bg-neutral-950 p-1 transition-colors hover:bg-neutral-900"
      @click="copyTelegramId"
    >
      <img
        :src="resolvedAvatarUrl"
        class="size-12 shrink-0 rounded-[14px] bg-neutral-700"
        alt="avatar"
      />
      <div class="min-w-0 flex-1">
        <p class="truncate font-semibold text-white">{{ displayName }}</p>
        <p class="text-sm text-neutral-400">ID: {{ auth.profile.user_id }}</p>
      </div>
      <button
        type="button"
        class="flex size-12 shrink-0 cursor-pointer items-center justify-center rounded-lg bg-neutral-950 text-neutral-400"
        @click.stop="copyTelegramId"
      >
        <Icon icon="lucide:copy" class="size-5" />
      </button>
    </div>

    <!-- Links -->
    <div class="flex flex-col gap-3">
      <div class="profile-links-group flex flex-col overflow-hidden rounded-[14px] bg-neutral-950">
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
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'operations' })"
        >
          <Icon icon="lucide:history" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.operations') }}</span>
        </Button>
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'proxies' })"
        >
          <Icon icon="lucide:shield" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.freeTelegramProxies') }}</span>
        </Button>
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="router.push({ name: 'access-save' })"
        >
          <Icon icon="lucide:link-2" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.accessSave') }}</span>
        </Button>
      </div>

      <div class="profile-links-group flex flex-col overflow-hidden rounded-[14px] bg-neutral-950">
        <Button
          v-if="reviewsUrl"
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(reviewsUrl)"
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
      </div>
      <div class="profile-links-group flex flex-col overflow-hidden rounded-[14px] bg-neutral-950">
        <Button
          class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-none bg-transparent p-4 text-left transition-colors hover:border-neutral-700 hover:bg-neutral-900"
          @click="openExternal(termsUrl)"
        >
          <Icon icon="lucide:file-text" class="size-4 shrink-0 text-neutral-500" />
          <span class="font-medium text-white">{{ t('profile.terms') }}</span>
        </Button>

        <Button
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
        class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
        @click="openLanguageModal"
      >
        <Icon icon="lucide:languages" class="size-4 shrink-0 text-neutral-500" />
        <span class="font-medium text-white">{{ t('profile.language') }}</span>
        <span class="ml-auto text-sm text-neutral-400">{{ currentLocaleLabel }}</span>
      </Button>
    </div>

    <Button
      v-if="!auth.isTelegram"
      class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] bg-red-950/50 px-4 text-left transition-colors hover:bg-red-950/70"
      @click="handleLogout"
    >
      <Icon icon="lucide:log-out" class="size-4 shrink-0 text-red-400" />
      <span class="font-medium text-red-300">{{ t('profile.logout') }}</span>
    </Button>

    <div class="flex flex-col items-center gap-2">
      <span>{{ t('profile.questions') }}</span>
      <Button
        class="w-fit bg-neutral-800 p-2 px-4 text-sm font-semibold text-white hover:bg-neutral-700"
        @click="router.push({ name: 'support' })"
      >
        {{ t('profile.support') }}
      </Button>
    </div>

    <SheetModal
      :model-value="showLanguageModal"
      show-handle
      overlay-class="bg-black/70 backdrop-blur-sm"
      panel-class="border-t border-white/10 bg-[#0a0a0a] p-4 pb-6 md:w-full md:max-w-md md:rounded-2xl md:border md:pb-4"
      @close="closeLanguageModal"
    >
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
    </SheetModal>

    <SheetModal
      :model-value="showPromoModal"
      desktop-position="end"
      show-handle
      panel-class="bg-[#0a0a0a] p-4 pb-6 md:w-full md:max-w-md md:rounded-2xl md:pb-4"
      @close="closePromoModal"
    >
      <h2 class="mb-3 text-base font-medium text-white">{{ t('promo.title') }}</h2>
      <p class="mb-3 text-sm text-neutral-400">
        {{ t('promo.modalDesc') }}
      </p>
      <div class="flex flex-col gap-3">
        <input
          v-model="promoCode"
          :placeholder="t('promo.placeholder')"
          class="promo-input min-w-0 rounded-[14px] bg-neutral-900 px-3 py-2 font-mono text-sm tracking-widest text-white uppercase outline-none placeholder:text-neutral-500 disabled:opacity-40"
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
            <Icon v-if="promoLoading" icon="lucide:loader-circle" class="size-4 animate-spin" />
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
    </SheetModal>

    <FloatingSubscriptionLink :url="connectUrl" />
  </div>
</template>

<style scoped>
.promo-input {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

:global(:root[data-theme='light']) .promo-input {
  background-color: #f2f2f7;
  border-color: #c7c7cc;
  color: #1d1d1f;
  box-shadow: none;
}

:global(:root[data-theme='light']) .promo-input::placeholder {
  color: #8e8e93;
}

.profile-links-group > :deep(button + button) {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

:global(:root[data-theme='light']) .profile-links-group > :deep(button + button) {
  box-shadow: inset 0 1px 0 #d2d2d7;
}
</style>
