<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { formatPrice, monthsLabel, providerLabel, pluralDays } from '@/lib/utils'
import { hapticImpact, hapticSuccess, hapticError } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import type { PaymentProvider, PromoResult } from '@/types'

const store = useSubscriptionStore()
const auth = useAuthStore()
const { t, te } = useI18n()
const { success, error } = useToast()

const selectedMonths = ref<number | null>(null)
const selectedGb = ref<number | null>(null)
const selectedProvider = ref<PaymentProvider | null>(null)
const step = ref<'plan' | 'payment'>('plan')

const promoCode = ref('')
const promoLoading = ref(false)
const promoApplied = ref(false)
const promoResult = ref<PromoResult | null>(null)

onMounted(() => store.fetchPlans())

const discount = computed(() => store.activeDiscount)

const providerIconMap: Record<string, string> = {
  yookassa: 'lucide:credit-card',
  stars: 'lucide:star',
  cryptopay: 'lucide:bitcoin',
  freekassa: 'lucide:banknote',
  platega: 'lucide:wallet',
  severpay: 'lucide:shield',
}

function discountedPrice(price: number) {
  if (!discount.value) return price
  return Math.ceil(price * (1 - discount.value.discount_percentage / 100))
}

function selectPlan(months: number) {
  hapticImpact()
  selectedMonths.value = months
  selectedGb.value = null
  step.value = 'payment'
}

function selectTraffic(gb: number) {
  hapticImpact()
  selectedGb.value = gb
  selectedMonths.value = null
  step.value = 'payment'
}

function backToPlan() {
  hapticImpact('light')
  step.value = 'plan'
  selectedProvider.value = null
}

async function pay() {
  if (!selectedProvider.value) return
  hapticImpact('medium')
  const params = selectedMonths.value ? { months: selectedMonths.value } : { gb: selectedGb.value! }
  const result = await store.createPayment(params, selectedProvider.value)
  if (result) {
    if (selectedProvider.value !== 'stars') success(t('plans.redirecting'))
  } else {
    error(t('plans.paymentError'))
  }
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
</script>

<template>
  <div class="flex w-full flex-col items-center gap-5 pt-2 pb-6">
    <h1 class="text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('plans.title') }}
    </h1>

    <!-- Loading -->
    <div v-if="store.loadingPlans" class="flex items-center justify-center py-12">
      <LoadingSpinner :text="t('plans.loading')" />
    </div>

    <template v-else>
      <!-- Active Discount Banner -->
      <div
        v-if="discount"
        class="flex items-center gap-3 border border-[#bdfe00]/30 bg-neutral-950 px-4 py-2"
      >
        <Icon icon="lucide:percent" class="size-4 shrink-0 text-[#bdfe00]" />
        <div>
          <p class="text-sm font-semibold text-[#bdfe00]">
            {{ t('plans.discountActive', { n: discount.discount_percentage }) }}
          </p>
          <p class="font-mono text-xs text-neutral-500">{{ discount.promo_code }}</p>
        </div>
      </div>

      <!-- STEP: Plan Selection -->
      <div v-if="step === 'plan'" class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3">
          <template v-if="!store.isTrafficMode">
            <button
              v-for="plan in store.activePlans"
              :key="plan.months"
              class="flex cursor-pointer flex-col gap-1 border p-4 text-left transition-colors"
              :class="
                selectedMonths === plan.months
                  ? 'border-[#bdfe00] bg-neutral-900'
                  : 'border-neutral-800 bg-neutral-950 hover:border-neutral-700'
              "
              @click="selectPlan(plan.months)"
            >
              <span class="text-2xl font-extrabold tracking-tighter text-white uppercase">{{
                monthsLabel(plan.months)
              }}</span>
              <span class="font-mono text-xl font-bold text-[#bdfe00]">{{
                formatPrice(discountedPrice(plan.price_rub!))
              }}</span>
              <span
                v-if="discount && plan.price_rub"
                class="font-mono text-xs text-neutral-500 line-through"
                >{{ formatPrice(plan.price_rub) }}</span
              >
            </button>
          </template>

          <template v-else>
            <button
              v-for="pkg in store.activeTrafficPackages"
              :key="pkg.gb"
              class="flex cursor-pointer flex-col gap-1 border p-4 text-left transition-colors"
              :class="
                selectedGb === pkg.gb
                  ? 'border-[#bdfe00] bg-neutral-900'
                  : 'border-neutral-800 bg-neutral-950 hover:border-neutral-700'
              "
              @click="selectTraffic(pkg.gb)"
            >
              <span class="text-2xl font-extrabold tracking-tighter text-white uppercase"
                >{{ pkg.gb }} GB</span
              >
              <span class="font-mono text-xl font-bold text-[#bdfe00]">{{
                formatPrice(discountedPrice(pkg.price_rub!))
              }}</span>
              <span
                v-if="discount && pkg.price_rub"
                class="font-mono text-xs text-neutral-500 line-through"
                >{{ formatPrice(pkg.price_rub) }}</span
              >
            </button>
          </template>
        </div>

        <!-- Promo Code -->
        <div class="flex flex-col gap-3 border border-neutral-800 bg-neutral-950 px-4 py-3">
          <p class="font-mono text-xs tracking-wide text-neutral-500 uppercase">
            {{ t('promo.inputLabel') }}
          </p>
          <div class="flex gap-2">
            <input
              v-model="promoCode"
              :placeholder="t('promo.placeholder')"
              class="min-w-0 flex-1 border border-neutral-800 bg-transparent px-3 py-2 font-mono text-sm tracking-widest text-white uppercase outline-none placeholder:text-neutral-600 focus:border-neutral-600 disabled:opacity-40"
              autocomplete="off"
              :disabled="promoLoading || promoApplied"
              @keydown.enter="applyPromo"
            />
            <button
              v-if="promoApplied || promoCode"
              class="cursor-pointer border border-neutral-800 bg-neutral-900 px-3 text-neutral-400"
              @click="resetPromo"
            >
              <Icon icon="lucide:x" class="size-4" />
            </button>
            <button
              class="cursor-pointer bg-white px-4 font-mono text-xs font-bold text-black uppercase transition-opacity disabled:opacity-40"
              :disabled="!promoCode.trim() || promoLoading || promoApplied"
              @click="applyPromo"
            >
              <Icon v-if="promoLoading" icon="lucide:loader-circle" class="size-4 animate-spin" />
              <span v-else>{{ t('common.apply') }}</span>
            </button>
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

      <!-- STEP: Payment Method -->
      <div v-else class="flex flex-col gap-4">
        <button
          class="flex cursor-pointer items-center gap-2 text-sm text-neutral-400"
          @click="backToPlan"
        >
          <Icon icon="lucide:chevron-left" class="size-4" />
          {{ t('plans.backToPlans') }}
        </button>

        <!-- Selected plan summary -->
        <div
          class="flex items-center justify-between border border-neutral-800 bg-neutral-950 px-4 py-2"
        >
          <div>
            <p class="text-xs text-neutral-500 uppercase">{{ t('plans.selectedPlan') }}</p>
            <p class="font-mono font-medium text-white">
              {{ selectedMonths ? monthsLabel(selectedMonths) : `${selectedGb} GB` }}
            </p>
          </div>
          <Icon icon="lucide:clock" class="size-5 text-neutral-500" />
        </div>

        <p class="text-sm font-semibold tracking-wide text-neutral-400 uppercase">
          {{ t('plans.paymentMethod') }}
        </p>

        <!-- Provider list -->
        <div class="flex flex-col gap-2">
          <button
            v-for="provider in store.availableProviders"
            :key="provider"
            class="flex w-full cursor-pointer items-center gap-3 border bg-neutral-950 px-4 py-2 transition-colors"
            :class="
              selectedProvider === provider
                ? 'border-[#bdfe00]'
                : 'border-neutral-800 hover:border-neutral-700'
            "
            @click="((selectedProvider = provider as PaymentProvider), hapticImpact('light'))"
          >
            <Icon
              :icon="providerIconMap[provider] ?? 'lucide:credit-card'"
              class="size-4 shrink-0"
              :class="selectedProvider === provider ? 'text-[#bdfe00]' : 'text-neutral-500'"
            />
            <span
              class="flex-1 text-left font-medium"
              :class="selectedProvider === provider ? 'text-white' : 'text-neutral-400'"
            >
              {{ providerLabel(provider) }}
            </span>
            <Icon
              v-if="selectedProvider === provider"
              icon="lucide:check"
              class="size-4 text-[#bdfe00]"
            />
          </button>
        </div>

        <!-- Pay button -->
        <button
          class="flex h-12 w-full cursor-pointer items-center justify-center bg-white text-sm font-extrabold tracking-tight text-black uppercase transition-opacity disabled:opacity-40"
          :disabled="!selectedProvider || store.processingPayment"
          @click="pay"
        >
          <span v-if="store.processingPayment">
            <Icon icon="lucide:loader-circle" class="size-4 animate-spin" />
          </span>
          <span v-else>{{ t('plans.pay') }}</span>
        </button>
      </div>
    </template>
  </div>
</template>
