import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Offline Batch Data Entry', () => {
  const auditAdmin = 'audit-admin-cypress@example.com'
  const jurisdictionAdmin = 'wtarkin@empire.gov'
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0

  beforeEach(() => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin(auditAdmin)
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_POLLING"]').check({ force: true })
    cy.get('input[value="BRAVO"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.viewport(1000, 2000)
    cy.contains('Audit Setup')
  })

  it('success & failure cases', () => {
    cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'sample_jurisdiction_filesheet.csv',
            mimeType: 'csv',
          })
      }
    )
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Upload successfully completed')

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
    cy.get('input[name=randomSeed]').type('543210')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByText(`Jurisdictions - TestAudit${id}`)
      .siblings('button')
      .click()
    cy.fixture('CSVs/manifest/ballot_polling_manifest.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_polling_manifest.csv',
            mimeType: 'csv',
          })
      }
    )
    cy.findByText('Upload File').click()
    cy.contains('Upload successfully completed')
    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)

    // add custom sample size to be same as total ballots cast
    cy.findByText('Enter your own sample size (not recommended)').click()
    cy.findByRole('spinbutton').type('400').blur()

    cy.findByRole('button', { name: 'Launch Audit' })
      .should('be.enabled')
      .click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByRole('heading', { name: 'Audit Progress' })
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByText(`Jurisdictions - TestAudit${id}`)
      .siblings('button')
      .click()
    cy.contains('Number of Audit Boards')
    cy.findByText('Save & Next').click()

    // renders properly
    cy.contains('No batches added. Add your first batch below.')

    // adding batch
    cy.findByRole('button', { name: /Add batch/ }).click()
    cy.findByLabelText('Batch Name').type('Batch 1')
    cy.findByLabelText('Batch Type').select('Other')
    cy.findByLabelText('A').type('200')
    cy.findByLabelText('B').type('50')
    cy.findByRole('button', {name: 'Save Batch'}).click()
    cy.contains('Batch 1')

    cy.findByRole('button', { name: /Add batch/ }).click()
    cy.findByLabelText('Batch Name').type('Batch 2')
    cy.findByLabelText('Batch Type').select('Provisional')
    cy.findByLabelText('A').type('100')
    cy.findByLabelText('B').type('50')
    cy.findByRole('button', {name: 'Save Batch'}).click()
    cy.contains('Batch 2')

    // shouldn't allow same batch name to be used
    cy.findByRole('button', { name: /Add batch/ }).click()
    cy.findByLabelText('Batch Name').type('Batch 1')
    cy.findByLabelText('Batch Type').select('Other')
    cy.findByLabelText('A').type('300')
    cy.findByLabelText('B').type('100')
    cy.findByRole('button', {name: 'Save Batch'}).click()
    cy.get('.Toastify')
    .find('div')
    .find('div')
    .contains('Batch names must be unique')
    .invoke('text')
    .then(text =>
      expect(text).to.equal('Batch names must be unique')
    )
    cy.get('.Toastify')
      .find('div')
      .should('not.have.class', 'Toastify__bounce-exit--top-right')
      .get('.Toastify__close-button')
      .click()
    cy.findByRole('button', {name: 'Cancel'}).click()

    // editing batch
    cy.findByText('Batch 1').closest('tr').findByRole('button', /Edit/).click()
    cy.findByLabelText('Batch Type').select('Election Day')
    cy.findByRole('button', {name: 'Save Batch'}).click()
    cy.findAllByText('Batch 1').closest('tr').contains('Election Day')

    // deleting batch
    cy.findByText('Batch 2').closest('tr').findByRole('button', /Edit/).click()
    cy.findByRole('button', {name: 'Remove Batch'}).click()
    cy.findByText('Batch 2').should('not.exist')

    // adding batch again
    cy.findByRole('button', { name: /Add batch/ }).click()
    cy.findByLabelText('Batch Name').type('Batch 2')
    cy.findByLabelText('Batch Type').select('Provisional')
    cy.findByLabelText('A').type('100')
    cy.findByLabelText('B').type('50')
    cy.findByRole('button', {name: 'Save Batch'}).click()
    cy.contains('Batch 2')

    //verify total
    cy.findAllByText('Total').closest('tr').last().contains('400')

    // finalize results
    cy.findByRole('button', {name: 'Finalize Results'}).click()
    cy.contains('Are you sure you want to finalize your results?')
    cy.findAllByText('Finalize Results').spread((firstButton, secondButton) => {
        secondButton.click()
    })
    cy.findByRole('button', {name: 'Finalize Results'}).should('be.disabled')

    // unfinalize results
    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Death Star').closest('tr').findByText('Complete').click({force: true})
    cy.findByRole('button', {name: 'Unfinalize Results'}).click()
    cy.findByText('Death Star').closest('tr').contains('In progress')
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByText(`Jurisdictions - TestAudit${id}`)
      .siblings('button')
      .click()

    // finalize results again
    cy.findByRole('button', {name: 'Finalize Results'}).click()
    cy.contains('Are you sure you want to finalize your results?')
    cy.findAllByText('Finalize Results').spread((firstButton, secondButton) => {
        secondButton.click()
    })
    cy.findByRole('button', {name: 'Finalize Results'}).should('be.disabled')
  })
})