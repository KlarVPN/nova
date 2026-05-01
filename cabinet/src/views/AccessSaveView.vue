<script setup lang="ts">
import { PageHeroCard, Skeleton } from '@/components/common'
import { useToast } from '@/components/ui/toast'
import { api } from '@/lib/api'
import { openLink } from '@/lib/telegram'
import { Icon } from '@iconify/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const { success, error } = useToast()

const loading = ref(true)
const accessUrl = ref('')
const channelUrl = ref('')

onMounted(async () => {
  try {
    const [res, channelStatus] = await Promise.all([
      api.auth.accessLink(),
      api.channel.status().catch(() => null),
    ])
    accessUrl.value = res.url
    channelUrl.value = channelStatus?.channel_link || ''
  } catch {
    error(t('common.error'))
  } finally {
    loading.value = false
  }
})

async function copyLink() {
  if (!accessUrl.value) return
  try {
    await navigator.clipboard.writeText(accessUrl.value)
    success(t('accessSave.copied'))
  } catch {
    error(t('common.error'))
  }
}

function goToChannel() {
  if (!channelUrl.value) {
    error(t('common.error'))
    return
  }
  openLink(channelUrl.value)
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-4 pb-6">
    <PageHeroCard
      :title="t('accessSave.title')"
      :description="t('accessSave.description')"
      icon="lucide:save"
    />

    <div class="rounded-[14px] bg-neutral-950 p-4">
      <div class="mb-2 flex items-center gap-2">
        <Icon icon="lucide:megaphone" class="size-4" />
        <p class="font-medium text-white">{{ t('accessSave.channelTitle') }}</p>
      </div>
      <p class="text-sm text-neutral-400">{{ t('accessSave.channelDesc') }}</p>
      <button
        v-if="channelUrl"
        type="button"
        class="mt-3 inline-flex cursor-pointer items-center gap-2 rounded-[10px] bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-800"
        @click="goToChannel"
      >
        <Icon icon="lucide:external-link" class="size-4" />
        {{ t('accessSave.channelButton') }}
      </button>
    </div>

    <div class="rounded-[14px] bg-neutral-950 p-4">
      <div class="mb-2 flex items-center gap-2">
        <Icon icon="lucide:link" class="size-4" />
        <p class="font-medium text-white">{{ t('accessSave.linkTitle') }}</p>
      </div>
      <p class="mb-3 text-sm text-neutral-400">{{ t('accessSave.linkDesc') }}</p>

      <Skeleton v-if="loading" class="h-12" />
      <button
        v-else
        type="button"
        class="flex w-full cursor-pointer items-center gap-3 rounded-[14px] bg-neutral-900/95 px-4 py-3 text-left"
        @click="copyLink"
      >
        <p class="truncate text-sm text-white">{{ accessUrl }}</p>
        <Icon icon="lucide:copy" class="size-4 shrink-0 text-neutral-300" />
      </button>
    </div>
  </div>
</template>
