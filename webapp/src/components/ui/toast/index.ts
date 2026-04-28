export { default as Toaster } from './Toaster.vue'

import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

const toasts = ref<Toast[]>([])
let counter = 0

export function useToast() {
  function show(message: string, type: Toast['type'] = 'info') {
    const id = ++counter
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      const i = toasts.value.findIndex((t) => t.id === id)
      if (i !== -1) toasts.value.splice(i, 1)
    }, 3500)
  }

  return {
    toasts,
    show,
    success: (m: string) => show(m, 'success'),
    error: (m: string) => show(m, 'error'),
    info: (m: string) => show(m, 'info'),
  }
}
