describe('Basic ballot polling audit', () => {
  before(() => cy.exec('./cypress/seed-test-db.sh'))

  it('runs', () => {
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
  })
})
