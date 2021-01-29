import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Audit Boards', () => {
  const uuid = () => Cypress._.random(0, 1e6)
  const id = 0

  beforeEach(() => {
    id = uuid()
    cy.visit('/')
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.get('input[name=auditName]').type(`TestAudit${id}`)
    cy.get('input[value="BALLOT_COMPARISON"]').check({ force: true })
    cy.findByText("Create Audit").click()
    cy.contains("Audit Setup")
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
    cy.wait(3000)
    cy.findByText('Next').click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.get('input[type="checkbox"]').first().check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Opportunistic Contests').should('have.length', 2)
    cy.findByText('Save & Next').click()
    cy.get('#state').select('AL')
    cy.get('input[name=electionName]').type(`Test Election`)
    cy.get('#risk-limit').select('10')
    cy.get('input[name=randomSeed]').type("543210")
    cy.findByText('Save & Next').click()
    cy.wait(1000)
    cy.logout()
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
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
    cy.loginAuditAdmin('audit-admin-cypress@example.com')
    cy.findByText(`TestAudit${id}`).click()
    cy.findByText('Review & Launch').click()
    cy.findByText('Launch Audit').click()
    cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.logout()
    cy.wait(1000)
    cy.contains('Participating in an audit in your local jurisdiction?')

  })
  const board_credentials_url = ''

  it.skip('Audit Board Completion', () => {
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

  it('Audit Board - Return to audit overview', () => {
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
      cy.findByText('Start Auditing').click()
      cy.findByText('Return to audit overview').click()
      cy.contains(/Ballot Cards to Audit/)
    })
  })

  it.skip('Audit Board - Submit empty Ballot Error', () => {
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
      cy.findByText('Start Auditing').click()
      cy.findByText('Review').click() 
      cy.findByText('Submit & Next Ballot').click() 
      cy.get('.Toastify').find('div').find('div').contains('Must include an interpretation for each contest.').invoke('text')
      .then((text) => {
          const toastText = text
          expect(toastText).to.equal('Must include an interpretation for each contest.')
      }) 
    })
  })
})