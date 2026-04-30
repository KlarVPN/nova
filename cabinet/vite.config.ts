import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, dirname } from 'node:path'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'
import tailwindcss from '@tailwindcss/vite'

// Vite 8 uses Rolldown as the default bundler
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    VueI18nPlugin({
      include: resolve(__dirname, './src/i18n/locales/**'),
      runtimeOnly: false,
      compositionOnly: false,
      strictMessage: false,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes('node_modules/vue/') ||
            id.includes('node_modules/vue-router/') ||
            id.includes('node_modules/pinia/')
          ) {
            return 'vue'
          }
          if (id.includes('node_modules/radix-vue/')) {
            return 'radix'
          }
          if (
            id.includes('node_modules/@iconify/vue/') ||
            id.includes('node_modules/@iconify-json/lucide/')
          ) {
            return 'iconify'
          }
          return undefined
        },
      },
    },
  },
  server: {
    allowedHosts: ['ny0b3on6hopq.share.zrok.io'],
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
