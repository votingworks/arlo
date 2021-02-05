import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Ballot Polling', () => {
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0
  let board_credentials_url = ''

  beforeEach(() => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_POLLING"]').check({ force: true })
    cy.get('input[value="BRAVO"]').check({ force: true })
    cy.findByText('Create Audit').click()
    cy.contains('Audit Setup')
  })


  it('offline audit', () => {
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
    cy.wait(100)
    cy.logout()
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.fixture('CSVs/manifest/ballot_polling_manifest.csv').then(fileContent => {
        cy.get('input[type="file"]').first().attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_polling_manifest.csv',
            mimeType: 'csv'
        })
    })
    cy.findByText('Upload File').click()
    cy.contains("Upload successfully completed")
    cy.logout()
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByText('Launch Audit').click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.get('tbody').children('tr').its('length').should('be.gt', 0)
  })

  it('online audit', () => {
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
    cy.get("input[value=online]").click({ force: true })
    cy.findByRole('combobox', {name: /Choose your state from the options below/}).select('AL')
    cy.findByLabelText('Enter the name of the election you are auditing.').type('Test Election')
    cy.findByRole('combobox', {name: /Set the risk limit for the audit/}).select('10')
    cy.findByLabelText('Enter the random characters to seed the pseudo-random number generator.').type('543210')
    cy.findByText('Save & Next').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.wait(100)
    cy.logout()
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.fixture('CSVs/manifest/ballot_polling_manifest.csv').then(fileContent => {
        cy.get('input[type="file"]').first().attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_polling_manifest.csv',
            mimeType: 'csv'
        })
    })
    cy.findByText('Upload File').click()
    cy.contains("Upload successfully completed")
    cy.logout()
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.findByText('Launch Audit').click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.get('tbody').children('tr').its('length').should('be.gt', 0)
    cy.wait(1000)
    cy.logout()
    cy.wait(1000)
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
    cy.contains('Number of Audit Boards')
    cy.findByText('Save & Next').click()
    cy.findByText('Download Audit Board Credentials').click()
    cy.logout()
    cy.wait(1000)
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
      cy.findAllByText('Audit Board Member: Board Member 1').siblings('input').type('Board Member 1')
      cy.findAllByText('Audit Board Member: Board Member 2').siblings('input').type('Board Member 2')
      cy.findByText('Sign Off').should('not.be.disabled').click()
      cy.contains(/Auditing Complete/)
    })
  })
})