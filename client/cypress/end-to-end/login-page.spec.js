before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Audit creation, filling in standard ballot comparison values', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('arlo login page opens', () => {
    cy.title('Arlo (by VotingWorks)')
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.contains('Log in to your audit')
    cy.contains('State-level audit administrators: Log in as an admin')
  })

  it('logins as a audit admin', () => {
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.contains('Audits - Cypress Test Org')
  })
})
