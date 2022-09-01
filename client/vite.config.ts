import { defineConfig } from 'vite'

const devFlaskServerUrl = 'http://localhost:3001'

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    outDir: 'build',
  },
  // Blueprint (UI component library) tries to check some env variables to set a
  // CSS namespace, but we don't use that. It breaks because `process` is not
  // defined. To fix we just substitute undefined, which causes Blueprint to use
  // a default namespace.
  define: {
    'process.env.BLUEPRINT_NAMESPACE': 'undefined',
    'process.env.REACT_APP_BLUEPRINT_NAMESPACE': 'undefined',
  },
  // Configure the Vite dev server to proxy API requests to the dev Flask server
  server: {
    proxy: {
      '/api': devFlaskServerUrl,
      '/auth': devFlaskServerUrl,
      '/auditboard': devFlaskServerUrl,
    },
    port: 3000,
  },
})
