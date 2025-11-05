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
  // CSS namespace, but we don't use that. This causes a runtime exception since
  // `process` is not defined in the browser environment. So we define these to
  // be the value that Blueprint actually uses.
  define: {
    'process.env.BLUEPRINT_NAMESPACE': '"bp3"',
    'process.env.REACT_APP_BLUEPRINT_NAMESPACE': '"bp3"',
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
    setupFiles: ['src/setupTests.ts'],
    coverage: {
      thresholds: {
        lines: -206,
        branches: -217,
      },
    },
  },
})
