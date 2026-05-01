<script setup lang="ts">
import { ActionListButton, PageHeroCard } from '@/components/common'
import { hapticImpact, openLink } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

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
  <div class="mx-auto flex min-h-[calc(100dvh-9rem)] w-full max-w-5xl flex-col gap-4 pt-3 pb-6">
    <PageHeroCard
      icon="bx:support"
      :title="t('support.title')"
      :description="t('support.description')"
    />

    <div class="mt-2 flex flex-col gap-3">
      <ActionListButton icon="lucide:circle-help" :label="t('support.faq')" @click="openFaq" />

      <ActionListButton
        icon="lucide:monitor-smartphone"
        :label="t('support.setupOtherDevice')"
        @click="openOtherDeviceSetup"
      />

      <ActionListButton
        :disabled="!supportUrl"
        icon="lucide:message-circle"
        :label="t('support.contact')"
        @click="openSupport"
      />
    </div>
  </div>
</template>
