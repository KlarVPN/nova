<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, monthsLabel, providerLabel } from '@/lib/utils'
import { hapticImpact } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'
import type { PaymentProvider } from '@/types'

const store = useSubscriptionStore()
const auth = useAuthStore()
const { t } = useI18n()
const { success, error } = useToast()

const selectedMonths = ref<number | null>(null)
const selectedGb = ref<number | null>(null)
const selectedProvider = ref<PaymentProvider | null>(null)
const step = ref<'plan' | 'payment'>('plan')
const hasRequestedPlans = ref(false)

const supportedProviders: PaymentProvider[] = [
  'yookassa',
  'stars',
  'cryptopay',
  'freekassa',
  'platega',
  'severpay',
]

const paymentProviders = computed(() =>
  store.availableProviders.filter((provider): provider is PaymentProvider =>
    supportedProviders.includes(provider as PaymentProvider),
  ),
)
const displayPlans = computed(() => {
  if (store.activePlans.length) return store.activePlans
  return (store.plansData?.plans ?? []).filter(
    (p) => p.price_rub !== null || p.price_stars !== null,
  )
})
const displayTrafficPackages = computed(() => {
  if (store.activeTrafficPackages.length) return store.activeTrafficPackages
  return (store.plansData?.traffic_packages ?? []).filter(
    (p) => p.price_rub !== null || p.price_stars !== null,
  )
})
const selectedPlan = computed(() =>
  selectedMonths.value ? displayPlans.value.find((p) => p.months === selectedMonths.value) : null,
)
const selectedTraffic = computed(() =>
  selectedGb.value ? displayTrafficPackages.value.find((p) => p.gb === selectedGb.value) : null,
)

const availableProvidersForSelection = computed(() =>
  paymentProviders.value.filter((provider) => {
    if (provider === 'stars') {
      if (store.isTrafficMode) return selectedTraffic.value?.price_stars != null
      return selectedPlan.value?.price_stars != null
    }
    if (store.isTrafficMode) return selectedTraffic.value?.price_rub != null
    return selectedPlan.value?.price_rub != null
  }),
)

const selectedAmountLabel = computed(() => {
  const selected = store.isTrafficMode ? selectedTraffic.value : selectedPlan.value
  if (!selected || !selectedProvider.value) return null

  if (selectedProvider.value === 'stars') {
    if (selected.price_stars == null) return null
    return String(selected.price_stars)
  }

  if (selected.price_rub == null) return null
  return formatPrice(discountedPrice(selected.price_rub))
})

const oneMonthPlan = computed(() => sortedPlans.value.find((p) => p.months === 1) ?? null)

const paySubscriptionPrice = computed(() => {
  if (selectedMonths.value) {
    const plan = sortedPlans.value.find((p) => p.months === selectedMonths.value)
    if (!plan) return { oldPrice: null as string | null, finalPrice: null as string | null }

    if (plan.price_rub != null) {
      const finalPrice = formatPrice(discountedPrice(plan.price_rub))
      if (selectedMonths.value >= 3 && oneMonthPlan.value?.price_rub != null) {
        const oldTotal = formatPrice(oneMonthPlan.value.price_rub * selectedMonths.value)
        return { oldPrice: oldTotal, finalPrice }
      }
      return { oldPrice: null, finalPrice }
    }

    if (plan.price_stars != null) {
      return { oldPrice: null, finalPrice: `${plan.price_stars} ⭐` }
    }
  }

  if (selectedGb.value) {
    const pkg = displayTrafficPackages.value.find((p) => p.gb === selectedGb.value)
    if (pkg?.price_rub != null)
      return { oldPrice: null, finalPrice: formatPrice(discountedPrice(pkg.price_rub)) }
    if (pkg?.price_stars != null) return { oldPrice: null, finalPrice: `${pkg.price_stars} ⭐` }
  }

  return { oldPrice: null, finalPrice: null }
})

onMounted(() => {
  if (store.plansData) {
    hasRequestedPlans.value = true
    return
  }

  hasRequestedPlans.value = true
  store.fetchPlans()
})

const showPlansSkeleton = computed(
  () => store.loadingPlans || (!store.plansData && !hasRequestedPlans.value),
)

const discount = computed(() => store.activeDiscount)
const includedTrafficGb = computed(() => store.plansData?.included_traffic_gb ?? null)
const maxDevices = computed(() => store.plansData?.max_devices ?? null)
const sortedPlans = computed(() => [...displayPlans.value].sort((a, b) => a.months - b.months))

const cheapestMonthlyPlan = computed(() => {
  const base = sortedPlans.value.find((p) => p.months === 1)
  if (!base) return null
  const cost = planCostValue(base)
  return cost == null ? null : Math.round(cost)
})

const providerIconMap: Record<string, string> = {
  yookassa: 'lucide:credit-card',
  stars: 'mingcute:star-fill',
  cryptopay: 'lucide:bitcoin',
  freekassa: 'lucide:banknote',
  severpay: 'lucide:shield',
}

const selectedUntilText = computed(() => {
  const now = new Date()
  const currentEnd = auth.subscription?.end_date ? new Date(auth.subscription.end_date) : null
  const base = currentEnd && currentEnd > now ? currentEnd : now

  if (selectedMonths.value) {
    const end = new Date(base)
    end.setMonth(end.getMonth() + selectedMonths.value)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(end)
  }

  if (currentEnd) {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(currentEnd)
  }

  return '—'
})

function discountedPrice(price: number) {
  if (!discount.value) return price
  return Math.ceil(price * (1 - discount.value.discount_percentage / 100))
}

function planDisplayPrice(priceRub: number | null, priceStars: number | null) {
  if (priceRub != null) return formatPrice(discountedPrice(priceRub))
  if (priceStars != null) return `${priceStars} ⭐`
  return '—'
}

function planCostValue(plan: {
  price_rub: number | null
  price_stars: number | null
}): number | null {
  if (plan.price_rub != null) return discountedPrice(plan.price_rub)
  if (plan.price_stars != null) return plan.price_stars
  return null
}

function planSavings(months: number): number | null {
  const base = sortedPlans.value.find((p) => p.months === 1)
  const target = sortedPlans.value.find((p) => p.months === months)
  if (!base || !target || months <= 1) return null
  const baseCost = planCostValue(base)
  const targetCost = planCostValue(target)
  if (baseCost == null || targetCost == null) return null
  const save = baseCost * months - targetCost
  return save > 0 ? Math.round(save) : null
}

function pricePerMonth(
  months: number,
  priceRub: number | null,
  priceStars: number | null,
): string | null {
  if (months <= 0) return null
  if (priceRub != null) {
    const monthly = Math.round(discountedPrice(priceRub) / months)
    return `${formatPrice(monthly)}/${t('common.month', 1)}`
  }
  if (priceStars != null) {
    const monthly = Math.round(priceStars / months)
    return `${monthly} ⭐/${t('common.month', 1)}`
  }
  return null
}

function trafficLabel(): string {
  if (includedTrafficGb.value == null || includedTrafficGb.value <= 0)
    return t('plans.unlimitedTraffic')
  return `${includedTrafficGb.value} GB`
}

function devicesLabel(): string {
  if (maxDevices.value == null || maxDevices.value <= 0) return t('plans.unlimitedDevices')
  return String(maxDevices.value)
}

function selectPlan(months: number) {
  hapticImpact()
  selectedMonths.value = months
  selectedGb.value = null
}

function selectTraffic(gb: number) {
  hapticImpact()
  selectedGb.value = gb
  selectedMonths.value = null
}

function goToPaymentStep() {
  if (!selectedMonths.value && !selectedGb.value) {
    error(t('plans.selectPlanFirst'))
    return
  }
  hapticImpact('light')
  step.value = 'payment'
}

function backToPlan() {
  hapticImpact('light')
  step.value = 'plan'
  selectedProvider.value = null
}

async function pay() {
  if (!selectedProvider.value) {
    error(t('plans.paymentError'))
    return
  }
  if (!selectedMonths.value && !selectedGb.value) {
    error(t('plans.paymentError'))
    return
  }

  hapticImpact('medium')
  const params = selectedMonths.value ? { months: selectedMonths.value } : { gb: selectedGb.value! }
  const result = await store.createPayment(params, selectedProvider.value)
  if (result) {
    if (selectedProvider.value !== 'stars') success(t('plans.redirecting'))
  } else {
    error(t('plans.paymentError'))
  }
}

watch(
  () => [step.value, availableProvidersForSelection.value] as const,
  ([currentStep, providers]) => {
    if (currentStep !== 'payment') return
    if (!providers.length) {
      selectedProvider.value = null
      return
    }
    if (!selectedProvider.value || !providers.includes(selectedProvider.value)) {
      selectedProvider.value = providers[0]
    }
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="plans-page relative mx-auto flex w-full max-w-5xl flex-col items-center gap-5 pt-2 pb-6"
  >
    <div class="bg-wh flex flex-col gap-3 rounded-[14px] bg-neutral-950 p-5 pr-25">
      <h1 class="mt-1 text-2xl leading-[0.9] font-medium tracking-tight text-balance text-white">
        {{ t('plans.title') }}
      </h1>
      <p class="text-sm text-balance opacity-60">
        {{ t('plans.description') }}
      </p>
    </div>

    <Transition name="content-fade">
      <!-- Loading -->
      <div v-if="showPlansSkeleton" key="loading" class="flex w-full flex-col gap-3 py-4">
        <div
          class="h-[136px] w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
        <div
          class="h-[136px] w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
        <div
          class="h-[136px] w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
        <div
          class="h-[136px] w-full animate-pulse rounded-[14px] border border-neutral-800 bg-neutral-900"
        />
      </div>

      <div v-else key="content" class="w-full">
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
        <div v-if="step === 'plan'" class="flex w-full flex-col gap-4">
          <div
            v-if="!displayPlans.length && !displayTrafficPackages.length"
            class="flex flex-col items-center gap-3 border border-neutral-800 bg-neutral-950 px-4 py-6 text-center"
          >
            <p class="text-sm text-neutral-400">{{ t('plans.loading') }}</p>
            <button
              class="cursor-pointer border border-neutral-700 bg-neutral-900 px-4 py-2 text-xs font-semibold text-white uppercase"
              @click="store.fetchPlans()"
            >
              {{ t('common.retry') }}
            </button>
          </div>
          <div class="flex w-full flex-col gap-3">
            <template v-if="!store.isTrafficMode">
              <div class="grid grid-cols-2 gap-3">
                <button
                  v-for="plan in sortedPlans"
                  :key="plan.months"
                  class="relative flex aspect-square cursor-pointer flex-col justify-between gap-2 overflow-hidden rounded-[18px] border p-4 text-left transition-all"
                  :class="
                    selectedMonths === plan.months
                      ? 'border-emerald-300/80 bg-neutral-900/90 shadow-[0_20px_45px_rgba(16,185,129,0.12)]'
                      : 'border-white/10 bg-neutral-950/70 hover:border-white/20 hover:bg-neutral-900/70'
                  "
                  @click="selectPlan(plan.months)"
                >
                  <div class="flex items-start justify-between gap-2">
                    <span class="text-base text-white">
                      {{ monthsLabel(plan.months) }}
                    </span>
                    <Icon
                      v-if="plan.months === 6"
                      icon="mingcute:star-fill"
                      class="size-4 shrink-0 text-amber-300"
                    />
                  </div>
                  <div class="flex flex-col gap-2">
                    <span class="text-2xl leading-none font-semibold tracking-tight">{{
                      planDisplayPrice(plan.price_rub, plan.price_stars)
                    }}</span>
                    <span class="text-sm text-white/65">{{
                      pricePerMonth(plan.months, plan.price_rub, plan.price_stars)
                    }}</span>
                  </div>
                </button>
              </div>
            </template>

            <template v-else>
              <button
                v-for="pkg in displayTrafficPackages"
                :key="pkg.gb"
                class="plan-card-modern relative flex cursor-pointer flex-col gap-1 overflow-hidden rounded-[18px] border p-4 text-left transition-all"
                :class="
                  selectedGb === pkg.gb
                    ? 'plan-card-active border-emerald-300/70 bg-neutral-900/90 shadow-[0_20px_45px_rgba(16,185,129,0.12)]'
                    : 'border-white/10 bg-neutral-950/70 hover:border-white/20 hover:bg-neutral-900/70'
                "
                @click="selectTraffic(pkg.gb)"
              >
                <div
                  class="plan-card-glow"
                  :class="selectedGb === pkg.gb ? 'opacity-100' : 'opacity-0'"
                />
                <span class="text-2xl font-extrabold tracking-tighter text-white uppercase"
                  >{{ pkg.gb }} GB</span
                >
                <span class="text-3xl font-semibold tracking-tight text-emerald-200">{{
                  planDisplayPrice(pkg.price_rub, pkg.price_stars)
                }}</span>
                <span
                  v-if="discount && pkg.price_rub !== null"
                  class="font-mono text-xs text-neutral-500 line-through"
                  >{{ formatPrice(pkg.price_rub) }}</span
                >
              </button>
            </template>
          </div>

          <button
            class="mt-2 flex h-12 w-full cursor-pointer items-center justify-between rounded-[14px] bg-emerald-200 px-4 text-sm font-bold tracking-[0.08em] text-emerald-950 uppercase transition-all hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!selectedMonths && !selectedGb"
            @click="goToPaymentStep"
          >
            <span>{{ t('plans.paySubscription') }}</span>
            <span
              v-if="paySubscriptionPrice.finalPrice"
              class="flex items-center gap-1 text-right text-xs tracking-normal normal-case"
            >
              <span v-if="paySubscriptionPrice.oldPrice" class="text-emerald-900/60 line-through">{{
                paySubscriptionPrice.oldPrice
              }}</span>
              <span class="text-sm font-semibold text-emerald-950">{{
                paySubscriptionPrice.finalPrice
              }}</span>
            </span>
          </button>
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
          <div class="rounded-[16px] border border-white/10 bg-neutral-950/80 px-4 py-3">
            <div>
              <p class="text-xs text-neutral-500 uppercase">{{ t('plans.selectedPlan') }}</p>
              <p class="text-base font-semibold tracking-tight text-white">
                {{ selectedMonths ? monthsLabel(selectedMonths) : `${selectedGb} GB` }}
              </p>
              <p class="mt-1 text-xs text-neutral-400">
                {{ t('plans.activeUntil') }}:
                <span class="text-neutral-200">{{ selectedUntilText }}</span>
              </p>
              <p class="mt-1 text-xs text-neutral-400">
                {{ t('plans.devices') }}: <span class="text-neutral-200">{{ devicesLabel() }}</span>
              </p>
              <p class="mt-1 text-xs text-neutral-400">
                {{ t('plans.traffic') }}: <span class="text-neutral-200">{{ trafficLabel() }}</span>
              </p>
            </div>
          </div>

          <p class="text-sm font-semibold tracking-wide text-neutral-400 uppercase">
            {{ t('plans.paymentMethod') }}
          </p>

          <!-- Provider list -->
          <div class="flex flex-col gap-2">
            <div
              v-if="!availableProvidersForSelection.length"
              class="border border-amber-700/40 bg-amber-950/40 px-4 py-3 text-sm text-amber-300"
            >
              {{ t('plans.paymentError') }}
            </div>

            <button
              v-for="provider in availableProvidersForSelection"
              :key="provider"
              class="flex w-full cursor-pointer items-center gap-3 rounded-[14px] border bg-neutral-950/80 px-4 py-3 transition-all"
              :class="
                selectedProvider === provider
                  ? 'border-emerald-300/70 bg-emerald-300/10'
                  : 'border-white/10 hover:border-white/20'
              "
              @click="((selectedProvider = provider as PaymentProvider), hapticImpact('light'))"
            >
              <img v-if="provider === 'platega'" src="/SBP.svg" alt="SBP" class="size-4 shrink-0" />
              <Icon
                v-else
                :icon="providerIconMap[provider] ?? 'lucide:credit-card'"
                class="size-4 shrink-0"
                :class="selectedProvider === provider ? 'text-emerald-200' : 'text-neutral-500'"
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
                class="size-4 text-emerald-200"
              />
            </button>
          </div>

          <!-- Pay button -->
          <button
            class="flex h-12 w-full cursor-pointer items-center justify-center rounded-[14px] bg-emerald-200 text-sm font-bold tracking-[0.1em] text-emerald-950 uppercase transition-all hover:bg-emerald-100 disabled:opacity-40"
            :disabled="!selectedProvider || store.processingPayment"
            @click="pay"
          >
            <span v-if="store.processingPayment">
              <Icon icon="lucide:loader-circle" class="size-4 animate-spin" />
            </span>
            <span v-else>
              {{ t('plans.pay') }}
              <template v-if="selectedAmountLabel">
                <template v-if="selectedProvider === 'stars'">
                  · {{ selectedAmountLabel }}
                  <Icon icon="mingcute:star-fill" class="-mt-0.5 ml-1 inline size-4 align-middle" />
                </template>
                <template v-else> · {{ selectedAmountLabel }}</template>
              </template>
            </span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.content-fade-enter-active,
.content-fade-leave-active {
  transition: opacity 280ms ease;
}

.content-fade-leave-active {
  position: absolute;
  inset: 0;
  width: 100%;
  pointer-events: none;
}

.content-fade-enter-from,
.content-fade-leave-to {
  opacity: 0;
}
</style>
