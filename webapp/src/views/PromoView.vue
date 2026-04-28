<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { useSubscriptionStore } from '@/stores/subscription'
import { useAuthStore } from '@/stores/auth'
import GlassCard from '@/components/common/GlassCard.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { formatDate, minutesUntil, pluralDays } from '@/lib/utils'
import { hapticSuccess, hapticError } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'
import type { PromoResult } from '@/types'

const auth = useAuthStore()
const store = useSubscriptionStore()
const { t, te } = useI18n()
const { success, error } = useToast()

const code = ref('')
const loading = ref(false)
const result = ref<PromoResult | null>(null)
const applied = ref(false)

const activeDiscount = computed(() => store.activeDiscount)

onMounted(() => store.fetchPlans())

async function applyCode() {
  const trimmed = code.value.trim().toUpperCase()
  if (!trimmed) return

  loading.value = true
  result.value = null

  try {
    const res = await api.promo.apply(trimmed)
    result.value = res

    if (res.success) {
      hapticSuccess()
      applied.value = true
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
    loading.value = false
  }
}

function reset() {
  code.value = ''
  result.value = null
  applied.value = false
}
</script>

<template>
  <div>
    <AppHeader :title="t('promo.title')" :subtitle="t('promo.subtitle')" />

    <div class="space-y-4 px-4 pt-2">
      <!-- Active Discount -->
      <GlassCard v-if="activeDiscount" :glow="true" class="border-accent/20 space-y-2 border">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Icon icon="lucide:percent" class="text-accent h-4 w-4" />
            <p class="text-foreground text-sm font-medium">{{ t('promo.activeDiscount') }}</p>
          </div>
          <Badge variant="popular" class="text-sm font-bold"
            >{{ activeDiscount.discount_percentage }}% OFF</Badge
          >
        </div>
        <p class="text-muted-foreground font-mono text-xs">{{ activeDiscount.promo_code }}</p>
        <div class="text-warning flex items-center gap-1.5 text-xs">
          <Icon icon="lucide:clock" class="h-3 w-3" />
          <span>{{ t('promo.expiresIn', { n: minutesUntil(activeDiscount.expires_at) }) }}</span>
        </div>
        <p class="text-muted-foreground text-xs">{{ t('promo.useHint') }}</p>
      </GlassCard>

      <!-- Input -->
      <GlassCard subtle class="space-y-3">
        <div class="flex items-center gap-2">
          <Icon icon="lucide:tag" class="text-muted-foreground h-4 w-4" />
          <p class="text-foreground text-sm font-medium">{{ t('promo.inputLabel') }}</p>
        </div>
        <Input
          v-model="code"
          :placeholder="t('promo.placeholder')"
          class="font-mono tracking-widest uppercase"
          autocomplete="off"
          :disabled="loading || applied"
          @keydown.enter="applyCode"
        />
        <div class="flex gap-2">
          <Button
            class="flex-1"
            :loading="loading"
            :disabled="!code.trim() || applied"
            @click="applyCode"
          >
            <Icon icon="lucide:check" class="h-4 w-4" />
            {{ t('common.apply') }}
          </Button>
          <Button
            v-if="applied || code"
            variant="ghost"
            size="icon"
            class="shrink-0"
            @click="reset"
          >
            <Icon icon="lucide:x" class="h-4 w-4" />
          </Button>
        </div>
      </GlassCard>

      <!-- Result -->
      <Transition name="page">
        <GlassCard
          v-if="result"
          subtle
          class="space-y-2"
          :class="result.success ? 'border-accent/30 border' : 'border-destructive/30 border'"
        >
          <template v-if="result.success && result.type === 'bonus_days'">
            <div class="flex items-center gap-2">
              <div class="bg-accent/20 flex h-8 w-8 items-center justify-center rounded-full">
                <Icon icon="lucide:check" class="text-accent h-4 w-4" />
              </div>
              <p class="text-accent font-medium">{{ t('promo.applied') }}</p>
            </div>
            <p class="text-muted-foreground text-sm">
              {{ t('promo.addedDays', { days: pluralDays(result.bonus_days ?? 0) }) }}
            </p>
            <p v-if="result.new_end_date" class="text-muted-foreground text-xs">
              {{ t('promo.newExpiry', { date: formatDate(result.new_end_date) }) }}
            </p>
          </template>

          <template v-else-if="result.success && result.type === 'discount'">
            <div class="flex items-center gap-2">
              <div class="bg-accent/20 flex h-8 w-8 items-center justify-center rounded-full">
                <Icon icon="lucide:percent" class="text-accent h-4 w-4" />
              </div>
              <p class="text-accent font-medium">{{ t('promo.discountActivated') }}</p>
            </div>
            <p class="text-muted-foreground text-sm">
              {{ t('promo.discountApplied', { n: result.discount_percentage }) }}
            </p>
            <p v-if="result.expires_at" class="text-warning text-xs">
              {{ t('promo.expiresIn', { n: minutesUntil(result.expires_at) }) }}
            </p>
          </template>

          <template v-else-if="!result.success">
            <div class="flex items-center gap-2">
              <div class="bg-destructive/20 flex h-8 w-8 items-center justify-center rounded-full">
                <Icon icon="lucide:x" class="text-destructive h-4 w-4" />
              </div>
              <p class="text-destructive font-medium">{{ t('promo.failed') }}</p>
            </div>
          </template>
        </GlassCard>
      </Transition>

      <!-- Info -->
      <GlassCard subtle class="space-y-2">
        <p class="text-foreground text-sm font-medium">{{ t('promo.types') }}</p>
        <div class="space-y-2">
          <div class="flex items-start gap-2">
            <Badge variant="default" class="shrink-0 text-xs">{{ t('promo.bonus') }}</Badge>
            <p class="text-muted-foreground text-xs">{{ t('promo.bonusDesc') }}</p>
          </div>
          <div class="flex items-start gap-2">
            <Badge variant="warning" class="shrink-0 text-xs">{{ t('promo.discount') }}</Badge>
            <p class="text-muted-foreground text-xs">{{ t('promo.discountDesc') }}</p>
          </div>
        </div>
      </GlassCard>
    </div>
  </div>
</template>
