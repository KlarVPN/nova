export { default as Toaster } from './Toaster.vue'

import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'loading'
}

const toasts = ref<Toast[]>([])
let counter = 0

function dismiss(id: number) {
  const i = toasts.value.findIndex((t) => t.id === id)
  if (i !== -1) toasts.value.splice(i, 1)
}

export function useToast() {
  function show(message: string, type: Toast['type'] = 'info') {
    const id = ++counter
    toasts.value.push({ id, message, type })
    setTimeout(() => dismiss(id), 3500)
  }

  function loading(message: string): () => void {
    const id = ++counter
    toasts.value.push({ id, message, type: 'loading' })
    return () => dismiss(id)
  }

  return {
    toasts,
    show,
    loading,
    success: (m: string) => show(m, 'success'),
    error: (m: string) => show(m, 'error'),
    info: (m: string) => show(m, 'info'),
  }
}
