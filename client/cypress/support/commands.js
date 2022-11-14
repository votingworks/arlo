// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

import url from 'url'
import qs from 'querystring'

Cypress.Commands.add('loginAuditAdmin', email => {
  cy.request({ url: '/auth/auditadmin/start', followRedirect: false }).then(
    response => {
      const { state } = qs.parse(url.parse(response.headers.location).query)
      const callbackParams = qs.stringify({
        code: email,
        state,
      })
      cy.visit(`/auth/auditadmin/callback?${callbackParams}`)
    }
  )
})

Cypress.Commands.add('loginJurisdictionAdmin', jaEmail => {
  cy.task('clearEmails')
  cy.findByLabelText('Enter your email to log in:').type(jaEmail)
  cy.findByRole('button', { name: 'Log in to your audit' }).click()
  cy.task('waitForEmail', jaEmail).then(email => {
    const [_, code] = email.text.match(
      /Your verification code is: (\d\d\d\d\d\d)/
    )
    cy.findByLabelText('Enter the six-digit code below:').type(code)
    cy.findByRole('button', { name: 'Submit code' }).click()
  })
})

Cypress.Commands.add('logout', email => {
  cy.intercept('/auth/logout').as('logout')
  cy.intercept('/api/me').as('me')
  if (email) {
    cy.findByRole('button', { name: new RegExp(email) }).click()
  }
  cy.findByRole('link', { name: 'Log out' }).click()
  cy.wait('@logout')
  cy.wait('@me')
  cy.contains('Participating in an audit in your local jurisdiction?')
})

// Whenever we check for a toast, we should also close it before moving forward,
// because otherwise it might cover up the user menu or other items we need to
// find on the screen.
Cypress.Commands.add('findAndCloseToast', message => {
  cy.findByRole('alert')
    .contains(message)
    .parent()
    .findByRole('button', { name: 'close' })
    .click()
})
