<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/lib/api'
import type { LocationStatus } from '@/types'
import PageHeroCard from '@/components/common/PageHeroCard.vue'

const { t } = useI18n()

const loading = ref(false)
const locations = ref<LocationStatus[]>([])
const filter = ref<'all' | 'online' | 'offline'>('all')
let refreshTimer: number | null = null

const filtered = computed(() => {
  let list = [...locations.value]
  if (filter.value === 'online') list = list.filter((item) => item.status === 'online')
  if (filter.value === 'offline') list = list.filter((item) => item.status === 'offline')
  return list
})

function flagEmojiToCode(flagEmoji: string): string | null {
  const chars = Array.from(flagEmoji)
  if (chars.length !== 2) return null
  const base = 0x1f1e6
  const first = chars[0].codePointAt(0)
  const second = chars[1].codePointAt(0)
  if (!first || !second) return null
  if (first < base || first > 0x1f1ff || second < base || second > 0x1f1ff) return null
  return String.fromCharCode(first - base + 65, second - base + 65).toLowerCase()
}

function splitLocationName(rawName: string): { flagCode: string | null; title: string } {
  const match = rawName.trim().match(/^([\u{1F1E6}-\u{1F1FF}]{2})\s*(.+)$/u)
  if (!match) return { flagCode: null, title: rawName }
  return {
    flagCode: flagEmojiToCode(match[1]),
    title: match[2].trim() || rawName,
  }
}

async function fetchLocations() {
  if (loading.value) return
  loading.value = true
  try {
    const response = await api.locations.list()
    locations.value = response.locations
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchLocations()
  refreshTimer = window.setInterval(fetchLocations, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-2 pb-6">
    <div class="flex items-center justify-between">
      <PageHeroCard
        icon="lucide:map"
        :title="t('locations.title')"
        :description="t('support.description')"
      />
    </div>

    <div class="grid grid-cols-3 gap-1">
      <button
        class="cursor-pointer rounded-full p-3 text-xs font-medium transition-all"
        :class="filter === 'all' ? 'bg-neutral-900 text-white' : 'bg-neutral-950 text-neutral-300'"
        @click="filter = 'all'"
      >
        {{ t('locations.filters.all') }}
      </button>
      <button
        class="cursor-pointer rounded-full p-3 text-xs font-medium transition-all"
        :class="
          filter === 'online'
            ? 'bg-emerald-950/30 text-emerald-300'
            : 'bg-neutral-950 text-neutral-300'
        "
        @click="filter = 'online'"
      >
        {{ t('locations.filters.online') }}
      </button>
      <button
        class="cursor-pointer rounded-full p-3 text-xs font-medium transition-all"
        :class="
          filter === 'offline' ? 'bg-rose-950/30 text-rose-300' : 'bg-neutral-950 text-neutral-300'
        "
        @click="filter = 'offline'"
      >
        {{ t('locations.filters.offline') }}
      </button>
    </div>

    <div v-if="loading" class="py-10 text-center text-sm text-neutral-400">
      {{ t('common.loading') }}
    </div>

    <div v-else class="flex flex-col gap-2">
      <div
        v-for="item in filtered"
        :key="`${item.country}-${item.name}`"
        class="rounded-[14px] bg-neutral-950 px-4 py-3"
      >
        <div class="flex items-center gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <Icon
                v-if="splitLocationName(item.name).flagCode"
                :icon="`circle-flags:${splitLocationName(item.name).flagCode}`"
                class="size-4 rounded-full"
              />
              <p class="truncate font-medium text-white">
                {{ splitLocationName(item.name).title }}
              </p>
            </div>
          </div>
          <p
            class="font-mono text-sm font-semibold"
            :class="
              item.status === 'online'
                ? 'text-emerald-300'
                : item.status === 'offline'
                  ? 'text-rose-300'
                  : item.status === 'pending'
                    ? 'text-amber-300'
                    : 'text-neutral-300'
            "
          >
            {{ item.uptime_pct != null ? `${item.uptime_pct}% ${t('locations.uptime')}` : '—' }}
          </p>
        </div>

        <div class="mt-2 flex w-full items-center gap-0.5">
          <span
            v-for="(point, idx) in item.availability"
            :key="idx"
            class="h-4 min-w-0 flex-1 rounded-[2px]"
            :class="point ? 'bg-emerald-400' : 'bg-rose-500'"
          />
        </div>
        <div class="mt-1 flex items-center justify-between text-[10px] text-neutral-500">
          <span>{{ t('locations.daysMonitored', { n: item.availability.length }) }}</span>
          <span>{{ t('locations.now') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
