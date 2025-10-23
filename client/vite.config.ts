import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

const devFlaskServerUrl = 'http://localhost:3001'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'classic',
    }),
  ],
  build: {
    outDir: 'build',
  },
  // Blueprint (UI component library) tries to check some env variables to set a
  // CSS namespace, but we don't use that. We define these as empty strings so
  // Blueprint falls back to its default "bp3" namespace.
  define: {
    'process.env.BLUEPRINT_NAMESPACE': '""',
    'process.env.REACT_APP_BLUEPRINT_NAMESPACE': '""',
  },
  // Configure the Vite dev server to proxy API requests to the dev Flask server
  server: {
    proxy: {
      '/api': devFlaskServerUrl,
      '/auth': devFlaskServerUrl,
      '/auditboard': devFlaskServerUrl,
      '/tallyentry': devFlaskServerUrl,
    },
    port: 3000,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/setupTests.ts']
  }
})
