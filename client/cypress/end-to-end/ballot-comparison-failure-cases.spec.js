before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Ballot Comparison Failure Cases', () => {
  const auditAdmin = 'audit-admin-cypress@example.com'
  const jurisdictionAdmin = 'wtarkin@empire.gov'
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0
  let board_credentials_url = ''

  it('CSV and input errors', () => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin(auditAdmin)
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_COMPARISON"]').check({ force: true })
    cy.findByText("Create Audit").click()
    cy.contains("Audit Setup")
    // attempt uploading a jurisdiction filesheet without selecting one
    // cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
    //   firstButton.click()
    // })
    // cy.contains("You must upload a file")

    // upload invalid jurisdiction filesheet
    cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet_jurisdiction_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_jurisdiction_filesheet_jurisdiction_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.get('.Toastify').find('div').find('div').contains('Missing required CSV field "Jurisdiction"').invoke('text')
    .then(text => {
      const toastText = text;
      expect(toastText).to.equal('Missing required CSV field "Jurisdiction"');
    })

    // upload valid jurisdiction filesheet
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

    // attempt uploading a standardized contests file without selecting one
    cy.findAllByText('Upload File').click()
    cy.contains("You must upload a file")

    // upload invalid standardized contests file
    cy.fixture('CSVs/contest/sample_standardized_contests_contest_name_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests_contest_name_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.contains("Missing required column: Contest Name.")

    // upload valid standardized contests file
    cy.fixture('CSVs/contest/ballot_comparison_contests.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_contests.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.get('button[type="submit"]').should('not.have.class', 'bp3-disabled').click()
    cy.findAllByText('Target Contests').should('have.length', 2)

    // neglect to select a targeted contest
    cy.findByText('Save & Next').click()
    cy.get('.Toastify').find('div').find('div').contains('Must have at least one targeted contest').invoke('text')
    .then(text => {
      const toastText = text;
      expect(toastText).to.equal('Must have at least one targeted contest');
    })

    // select targeted contest
    cy.get('input[type="checkbox"]').first().check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Opportunistic Contests').should('have.length', 2)
    cy.findByText('Save & Next').click()
    cy.findByRole('combobox', {name: /Choose your state from the options below/}).select('AL')
    cy.findByLabelText('Enter the name of the election you are auditing.').type('Test Election')
    cy.findByRole('combobox', {name: /Set the risk limit for the audit/}).select('10')
    cy.findByLabelText('Enter the random characters to seed the pseudo-random number generator.').type('543210')
    cy.findByText('Save & Next').click()
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()

    // upload invalid manifest
    cy.fixture('CSVs/manifest/ballot_comparison_manifest_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_manifest_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains("Missing required column: Number of Ballots.")

    // upload valid manifest
    cy.findByText('Replace File').click()
    cy.findAllByText('Upload File').should('have.length',2)
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.fixture('CSVs/manifest/ballot_comparison_manifest.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_manifest.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains("Upload successfully completed")

    // upload invalid cvr
    cy.fixture('CSVs/cvr/ballot_comparison_cvr_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').last().click()
    cy.contains(/Invalid contest name/)
    
    // now upload valid cvr
    cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByText('Upload File')
    cy.fixture('CSVs/cvr/ballot_comparison_cvr.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)

    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findByText('Launch Audit').click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    // cy.contains('Audit Progress')
    cy.contains('Drawing a random sample of ballots...')
    cy.get('tbody').children('tr').its('length').should('be.gt', 0)
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.contains('Number of Audit Boards')
    cy.findByText('Save & Next').click()
    cy.findByText('Download Audit Board Credentials').click()
    cy.logout(jurisdictionAdmin)
    cy.task('getPdfContent', `cypress/fixtures/PDFs/Audit Board Credentials\ -\ Death Star\ -\ TestAudit${id}.pdf`).then((content) => {
    function urlify(text) {
      var urlRegex = /(((https?:\/\/)|(www\.))[^\s]+)/g;
      return text.match(urlRegex, function(url) {
      return url
      }) 
    }
    board_credentials_url = urlify(content.text);
    cy.visit(board_credentials_url[0])
    cy.findAllByText('Audit Board Member').eq(0).siblings('input').type('Board Member 1')
    cy.findAllByText('Audit Board Member').eq(1).siblings('input').type('Board Member 2')
    cy.findByText('Next').click()
    cy.contains(/Ballot Cards to Audit/)
    cy.findByText('Start Auditing').click()

    // submit empty ballot review
    cy.findByText('Review').click() 
    cy.findByText('Submit & Next Ballot').click() 
    cy.get('.Toastify').find('div').find('div').contains('Must include an interpretation for each contest.').invoke('text')
      .then((text) => {
        const toastText = text
        expect(toastText).to.equal('Must include an interpretation for each contest.')
      }) 
    })

    // audit all ballots
    cy.findByText('Return to audit overview')
    cy.contains(/Ballot Cards to Audit/)
    cy.get('table tbody tr').each(($el, index, list) => {
      // iterate through exactly the number of ballots available to avoid conditions
      if(index == 0) {
        cy.findByText('Start Auditing').click()
      }
      cy.get('input[type="checkbox"]').first().click({force: true})
      cy.findByText('Review').click() 
      cy.findByText('Submit & Next Ballot').click() 
    })
    cy.wait(100)
    cy.findByText('Auditing Complete - Submit Results').click()

    // input wrong audit board member name in signoff
    cy.findAllByText('Audit Board Member: Board Member 1').siblings('input').type('Member 1')
    cy.findAllByText('Audit Board Member: Board Member 2').siblings('input').type('Board Member 2')
    cy.findByText('Sign Off').should('not.be.disabled').click()
    cy.get('.Toastify').get('.Toastify__toast-body').should('be.visible').contains('Audit board member name did not match: Member 1').invoke('text')
    .then(text => {
      const toastText = text
      expect(toastText).to.equal('Audit board member name did not match: Member 1')
    })

    // correct the audit board member name and signoff
    cy.findAllByText('Audit Board Member: Board Member 1').siblings('input').type('Board Member 1')
    cy.findByText('Sign Off').should('not.be.disabled').click()
    cy.contains(/Auditing Complete/)
  })
})