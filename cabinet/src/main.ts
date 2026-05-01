import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { addCollection } from '@iconify/vue'
import lucide from '@iconify-json/lucide/icons.json'
import App from './App.vue'
import router from './router'
import { i18n } from '@/i18n/i18n.ts'
import './assets/main.css'

addCollection(lucide)

window.addEventListener('contextmenu', (event) => {
  event.preventDefault()
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)

router.isReady().then(() => {
  app.mount('#app')
})
