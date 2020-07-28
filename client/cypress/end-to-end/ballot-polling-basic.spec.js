describe('Basic ballot polling audit', () => {
  it('runs', () => {
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
  })
})
