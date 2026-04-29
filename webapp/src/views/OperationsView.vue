<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/lib/api'
import type { OperationHistoryItem } from '@/types'

const { t } = useI18n()

const loading = ref(false)
const operations = ref<OperationHistoryItem[]>([])

const hasOperations = computed(() => operations.value.length > 0)

function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

async function fetchOperations() {
  if (loading.value) return
  loading.value = true
  try {
    const response = await api.operations.list()
    operations.value = response.operations
  } finally {
    loading.value = false
  }
}

onMounted(fetchOperations)
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-2 pb-6">
    <h1 class="text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('operations.title') }}
    </h1>
    <p class="-mt-1 text-sm text-neutral-400">{{ t('operations.subtitle') }}</p>

    <div v-if="loading" class="py-10 text-center text-sm text-neutral-400">
      {{ t('common.loading') }}
    </div>

    <div v-else-if="!hasOperations" class="rounded-[14px] bg-neutral-950 px-4 py-6 text-center">
      <p class="text-sm text-neutral-400">{{ t('operations.empty') }}</p>
    </div>

    <div v-else class="flex flex-col gap-2">
      <div
        v-for="(item, idx) in operations"
        :key="`${item.type}-${item.created_at}-${idx}`"
        class="rounded-[14px] bg-neutral-950 px-4 py-3"
      >
        <div class="flex items-center gap-2">
          <Icon
            :icon="item.type === 'trial_activated' ? 'lucide:rocket' : 'lucide:receipt-text'"
            class="size-4 text-[#bdfe00]"
          />
          <p class="font-medium text-white">
            {{
              item.type === 'trial_activated'
                ? t('operations.trialActivated')
                : t('operations.planPaid')
            }}
          </p>
          <span class="ml-auto text-xs text-neutral-500">{{ formatDate(item.created_at) }}</span>
        </div>

        <p v-if="item.type === 'trial_activated'" class="mt-2 text-sm text-neutral-400">
          {{ t('operations.trialDuration', { n: item.duration_days ?? 0 }) }}
        </p>
        <p v-if="item.type === 'trial_activated'" class="mt-1 text-sm text-neutral-400">
          {{ t('operations.trialUntil') }}: {{ formatDate(item.end_date ?? null) }}
        </p>

        <p v-if="item.type === 'plan_payment'" class="mt-2 text-sm text-neutral-400">
          {{ t('operations.amount') }}: {{ item.amount }} {{ item.currency }}
        </p>
        <p v-if="item.type === 'plan_payment'" class="mt-1 text-sm text-neutral-400">
          {{ t('operations.months') }}: {{ item.months ?? '—' }}
        </p>
      </div>
    </div>
  </div>
</template>
