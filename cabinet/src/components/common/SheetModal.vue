<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    desktopPosition?: 'center' | 'end'
    panelClass?: string
    overlayClass?: string
    showHandle?: boolean
  }>(),
  {
    desktopPosition: 'center',
    panelClass: '',
    overlayClass: 'bg-black/70',
    showHandle: false,
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex flex-col gap-2 md:items-center md:p-4"
        :class="
          desktopPosition === 'end' ? 'justify-end md:justify-end' : 'justify-end md:justify-center'
        "
      >
        <div class="absolute inset-0" :class="overlayClass" @click="close" />
        <div class="sheet-panel relative" :class="panelClass">
          <div v-if="showHandle" class="mb-4 flex justify-center md:hidden">
            <div class="h-1 w-10 rounded-full bg-neutral-700" />
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;
}

.sheet-enter-active .sheet-panel,
.sheet-leave-active .sheet-panel {
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}

.sheet-enter-from .sheet-panel,
.sheet-leave-to .sheet-panel {
  transform: translateY(100%);
}

@media (min-width: 768px) {
  .sheet-enter-from .sheet-panel,
  .sheet-leave-to .sheet-panel {
    transform: translateY(0) scale(0.96);
  }
}
</style>
