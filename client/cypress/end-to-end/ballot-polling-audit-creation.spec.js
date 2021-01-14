before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Audit creation, filling in standard ballot polling values', () => {
  beforeEach(() => {
    const uuid = () => Cypress._.random(0, 1e6)
    const id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_POLLING"]').check({ force: true })
    cy.get('input[value="BRAVO"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.contains('Audit Setup')
  })

  it('sidebar changes stages', () => {
    cy.findAllByText('Participants').should('have.length', 2)
    cy.findByText('Audit Settings').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
  })

  it('save & next and back buttons change stage', () => {
    cy.findAllByText('Participants').should('have.length', 2)
    cy.findByText('Audit Settings').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
    cy.get('#state').select('AL')
    cy.get('input[name=electionName]').type(`Test Election`)
    cy.get('input[value="online"]').check({ force: true })
    cy.get('#risk-limit').select('10')
    cy.get('input[name=randomSeed]').type('543210')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByText('Back').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
  })
})
