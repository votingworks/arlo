import { defineConfig } from 'cypress'
import {
  getPdfContent,
  setupMockSmtpServer,
  configureDownloadDirectory,
} from './cypress/plugins'

export default defineConfig({
  // We only really need videos on failures in CI, so if there's a failure in
  // CI, we can just turn this setting on and run the tests again.
  video: false,
  viewportWidth: 1000,
  viewportHeight: 1000,
  defaultCommandTimeout: 10000,
  e2e: {
    setupNodeEvents(on, _config) {
      on('task', { getPdfContent })
      configureDownloadDirectory(on)
      setupMockSmtpServer(on)
    },
    baseUrl: 'http://localhost:3000',
    specPattern: 'cypress/end-to-end/**/*.cy.{js,jsx,ts,tsx}',
  },
})
