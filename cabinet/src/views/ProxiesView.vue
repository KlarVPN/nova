<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { api } from '@/lib/api'
import { hapticImpact, openLink } from '@/lib/telegram'
import type { ProxyItem } from '@/types'
import { PageHeroCard } from '@/components/common'

const { t } = useI18n()

const loading = ref(false)
const proxies = ref<ProxyItem[]>([])
const probeState = ref<
  Record<string, { status: 'online' | 'offline' | 'unknown'; ping_ms: number | null }>
>({})

function flagEmojiToCode(flagEmoji: string): string | null {
  const chars = Array.from(flagEmoji || '')
  if (chars.length !== 2) return null
  const base = 0x1f1e6
  const first = chars[0].codePointAt(0)
  const second = chars[1].codePointAt(0)
  if (!first || !second) return null
  if (first < base || first > 0x1f1ff || second < base || second > 0x1f1ff) return null
  return String.fromCharCode(first - base + 65, second - base + 65).toLowerCase()
}

function pingClass(status: 'online' | 'offline' | 'unknown', ping: number | null) {
  if (status !== 'online' || ping == null) return 'text-rose-300'
  if (ping <= 120) return 'text-emerald-300'
  if (ping <= 250) return 'text-amber-300'
  return 'text-rose-300'
}

async function probeProxy(link: string) {
  const start = performance.now()
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 2500)

  try {
    await fetch(link, {
      method: 'GET',
      mode: 'no-cors',
      cache: 'no-store',
      signal: controller.signal,
    })
    const ping = Math.round(performance.now() - start)
    probeState.value[link] = { status: 'online', ping_ms: ping }
  } catch {
    probeState.value[link] = { status: 'offline', ping_ms: null }
  } finally {
    window.clearTimeout(timeout)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await api.proxies.list()
    proxies.value = data.proxies || []
    for (const proxy of proxies.value) {
      probeState.value[proxy.link] = { status: 'unknown', ping_ms: null }
    }
    await Promise.all(proxies.value.map((proxy) => probeProxy(proxy.link)))
  } finally {
    loading.value = false
  }
})

function openProxy(link: string) {
  if (!link) return
  hapticImpact('light')
  openLink(link)
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-3 pb-6">
    <PageHeroCard
      :title="t('proxies.title')"
      :description="t('proxies.description')"
      icon="mdi:proxy"
    />

    <div class="rounded-[14px] bg-neutral-950 p-4 text-sm text-neutral-300">
      <p class="font-medium text-white">{{ t('proxies.helpTitle') }}</p>
      <p class="mt-2">{{ t('proxies.helpIntro') }}</p>
      <ul class="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
        <li>{{ t('proxies.benefit1') }}</li>
        <li>{{ t('proxies.benefit2') }}</li>
        <li>{{ t('proxies.benefit3') }}</li>
      </ul>
      <p class="mt-3 text-neutral-300">{{ t('proxies.disableTitle') }}</p>
      <p class="mt-1 text-neutral-400">{{ t('proxies.disablePath') }}</p>
      <p class="mt-3 text-neutral-300">{{ t('proxies.fallbackTitle') }}</p>
      <p class="mt-1 text-neutral-400">{{ t('proxies.fallbackText') }}</p>
    </div>

    <div v-if="loading" class="flex h-32 items-center justify-center">
      <Icon icon="lucide:loader-circle" class="size-8 animate-spin text-neutral-400" />
    </div>

    <div
      v-else-if="!proxies.length"
      class="rounded-[14px] bg-neutral-950 p-4 text-center text-sm text-neutral-400"
    >
      {{ t('proxies.empty') }}
    </div>

    <div v-else class="flex flex-col gap-3">
      <button
        v-for="proxy in proxies"
        :key="proxy.link"
        class="flex w-full cursor-pointer items-center gap-3 rounded-[14px] bg-neutral-950 px-4 py-3 text-left transition-colors hover:bg-neutral-900"
        @click="openProxy(proxy.link)"
      >
        <Icon
          v-if="flagEmojiToCode(proxy.emoji || '')"
          :icon="`circle-flags:${flagEmojiToCode(proxy.emoji || '')}`"
          class="size-5 rounded-full"
        />
        <Icon v-else icon="lucide:globe" class="size-5 text-neutral-500" />
        <div class="min-w-0 flex-1">
          <p class="font-medium text-white">{{ proxy.country }}</p>
          <p
            class="text-xs"
            :class="
              pingClass(
                probeState[proxy.link]?.status ?? 'unknown',
                probeState[proxy.link]?.ping_ms ?? null,
              )
            "
          >
            {{
              probeState[proxy.link]?.ping_ms != null
                ? `${Math.round(probeState[proxy.link].ping_ms!)} ms`
                : t('proxies.unavailable')
            }}
          </p>
        </div>
        <Icon icon="lucide:chevron-right" class="size-4 text-neutral-500" />
      </button>
    </div>
  </div>
</template>
