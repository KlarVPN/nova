<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge } from '@/components/ui/badge'

const props = defineProps<{
  status: 'active' | 'inactive' | 'expired' | 'trial'
}>()

const { t } = useI18n()

const config = computed(() => {
  const map = {
    active: { label: t('status.active'), variant: 'default' as const, dot: 'bg-accent' },
    inactive: { label: t('status.inactive'), variant: 'outline' as const, dot: 'bg-muted-foreground' },
    expired: { label: t('status.expired'), variant: 'destructive' as const, dot: 'bg-destructive' },
    trial: { label: t('status.trial'), variant: 'info' as const, dot: 'bg-info' },
  }
  return map[props.status]
})
</script>

<template>
  <Badge :variant="config.variant" class="gap-1.5">
    <span class="h-1.5 w-1.5 rounded-full" :class="config.dot" />
    {{ config.label }}
  </Badge>
</template>
