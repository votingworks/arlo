import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Ballot Comparison Test Cases', () => {
  const auditAdmin = 'audit-admin-cypress@example.com'
  const jurisdictionAdmin = 'wtarkin@empire.gov'
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0
  let board_credentials_url = ''

  it('success & failure cases', () => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin(auditAdmin)
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_COMPARISON"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.contains('Audit Setup')
    cy.viewport(1000, 2000)

    // upload invalid jurisdiction filesheet
    cy.fixture(
      'CSVs/jurisdiction/sample_jurisdiction_filesheet_jurisdiction_col_error.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .first()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_jurisdiction_filesheet_jurisdiction_col_error.csv',
          mimeType: 'text/csv',
        })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.findByText('Missing required column: Jurisdiction.')

    // upload valid jurisdiction filesheet
    cy.findByRole('button', { name: 'Replace File' }).click()
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
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Upload successfully completed')

    // upload invalid standardized contests file
    cy.fixture(
      'CSVs/contest/sample_standardized_contests_contest_name_col_error.csv'
    ).then(fileContent => {
      cy.get('input[type="file"]')
        .last()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'sample_standardized_contests_contest_name_col_error.csv',
          mimeType: 'text/csv',
        })
    })
    cy.findAllByText('Upload File').click()
    cy.contains('Missing required column: Contest Name.')

    // upload valid standardized contests file
    cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.fixture('CSVs/contest/ballot_comparison_contests.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .last()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_contests.csv',
            mimeType: 'text/csv',
          })
      }
    )
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.get('button[type="submit"]')
      .should('not.have.class', 'bp3-disabled')
      .click()
    cy.findAllByText('Target Contests').should('have.length', 2)

    // neglect to select a targeted contest
    cy.findByText('Save & Next').click()
    cy.findAndCloseToast('Must have at least one targeted contest')

    cy.findByText('Back').click()

    // select targeted contest
    cy.get('input[type="checkbox"]')
      .first()
      .check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Opportunistic Contests').should('have.length', 2)
    cy.findByText('Save & Next').click()
    cy.findByRole('combobox', {
      name: /Choose your state from the options below/,
    }).select('AL')
    cy.findByLabelText('Enter the name of the election you are auditing.').type(
      'Test Election'
    )
    cy.findByRole('combobox', {
      name: /Set the risk limit for the audit/,
    }).select('10')
    cy.findByLabelText(
      'Enter the random characters to seed the pseudo-random number generator.'
    ).type('543210')
    cy.findByText('Save & Next').click()
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)

    // upload invalid manifest
    cy.fixture('CSVs/manifest/ballot_comparison_manifest_col_error.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_manifest_col_error.csv',
            mimeType: 'text/csv',
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
    cy.fixture('CSVs/manifest/ballot_comparison_manifest.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .first()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_manifest.csv',
            mimeType: 'text/csv',
          })
      }
    )
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains('Upload successfully completed')

    // upload invalid cvr
    cy.fixture('CSVs/cvr/ballot_comparison_cvr_col_error.csv').then(
      fileContent => {
        cy.get('input[type="file"]')
          .last()
          .attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_cvr_col_error.csv',
            mimeType: 'text/csv',
          })
      }
    )
    cy.findAllByText('Upload File')
      .last()
      .click()
    cy.contains(/Invalid contest name/)

    // now upload valid cvr
    cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByText('Upload File')
    cy.fixture('CSVs/cvr/ballot_comparison_cvr.csv').then(fileContent => {
      cy.get('input[type="file"]')
        .last()
        .attachFile({
          fileContent: fileContent.toString(),
          fileName: 'ballot_comparison_cvr.csv',
          mimeType: 'text/csv',
        })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)

    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()

    cy.get('input[type="radio"]')
      .first()
      .click({ force: true })
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
    cy.findByText('Download Audit Board Credentials').click()
    cy.logout(jurisdictionAdmin)
    cy.task(
      'getPdfContent',
      `cypress/downloads/Audit Board Credentials\ -\ Death Star\ -\ TestAudit${id}.pdf`
    ).then(content => {
      function urlify(text) {
        var urlRegex = /(((https?:\/\/)|(www\.))[^\s]+)/g
        return text.match(urlRegex, function(url) {
          return url
        })
      }
      board_credentials_url = urlify(content.text)
      cy.visit(board_credentials_url[0])
      cy.findAllByText('Audit Board Member')
        .eq(0)
        .siblings('input')
        .type('Board Member 1')
      cy.findAllByText('Audit Board Member')
        .eq(1)
        .siblings('input')
        .type('Board Member 2')
      cy.findByText('Next').click()
      cy.contains('Ballots for Audit Board #1')

      // button name when no ballots are audited
      cy.findByText('Audit First Ballot').click()

      // submit empty ballot review
      cy.findByText('Review').click()
      cy.findByText('Submit & Next Ballot').click()
      cy.findAndCloseToast('Must include an interpretation for each contest.')
      cy.get('input[type="checkbox"]')
        .first()
        .click({ force: true })
      cy.findByText('Review').click()
      cy.findByText('Submit & Next Ballot').click()
      cy.findByText(/Auditing ballot 3 of/)
      cy.findByText('Return to audit overview').click()
    })

    cy.contains('Ballots for Audit Board #1')

    // audit all ballots
    cy.get('table tbody tr').each(($el, index, list) => {
      // iterate through exactly the number of ballots available to avoid conditions
      if (index == 0) {
        // button name when some ballots are audited
        cy.findByText('Audit Next Ballot').click()
      }
      cy.get('input[type="checkbox"]')
        .first()
        .click({ force: true })
      cy.findByText('Review').click()
      cy.findByText('Submit & Next Ballot').click()
    })
    cy.contains('Ballots for Audit Board #1')

    // test Re-Audit button
    cy.findAllByText('Re-Audit').first().click()
    cy.get('input[type="checkbox"]')
        .first()
        .click({ force: true })
    cy.findByText('Review').click()
    cy.findByText('Submit & Next Ballot').click()
    cy.findByText('Return to audit overview').click()

    cy.contains('Ballots for Audit Board #1')
    cy.findAllByText('Submit Audited Ballots').spread((firstButton, secondButton) => {
      // assert bottom submit button
      secondButton.click()
    })

    // input wrong audit board member name in signoff
    cy.findAllByText('Audit Board Member: Board Member 1')
      .siblings('input')
      .type('Member 1')
    cy.findAllByText('Audit Board Member: Board Member 2')
      .siblings('input')
      .type('Board Member 2')
    cy.findByText('Sign Off')
      .should('not.be.disabled')
      .click()
    cy.findAndCloseToast('Audit board member name did not match: Member 1')

    // correct the audit board member name and signoff
    cy.findAllByText('Audit Board Member: Board Member 1')
      .siblings('input')
      .clear()
      .type('Board Member 1')
    cy.findByText('Sign Off')
      .should('not.be.disabled')
      .click()
    cy.contains(/Auditing Complete/)
  })
})
