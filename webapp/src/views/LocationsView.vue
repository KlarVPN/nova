<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/lib/api'
import type { LocationStatus } from '@/types'

const { t } = useI18n()

const loading = ref(false)
const locations = ref<LocationStatus[]>([])
const filter = ref<'all' | 'online' | 'offline'>('all')

const filtered = computed(() => {
  let list = [...locations.value]
  if (filter.value === 'online') list = list.filter((item) => item.status === 'online')
  if (filter.value === 'offline') list = list.filter((item) => item.status === 'offline')
  return list
})

const counts = computed(() => ({
  all: locations.value.length,
  online: locations.value.filter((item) => item.status === 'online').length,
  offline: locations.value.filter((item) => item.status === 'offline').length,
}))

function statusClass(status: LocationStatus['status']) {
  if (status === 'online') return 'text-emerald-400'
  if (status === 'offline') return 'text-rose-400'
  return 'text-neutral-500'
}

async function fetchLocations() {
  loading.value = true
  try {
    const response = await api.locations.list()
    locations.value = response.locations
  } finally {
    loading.value = false
  }
}

onMounted(fetchLocations)
</script>

<template>
  <div class="flex w-full flex-col gap-4 pt-2 pb-6">
    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('locations.title') }}
    </h1>

    <div class="grid grid-cols-3 gap-2">
      <button
        class="cursor-pointer rounded-[12px] border px-3 py-2 text-xs font-semibold"
        :class="
          filter === 'all'
            ? 'border-[#bdfe00] bg-neutral-900 text-[#bdfe00]'
            : 'border-neutral-800 bg-neutral-950 text-neutral-300'
        "
        @click="filter = 'all'"
      >
        {{ t('locations.filters.all') }} ({{ counts.all }})
      </button>
      <button
        class="cursor-pointer rounded-[12px] border px-3 py-2 text-xs font-semibold"
        :class="
          filter === 'online'
            ? 'border-emerald-500/60 bg-emerald-950/30 text-emerald-300'
            : 'border-neutral-800 bg-neutral-950 text-neutral-300'
        "
        @click="filter = 'online'"
      >
        {{ t('locations.filters.online') }} ({{ counts.online }})
      </button>
      <button
        class="cursor-pointer rounded-[12px] border px-3 py-2 text-xs font-semibold"
        :class="
          filter === 'offline'
            ? 'border-rose-500/60 bg-rose-950/30 text-rose-300'
            : 'border-neutral-800 bg-neutral-950 text-neutral-300'
        "
        @click="filter = 'offline'"
      >
        {{ t('locations.filters.offline') }} ({{ counts.offline }})
      </button>
    </div>

    <div v-if="loading" class="py-10 text-center text-sm text-neutral-400">
      {{ t('common.loading') }}
    </div>

    <div v-else class="flex flex-col gap-2">
      <div
        v-for="item in filtered"
        :key="`${item.country}-${item.name}`"
        class="flex items-center gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 py-3"
      >
        <span class="text-lg">{{ item.emoji || '📍' }}</span>
        <div class="min-w-0 flex-1">
          <p class="truncate font-medium text-white">{{ item.name }}</p>
          <p class="text-xs text-neutral-500">{{ item.country }}</p>
        </div>
        <div class="text-right">
          <p class="text-xs font-semibold" :class="statusClass(item.status)">
            {{ t(`locations.status.${item.status}`) }}
          </p>
          <p class="font-mono text-xs text-neutral-300">
            {{ item.uptime_pct != null ? `${item.uptime_pct}% uptime` : '—' }}
          </p>
          <p class="font-mono text-xs text-neutral-300">
            {{ item.ping_ms != null ? `${Math.round(item.ping_ms)} ms` : '—' }}
          </p>
        </div>
        <div class="ml-2 flex items-center gap-0.5">
          <span
            v-for="(point, idx) in item.availability"
            :key="idx"
            class="h-4 w-0.5 rounded-full"
            :class="point ? 'bg-emerald-400' : 'bg-rose-500/80'"
          />
        </div>
      </div>
    </div>
  </div>
</template>
