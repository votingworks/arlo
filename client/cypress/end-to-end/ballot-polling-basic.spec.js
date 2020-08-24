before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Basic ballot polling audit', () => {
  it('runs', () => {
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
  })
})
