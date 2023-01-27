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
    cy.contains('Audit Setup')

    cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'sample_jurisdiction_filesheet.csv',
            mimeType: 'text/csv',
          })
      }
    )
    cy.findByText('Upload File').click()
    cy.contains('Uploaded')

    cy.get('button[type="submit"]')
      .should('not.have.class', 'bp3-disabled')
      .click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.get('input[name="contests[0].name"]').type('Contest')
    cy.findByLabelText('Name of Candidate/Choice 1').type('Vader')
    cy.findByLabelText('Votes for Candidate/Choice 1').type('9400')
    cy.findByLabelText('Name of Candidate/Choice 2').type('Palpatine')
    cy.findByLabelText('Votes for Candidate/Choice 2').type('1240')
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

    cy.findAllByText('Upload File').should('have.length', 2)
    cy.fixture('CSVs/manifest/batch_comparison_manifest.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'batch_comparison_manifest.csv',
            mimeType: 'text/csv',
          })
      }
    )
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Uploaded')

    cy.fixture(
      'CSVs/candidate-total-batch/sample_candidate_totals_by_batch.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .last()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_candidate_totals_by_batch.csv',
          mimeType: 'text/csv',
        })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Uploaded/).should('have.length', 2)
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

    cy.findByRole('heading', { name: 'Prepare Batches' })
    cy.findByRole('button', { name: /Continue/ }).click()
    cy.findByRole('heading', { name: 'Set Up Tally Entry Accounts' })
    cy.findByRole('button', { name: 'Set Up Tally Entry Accounts' }).click()

    // Start tally entry login
    cy.findByRole('textbox')
      .invoke('val')
      .then(loginLink => {
        cy.visit(loginLink)
        // Since tally entry users can't log in again once they log out, we have
        // to save their session cookie so that we can restore it later (after
        // switching back to the jurisdiction admin account to confirm the login
        // code).
        cy.getCookie('session').then(tallyEntryCookie => {
          cy.findByRole('heading', { name: 'Tally Entry Login' })
          cy.findAllByLabelText('Name')
            .eq(0)
            .type('John Snow')
          cy.findAllByLabelText('Name')
            .eq(1)
            .type('Frodo Baggins')
          cy.findByRole('button', { name: 'Log In' }).click()

          cy.findByRole('heading', { name: 'Login Code' })
            .next()
            .invoke('text')
   	    .then(loginCode => {
              // this will cause a new session to be allocated, so it's resilient to any type of session management, client or server.
              // importantly it won't invalidate the previous session, which is important since we want to go back to it later.
              cy.clearCookie('session')
              cy.visit('/')

              // Switch back to jurisdiction admin account and confirm the login code
              cy.loginJurisdictionAdmin(jurisdictionAdmin)
              cy.findByRole('heading', {
                name: 'Set Up Tally Entry Accounts',
              }).click()
              cy.findByRole('button', { name: /Enter Login Code/ }).click()
              cy.findByLabelText('Enter the login code shown on their screen:')
                .findAllByRole('textbox')
                .then(digitInputs => {
                  loginCode.split('').forEach((digit, index) => {
                    cy.wrap(digitInputs[index]).type(digit)
                  })
                })
              cy.findByRole('button', { name: 'Confirm' }).click()
              cy.logout(jurisdictionAdmin)

              // Switch back to tally entry user, who should now be logged in
              cy.setCookie('session', tallyEntryCookie.value, tallyEntryCookie)
              cy.visit('/tally-entry')
              cy.findByRole('heading', { name: 'Enter Tallies' })
            })
        })
      })

    const auditBatch = (batchName, { vader, palpatine }) => {
      cy.findByRole('button', { name: batchName }).click()
      cy.findByRole('button', { name: /Edit Tallies/ }).click()
      cy.findAllByRole('spinbutton')
        .eq(0)
        .type(vader)
      cy.findAllByRole('spinbutton')
        .eq(1)
        .type(palpatine)
      cy.findByRole('button', { name: /Save Tallies/ })
        .click()
        // Wait for save to complete
        .should('not.exist')
    }

    auditBatch('Batch 3', { vader: 600, palpatine: 400 })
    auditBatch('Batch 5', { vader: 3000, palpatine: 0 })
    cy.logout()

    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByRole('heading', { name: 'Enter Tallies', current: 'step' })
    auditBatch('Batch 10', { vader: 3000, palpatine: 0 })
    cy.findByRole('button', { name: /Finalize Tallies/ }).click()
    cy.findByRole('button', { name: /Confirm/ }).click()
    cy.findByText('Tallies finalized')

    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.contains('Congratulations - the audit is complete!')
  })
})
