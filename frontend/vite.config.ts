import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import pkg from './package.json' with { type: 'json' }

export default defineConfig({
  define: {
    // Expose the app version as a compile-time constant so the service worker
    // registration can namespace its caches per release (see main.tsx and
    // public/sw.js). Hardcoded cache names produce the classic "white screen
    // on restart" when chunk hashes change.
    APP_VERSION: JSON.stringify(pkg.version),
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        // In Docker dev: backend:8080, local dev: localhost:8080
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
