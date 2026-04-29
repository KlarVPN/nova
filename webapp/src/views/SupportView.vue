<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { Button } from '@/components/ui/button'
import { hapticImpact, openLink } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const supportUrl = computed(() => auth.profile?.links.support || '')

function openFaq() {
  hapticImpact('light')
  router.push({ name: 'faq' })
}

function openOtherDeviceSetup() {
  hapticImpact('light')
  router.push({ name: 'support-setup' })
}

function openSupport() {
  if (!supportUrl.value) return
  hapticImpact('light')
  openLink(supportUrl.value)
}
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-3 pb-6">
    <h1 class="text-center text-2xl leading-[0.9] font-medium tracking-tight text-white">
      {{ t('support.title') }}
    </h1>
    <p class="mx-auto max-w-[36ch] text-center text-sm text-neutral-400">
      {{ t('support.description') }}
    </p>

    <div class="mt-2 flex flex-col gap-3">
      <Button
        class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
        @click="openFaq"
      >
        <Icon icon="lucide:circle-help" class="size-4 shrink-0 text-neutral-500" />
        <span class="font-medium text-white">{{ t('support.faq') }}</span>
      </Button>

      <Button
        class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
        @click="openOtherDeviceSetup"
      >
        <Icon icon="lucide:monitor-smartphone" class="size-4 shrink-0 text-neutral-500" />
        <span class="font-medium text-white">{{ t('support.setupOtherDevice') }}</span>
      </Button>

      <Button
        :disabled="!supportUrl"
        class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] border border-neutral-800 bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
        @click="openSupport"
      >
        <Icon icon="lucide:message-circle" class="size-4 shrink-0 text-neutral-500" />
        <span class="font-medium text-white">{{ t('support.contact') }}</span>
      </Button>
    </div>
  </div>
</template>
