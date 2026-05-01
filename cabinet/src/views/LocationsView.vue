<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import { motion } from 'motion-v'
import { api } from '@/lib/api'
import type { LocationStatus } from '@/types'
import { PageHeroCard } from '@/components/common'

const { t } = useI18n()

const loading = ref(false)
const locations = ref<LocationStatus[]>([])
const filter = ref<'all' | 'online' | 'offline'>('all')
let refreshTimer: number | null = null
const filterContainerRef = ref<HTMLElement | null>(null)
const filterRefs = ref<Record<'all' | 'online' | 'offline', HTMLElement | null>>({
  all: null,
  online: null,
  offline: null,
})
const bubbleX = ref(0)
const bubbleWidth = ref(0)
const bubbleReady = ref(false)

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

function setFilterRef(key: 'all' | 'online' | 'offline', el: unknown) {
  filterRefs.value[key] = (el as HTMLElement | null) ?? null
}

function syncFilterBubble() {
  const container = filterContainerRef.value
  const activeEl = filterRefs.value[filter.value]
  if (!container || !activeEl) {
    bubbleReady.value = false
    return
  }

  const containerRect = container.getBoundingClientRect()
  const activeRect = activeEl.getBoundingClientRect()
  bubbleX.value = activeRect.left - containerRect.left
  bubbleWidth.value = activeRect.width
  bubbleReady.value = true
}

watch(filter, async () => {
  await nextTick()
  syncFilterBubble()
})

onMounted(() => {
  fetchLocations()
  void nextTick(syncFilterBubble)
  window.addEventListener('resize', syncFilterBubble)
  refreshTimer = window.setInterval(fetchLocations, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncFilterBubble)
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-2 pb-6">
    <div class="flex items-center justify-between">
      <PageHeroCard
        icon="lucide:map"
        :title="t('locations.title')"
        :description="t('locations.description')"
      />
    </div>

    <div
      ref="filterContainerRef"
      class="relative grid grid-cols-3 gap-1 rounded-full bg-neutral-950 p-1"
    >
      <motion.div
        v-if="bubbleReady"
        class="pointer-events-none absolute top-1 bottom-1 z-0 rounded-full bg-neutral-800"
        :initial="false"
        :animate="{ x: bubbleX, width: bubbleWidth, opacity: 1 }"
        :transition="{ type: 'spring', stiffness: 420, damping: 36, mass: 0.45 }"
        style="left: 0"
      />
      <button
        v-for="option in ['all', 'online', 'offline']"
        :key="option"
        :ref="(el) => setFilterRef(option, el)"
        class="relative z-10 cursor-pointer rounded-full p-3 text-xs font-medium transition-all"
        :class="filter === option ? 'text-white' : 'text-neutral-400'"
        @click="filter = option"
      >
        {{ t(`locations.filters.${option}`) }}
      </button>
    </div>

    <div v-if="loading" class="py-10 text-center text-sm text-neutral-400">
      {{ t('common.loading') }}
    </div>

    <div v-else-if="filtered.length" class="flex flex-col gap-2">
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

    <div
      v-else
      class="flex flex-col items-center gap-4 rounded-[14px] bg-neutral-950 px-4 py-10 text-center"
    >
      <Icon icon="lucide:map-pin-off" class="size-16 text-neutral-500" />
      <p class="text-base font-medium text-neutral-400">{{ t('locations.empty') }}</p>
    </div>
  </div>
</template>
