<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import { copyToClipboard } from '@/lib/utils'
import { hapticError, hapticSuccess } from '@/lib/telegram'
import { useToast } from '@/components/ui/toast'

const props = defineProps<{
  url: string
  text: string
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
  <Teleport to="body">
    <Transition name="floating-link">
      <div
        v-if="props.url"
        class="pointer-events-none fixed inset-x-0 z-40 px-3"
        style="bottom: calc(env(safe-area-inset-bottom) + 80px)"
      >
        <button
          class="pointer-events-auto mx-auto flex w-full max-w-md cursor-pointer items-center gap-3 rounded-[14px] bg-neutral-900/45 px-4 py-3 text-left backdrop-blur-xl"
          @click="copySubscriptionLink"
        >
          <div class="min-w-0 flex-1">
            <p class="text-xs text-neutral-500">{{ props.text }}</p>
            <p class="truncate text-sm text-white">{{ props.url }}</p>
          </div>
          <Icon icon="lucide:copy" class="size-4 shrink-0 text-neutral-300" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.floating-link-enter-active,
.floating-link-leave-active {
  transition:
    opacity 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.floating-link-enter-from,
.floating-link-leave-to {
  opacity: 0;
  transform: translateY(18px);
}
</style>
