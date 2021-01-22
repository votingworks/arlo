before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Ballot Comparison Audit Creation', () => {
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0

  beforeEach(() => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_COMPARISON"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.contains('Audit Setup')
  })

  it('sidebar changes stages', () => {
    cy.findAllByText('Participants & Contests').should('have.length', 2)
    cy.findByText('Audit Settings').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
  })

  it('save & next and back buttons change stage', () => {
    cy.findAllByText('Participants & Contests').should('have.length', 2)
    cy.findByText('Audit Settings').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
    cy.get('#state').select('AL')
    cy.get('input[name=electionName]').type(`Test Election`)
    cy.get('#risk-limit').select('10')
    cy.get('input[name=randomSeed]').type('543210')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByText('Back').click()
    cy.findAllByText('Audit Settings').should('have.length', 2)
  })

  it('participating jurisdictions invalid CSV - Jurisdiction column error', () => {
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
      .then((text)=>{
        const toastText = text;
        expect(toastText).to.equal('Missing required CSV field "Jurisdiction"');
    })   
  })

  it('participating jurisdictions invalid CSV - Admin Email column error', () => {
    cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet_admin_email_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_jurisdiction_filesheet_admin_email_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.get('.Toastify').find('div').find('div').contains('Missing required CSV field "Admin Email"').invoke('text')
      .then((text)=>{
        const toastText = text;
        expect(toastText).to.equal('Missing required CSV field "Admin Email"');
    })   
  })

  it('participating jurisdictions invalid CSV - Invalid Email error', () => {
    cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet_email_ID_error.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_jurisdiction_filesheet_email_ID_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains("Expected an email address in column Admin Email")   
  })

  it('participating jurisdictions proper CSV', () => {
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
  })

  it('Standardized Contests invalid CSV - Contest name column error', () => {
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

    cy.fixture('CSVs/contest/sample_standardized_contests_contest_name_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests_contest_name_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.contains("Missing required column: Contest Name.")      
  })

  it('Standardized Contests invalid CSV - Jurisdiction column error', () => {
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

    cy.fixture('CSVs/contest/sample_standardized_contests_jurisdiction_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests_jurisdiction_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.contains("Missing required column: Jurisdictions.")
  })

  it('Standardized Contests invalid CSV - Non-participating Jurisdiction error', () => {
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

    cy.fixture('CSVs/contest/sample_standardized_contests_non_participating_jurisdiction_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests_non_participating_jurisdiction_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.contains("Invalid jurisdictions for contest") 
  })

  it('Standardized Contests proper CSV', () => {
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

    cy.fixture('CSVs/contest/sample_standardized_contests.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
  })

  it('No Target Contest Selected Error', () => {
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

    cy.fixture('CSVs/contest/sample_standardized_contests.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'sample_standardized_contests.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.wait(1000) // gets stuck in an infinite loop without a 100ms wait here
    cy.findByText('Next').click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.findByText('Save & Next').click()
    cy.get('.Toastify').find('div').find('div').contains('Must have at least one targeted contest').invoke('text')
    .then((text) => {
        const toastText = text
        expect(toastText).to.equal('Must have at least one targeted contest')
     }) 
  })

  it('Participating Jurisdictions - File not uploaded error', () => {
    cy.wait(1000) // without this Cypress fails because the element becomes detached from DOM
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains("You must upload a file") 
  })

  it('Standardized Contests - File not uploaded error', () => {
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

    cy.findAllByText('Upload File').click()
    cy.contains("You must upload a file")   
  })

  it('Audit Progress opens', () => {
      var rowText = ''
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

      cy.fixture('CSVs/contest/sample_standardized_contests.csv').then(fileContent => {
          cy.get('input[type="file"]').last().attachFile({
              fileContent: fileContent.toString(),
              fileName: 'sample_standardized_contests.csv',
              mimeType: 'csv'
          })
      })
      cy.findAllByText('Upload File').click()
      cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
      cy.wait(1000)
      cy.findByText('Next').click()
      cy.findByText("Audit Progress").click()
      cy.get('tbody').children('tr').its('length').should('be.gt', 0)
      cy.get('tbody').children('tr').eq(2).children('td').first().then(function($tdElem) {
          rowText = $tdElem.text()
          cy.get('input[type="text"]').type(rowText)
          cy.get('tbody').children('tr').first().children('td').first().contains(rowText)
      })
  })

  it('View Audit button works', () => {
      cy.findAllByText('Participants & Contests').should('have.length', 2)
      cy.findByText('View Audits').click()
      cy.contains("Audits - Cypress Test Org")
  })

  it('Creating an Audit', () => {
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

    cy.fixture('CSVs/contest/ballot_comparison_contests.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_contests.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.wait(2000) // gets stuck in an infinite loop without a 100ms wait here
    cy.findByText('Next').click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.get('input[type="checkbox"]').first().check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Opportunistic Contests').should('have.length', 2)
    cy.findByText('Save & Next').click()
    cy.get('#state').select('AL')
    cy.get('input[name=electionName]').type('Test Election')
    cy.get('#risk-limit').select('10')
    cy.get('input[name=randomSeed]').type('543210')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.wait(100)
    cy.logout()
    cy.wait(2000)
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.wait(1000)
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

    cy.fixture('CSVs/cvr/ballot_comparison_cvr.csv').then(fileContent => {
        cy.get('input[type="file"]').last().attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_cvr.csv',
            mimeType: 'csv'
        })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.wait(1000)
    cy.logout()
    cy.wait(2000)
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByText('Launch Audit').click()
    cy.wait(1000)
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.get('tbody').children('tr').its('length').should('be.gt', 0)
  })
})
