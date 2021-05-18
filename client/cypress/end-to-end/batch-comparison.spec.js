import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Batch Comparison', () => {
  const auditAdmin = 'audit-admin-cypress@example.com'
  const jurisdictionAdmin = 'wtarkin@empire.gov'
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0

  it('success & failure cases', () => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin(auditAdmin)
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BATCH_COMPARISON"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.viewport(1000, 2000)
    cy.contains('Audit Setup')

    // upload invalid jurisdiction filesheet
    cy.fixture(
      'CSVs/jurisdiction/sample_jurisdiction_filesheet_jurisdiction_col_error.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .first()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_jurisdiction_filesheet_jurisdiction_col_error.csv',
          mimeType: 'csv',
        })
    })
    cy.findByText('Upload File').click({ force: true })
    cy.findAndCloseToast('Missing required CSV field "Jurisdiction"')

    // upload valid jurisdiction filesheet
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
    cy.findByText('Upload File').click()
    cy.contains('Upload successfully completed')

    cy.get('button[type="submit"]')
      .should('not.have.class', 'bp3-disabled')
      .click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.get('input[name="contests[0].name"]').type('Contest')
    cy.findByLabelText('Name of Candidate/Choice 1').type('Vader')
    cy.findByLabelText('Votes for Candidate/Choice 1').type('2700')
    cy.findByLabelText('Name of Candidate/Choice 2').type('Palpatine')
    cy.findByLabelText('Votes for Candidate/Choice 2').type('2620')
    cy.findByText('Select Jurisdictions').click()
    cy.findByLabelText('Death Star').check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
    cy.get('#state').select('AL')
    cy.get('input[name=electionName]').type(`Test Election`)
    cy.get('#risk-limit').select('10')
    cy.get('input[name=randomSeed]').type('54321')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)

    // upload invalid manifest
    cy.fixture('CSVs/manifest/batch_comparison_manifest_col_error.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'batch_comparison_manifest_col_error.csv',
            mimeType: 'csv',
          })
      }
    )
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Missing required column: Number of Ballots.')

    // upload valid manifest
    cy.findByText('Replace File').click()
    cy.findAllByText('Upload File').should('have.length', 2)
    cy.fixture('CSVs/manifest/batch_comparison_manifest.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'batch_comparison_manifest.csv',
            mimeType: 'csv',
          })
      }
    )
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Upload successfully completed')

    // upload invalid batch tallies
    cy.fixture(
      'CSVs/candidate-total-batch/sample_candidate_totals_by_batch_col_error.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .last()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_candidate_totals_by_batch_col_error.csv',
          mimeType: 'csv',
        })
    })
    cy.findAllByText('Upload File')
      .last()
      .click()
    cy.contains(/Missing required column: Palpatine/)

    // now upload valid batch tallies
    cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.fixture(
      'CSVs/candidate-total-batch/sample_candidate_totals_by_batch.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .last()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_candidate_totals_by_batch.csv',
          mimeType: 'csv',
        })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByRole('button', { name: 'Launch Audit' })
      .should('be.enabled')
      .click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByRole('heading', { name: 'Audit Progress' })
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.contains('Number of Audit Boards')
    cy.findByText('Save & Next').click()
    cy.get('.bp3-card')
      .eq('0')
      .findByLabelText('Votes for Vader:')
      .type('600')
    cy.get('.bp3-card')
      .eq('0')
      .findByLabelText('Votes for Palpatine:')
      .type('400')
    cy.get('.bp3-card')
      .eq('1')
      .findByLabelText('Votes for Vader:')
      .type('1000')
    cy.get('.bp3-card')
      .eq('1')
      .findByLabelText('Votes for Palpatine:')
      .type('200')
    cy.get('.bp3-card')
      .eq('2')
      .findByLabelText('Votes for Vader:')
      .type('1000')
    cy.get('.bp3-card')
      .eq('2')
      .findByLabelText('Votes for Palpatine:')
      .type('2000')
    cy.findByText('Submit Data for Round 1').click()
    cy.contains('Already Submitted Data for Round 1')
    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.contains('Congratulations - the audit is complete!')
  })
})
