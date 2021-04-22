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
// import 'cypress-file-upload'

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

Cypress.Commands.add('loginJurisdictionAdmin', email => {
  cy.request({
    url: '/auth/jurisdictionadmin/start',
    followRedirect: false,
  }).then(response => {
    const { state } = qs.parse(url.parse(response.headers.location).query)
    const callbackParams = qs.stringify({
      code: email,
      state,
    })
    cy.visit(`/auth/jurisdictionadmin/callback?${callbackParams}`)
  })
})

Cypress.Commands.add('logout', email => {
  cy.intercept('/auth/logout').as('logout')
  cy.findByText(email).click()
  cy.findByText('Log out').click()
  cy.wait(['@logout'])
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
