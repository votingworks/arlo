before(() => cy.exec('./cypress/seed-test-db.sh'))

describe.skip('Ballot Polling Audit Creation', () => {
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

  describe('Creating an offline audit', () => {
    it('AA sets up audit', () => {
      cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet.csv').then(fileContent => {
        cy.get('input[type="file"]').first().attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_jurisdiction_filesheet.csv',
          mimeType: 'csv'
        })
      })
      cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
        firstButton.click()
      })
      cy.contains("Upload successfully completed")   
  
      cy.wait(100) // gets stuck in an infinite loop without a 100ms wait here
      cy.findByText('Next').click()
      cy.get('input[name="contests[0].name"]').type('Contest')
      cy.get('input[name="contests[0].choices[0].name"]').type('A')
      cy.get('input[name="contests[0].choices[0].numVotes"]').type('300')
      cy.get('input[name="contests[0].choices[1].name"]').type('B')
      cy.get('input[name="contests[0].choices[1].numVotes"]').type('100')
      cy.get('input[name="contests[0].totalBallotsCast"]').type('400')
      cy.findByText('Select Jurisdictions').click()
      cy.findByLabelText('Death Star').check({ force: true })
      cy.findByText('Save & Next').click()
      cy.findAllByText('Opportunistic Contests').should('have.length', 2)
      cy.findByText('Save & Next').click()
      cy.get('#state').select('AL')
      cy.get('input[name=electionName]').type(`Test Election`)
      cy.get('#risk-limit').select('10')
      cy.get('input[name=randomSeed]').type("543210")
      cy.findByText('Save & Next').click()
      cy.findAllByText('Review & Launch').should('have.length', 2)
    })
  })

  describe('Creating an online audit', () => {
    it('AA sets up audit', () => {
      cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet.csv').then(fileContent => {
        cy.get('input[type="file"]').first().attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_jurisdiction_filesheet.csv',
          mimeType: 'csv'
        })
      })
      cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
        firstButton.click()
      })
      cy.contains("Upload successfully completed")   
  
      cy.wait(100) // gets stuck in an infinite loop without a 100ms wait here
      cy.findByText('Next').click()
      cy.get('input[name="contests[0].name"]').type('Contest')
      cy.get('input[name="contests[0].choices[0].name"]').type('A')
      cy.get('input[name="contests[0].choices[0].numVotes"]').type('300')
      cy.get('input[name="contests[0].choices[1].name"]').type('B')
      cy.get('input[name="contests[0].choices[1].numVotes"]').type('100')
      cy.get('input[name="contests[0].totalBallotsCast"]').type('400')
      cy.findByText('Select Jurisdictions').click()
      cy.findByLabelText('Death Star').check({ force: true })
      cy.findByText('Save & Next').click()
      cy.findAllByText('Opportunistic Contests').should('have.length', 2)
      cy.findByText('Save & Next').click()
      cy.get('#state').select('AL')
      cy.get('input[name=electionName]').type(`Test Election`)
      cy.get("input[value=online]").click({ force: true })
      cy.get('#risk-limit').select('10')
      cy.get('input[name=randomSeed]').type("543210")
      cy.findByText('Save & Next').click()
      cy.findAllByText('Review & Launch').should('have.length', 2)
    })
  })
})
