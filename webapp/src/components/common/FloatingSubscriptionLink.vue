<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { copyToClipboard } from '@/lib/utils'
import { hapticError, hapticSuccess } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'

const props = defineProps<{
  url: string
}>()

const { t } = useI18n()
const { success, error } = useToast()

async function copySubscriptionLink() {
  if (!props.url) return
  try {
    await copyToClipboard(props.url)
    hapticSuccess()
    success(t('common.copied'))
  } catch {
    hapticError()
    error(t('common.error'))
  }
}
</script>

<template>
  <Transition name="floating-link">
    <div
      v-if="url"
      class="pointer-events-none fixed inset-x-0 z-40 px-4"
      style="bottom: calc(env(safe-area-inset-bottom) + 80px)"
    >
      <button
        class="pointer-events-auto mx-auto flex w-full max-w-md cursor-pointer items-center gap-3 rounded-[14px] border border-neutral-700 bg-neutral-950/95 px-4 py-3 text-left backdrop-blur"
        @click="copySubscriptionLink"
      >
        <div class="min-w-0 flex-1">
          <p class="text-xs text-neutral-500">{{ t('home.subLink') }}</p>
          <p class="truncate text-sm text-white">{{ url }}</p>
        </div>
        <Icon icon="lucide:copy" class="size-4 shrink-0 text-neutral-300" />
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.floating-link-enter-active,
.floating-link-leave-active {
  transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.floating-link-enter-from,
.floating-link-leave-to {
  opacity: 0;
  transform: translateY(18px);
}
</style>
