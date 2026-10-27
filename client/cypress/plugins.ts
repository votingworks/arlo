import fs from 'fs'
import path from 'path'
import pdf from 'pdf-parse'
import MailDev from 'maildev'

const repoRoot = path.join(__dirname, '..') // assumes pdf at project root

export async function getPdfContent(pdfName: string): Promise<pdf.Result> {
  const pdfPathname = path.join(repoRoot, pdfName)
  const dataBuffer = fs.readFileSync(pdfPathname)
  return pdf(dataBuffer)
}

export function configureDownloadDirectory(on: Cypress.PluginEvents): void {
  on('before:browser:launch', (browser, launchOptions) => {
    const downloadDirectory = path.join(__dirname, 'downloads')
    if (browser.family === 'chromium' && browser.name !== 'electron') {
      // eslint-disable-next-line no-param-reassign
      launchOptions.preferences.default.download = {
        default_directory: downloadDirectory,
        prompt_for_download: false,
        directory_upgrade: false,
      }
    }
    return launchOptions
  })
}

// Set up a mock SMTP server to intercept emails
// Based on https://github.com/bahmutov/cypress-email-example
export function setupMockSmtpServer(on: Cypress.PluginEvents): void {
  const maildev = new MailDev({
    ip: process.env.ARLO_SMTP_HOST,
    smtp: process.env.ARLO_SMTP_PORT,
    incomingUser: process.env.ARLO_SMTP_USERNAME,
    incomingPass: process.env.ARLO_SMTP_PASSWORD,
    disableWeb: true,
  })
  maildev.listen()

  // email address -> last email received
  let lastEmail: Record<string, MailDev.Email> = {}
  maildev.on('new', email => {
    lastEmail[email.headers.to] = email
  })

  const waitForValue = <T>(valueFn: () => T | undefined, delay = 100) =>
    new Promise<T>((resolve, _reject) => {
      ;(function waitHelper() {
        const value = valueFn()
        if (value !== null && value !== undefined) return resolve(value)
        return setTimeout(waitHelper, delay)
      })()
    })

  on('task', {
    clearEmails() {
      lastEmail = {}
      return null
    },

    waitForEmail(emailAddress: string) {
      return waitForValue(() => lastEmail[emailAddress])
    },
  })
}
