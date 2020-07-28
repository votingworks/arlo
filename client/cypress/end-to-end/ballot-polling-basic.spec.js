describe('Basic ballot polling audit', () => {
  it('runs', () => {
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
  })
})

describe('Audit setup', () => {
  it('Creates an audit', () => {
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.contains('Give your new audit a unique name.').type('Audit One')
    cy.contains('Create a New Audit').click()
    cy.url()
      .should('include', '/setup')
      .and('include', '/election/')
    cy.get('h4').should('contain', 'The audit has not started.')
  })
})
