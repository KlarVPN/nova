<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { Button } from '@/components/ui/button'

defineProps<{
  icon: string
  label: string
  disabled?: boolean
}>()
</script>

<template>
  <Button
    :disabled="disabled"
    class="flex h-12 w-full cursor-pointer items-center justify-start gap-3 rounded-[14px] bg-neutral-950 px-4 text-left transition-colors hover:bg-neutral-900"
  >
    <Icon :icon="icon" class="size-4 shrink-0 text-neutral-500" />
    <span class="font-medium text-white">{{ label }}</span>
  </Button>
</template>
