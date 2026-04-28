<script setup lang="ts">
import { useToast } from '.'
const { toasts } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto glass flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium shadow-lg"
          :class="{
            'text-success': toast.type === 'success',
            'text-destructive': toast.type === 'error',
            'text-foreground': toast.type === 'info',
          }"
        >
          <span v-if="toast.type === 'success'" class="text-base leading-none">✓</span>
          <span v-else-if="toast.type === 'error'" class="text-base leading-none">✕</span>
          <span>{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.95);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>
