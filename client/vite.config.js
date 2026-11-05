import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    // West of UTC, so date-only parsing bugs (UTC midnight = previous local day) show up in tests
    env: { TZ: 'America/Los_Angeles' }
  }
})
