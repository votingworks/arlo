/* eslint-disable @typescript-eslint/camelcase */
import fs from 'fs'
import path from 'path'
import pdf from 'pdf-parse'
import MailDev from 'maildev'

const repoRoot = path.join(__dirname, '..') // assumes pdf at project root

export async function getPdfContent(pdfName) {
  const pdfPathname = path.join(repoRoot, pdfName)
  const dataBuffer = fs.readFileSync(pdfPathname)
  return pdf(dataBuffer)
}

export function configureDownloadDirectory(on) {
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
export function setupMockSmtpServer(on) {
  const maildev = new MailDev({
    ip: process.env.ARLO_SMTP_HOST,
    smtp: process.env.ARLO_SMTP_PORT,
    incomingUser: process.env.ARLO_SMTP_USERNAME,
    incomingPass: process.env.ARLO_SMTP_PASSWORD,
    disableWeb: true,
  })
  maildev.listen()

  // email address -> last email received
  let lastEmail = {}
  maildev.on('new', email => {
    lastEmail[email.headers.to] = email
  })

  const waitForValue = (valueFn, delay = 100) =>
    new Promise((resolve, _reject) => {
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

    waitForEmail(emailAddress) {
      return waitForValue(() => lastEmail[emailAddress])
    },
  })
}
