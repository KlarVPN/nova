<script setup lang="ts">
import QrcodeVue from 'qrcode.vue'

const props = defineProps<{
  url: string
  size?: number
  level?: 'L' | 'M' | 'Q' | 'H'
}>()

const size = props.size ?? 280
const level = props.level ?? 'H'
</script>

<template>
  <div class="flex justify-center">
    <QrcodeVue
      :value="props.url"
      :size="size"
      :level="level"
      :includeMargin="false"
      background="#000000"
      foreground="#ffffff"
    />
  </div>
</template>
