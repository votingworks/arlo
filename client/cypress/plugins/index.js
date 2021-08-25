/// <reference types="cypress" />
// ***********************************************************
// This example plugins/index.js can be used to load plugins
//
// You can change the location of this file or turn off loading
// the plugins file with the 'pluginsFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/plugins-guide
// ***********************************************************

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)

/**
 * @type {Cypress.PluginConfig}
 */
const fs = require('fs')
const path = require('path')
const pdf = require('pdf-parse')
const MailDev = require('maildev')

const repoRoot = path.join(__dirname, '..', '..') // assumes pdf at project root

const parsePdf = async pdfName => {
  const pdfPathname = path.join(repoRoot, pdfName)
  let dataBuffer = fs.readFileSync(pdfPathname)
  return await pdf(dataBuffer) // use async/await since pdf returns a promise
}

// `on` is used to hook into various events Cypress emits
// `config` is the resolved Cypress config
module.exports = (on, config) => {
  on('task', {
    getPdfContent(pdfName) {
      return parsePdf(pdfName)
    },
  })
  on('before:browser:launch', (browser = {}, launchOptions) => {
    const downloadDirectory = path.join(__dirname, '..', 'downloads')

    if (browser.family === 'chromium' && browser.name !== 'electron') {
      launchOptions.preferences.default['download'] = {
        default_directory: downloadDirectory,
        prompt_for_download: false,
        directory_upgrade: false,
      }
    }
    return launchOptions
  })

  // Set up a mock SMTP server to intercept emails
  // Based on https://github.com/bahmutov/cypress-email-example
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
    new Promise((resolve, reject) => {
      ;(function wait() {
        const value = valueFn()
        if (value !== null && value !== undefined) return resolve(value)
        return setTimeout(wait, delay)
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
