<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/toast'
import { Skeleton } from '@/components/common'

const { t } = useI18n()
const { success, error } = useToast()

const loading = ref(true)
const accessUrl = ref('')

onMounted(async () => {
  try {
    const res = await api.auth.accessLink()
    accessUrl.value = res.url
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
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-4 pb-6">
    <div class="rounded-[14px] bg-neutral-950 p-4">
      <h1 class="text-lg font-semibold text-white">{{ t('accessSave.title') }}</h1>
    </div>

    <div class="rounded-[14px] bg-neutral-950 p-4">
      <div class="mb-2 flex items-center gap-2">
        <Icon icon="lucide:megaphone" class="size-4 text-[#bdfe00]" />
        <p class="font-medium text-white">{{ t('accessSave.channelTitle') }}</p>
      </div>
      <p class="text-sm text-neutral-400">{{ t('accessSave.channelDesc') }}</p>
    </div>

    <div class="rounded-[14px] bg-neutral-950 p-4">
      <div class="mb-2 flex items-center gap-2">
        <Icon icon="lucide:link" class="size-4 text-[#bdfe00]" />
        <p class="font-medium text-white">{{ t('accessSave.linkTitle') }}</p>
      </div>
      <p class="mb-3 text-sm text-neutral-400">{{ t('accessSave.linkDesc') }}</p>

      <Skeleton v-if="loading" class="h-12" />
      <button
        v-else
        type="button"
        class="flex w-full cursor-pointer items-center gap-3 rounded-[14px] bg-neutral-950/95 px-4 py-3 text-left"
        @click="copyLink"
      >
        <div class="min-w-0 flex-1">
          <p class="text-xs text-neutral-500">{{ t('accessSave.linkTitle') }}</p>
          <p class="truncate text-sm text-white">{{ accessUrl }}</p>
        </div>
        <Icon icon="lucide:copy" class="size-4 shrink-0 text-neutral-300" />
      </button>
    </div>
  </div>
</template>
