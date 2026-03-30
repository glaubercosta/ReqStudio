import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // Porta do dev server local (npm run dev)
    // Separada do Docker que expõe FRONTEND_PORT (5174 por padrão)
    port: 5175,
    strictPort: false, // auto-incrementa se 5175 estiver ocupada
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/components/**', 'src/hooks/**', 'src/pages/**'],
      exclude: ['src/test/**'],
      thresholds: { lines: 70, functions: 70 },
    },
  },
})
