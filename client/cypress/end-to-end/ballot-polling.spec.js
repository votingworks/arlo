import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Ballot Polling', () => {
  const auditAdmin = 'audit-admin-cypress@example.com'
  const jurisdictionAdmin = 'wtarkin@empire.gov'
  const uuid = () => Cypress._.random(0, 1e6)
  let id = 0
  let board_credentials_url = ''

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

  it('offline audit', () => {
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
    cy.contains('Round 1 Data Entry')
    cy.get('.bp3-card')
      .eq('0')
      .findByLabelText('Votes for A:')
      .type('15')
    cy.get('.bp3-card')
      .eq('0')
      .findByLabelText('Votes for B:')
      .type('5')
    cy.findByText('Submit Data for Round 1').click()
    cy.contains('Already Submitted Data for Round 1')
    cy.logout(jurisdictionAdmin)
    cy.loginAuditAdmin(auditAdmin)
    cy.findByText(`TestAudit${id}`).click()
    cy.contains('Congratulations - the audit is complete!')

    // Delete the audit
    cy.findByRole('button', { name: /View Audits/ }).click()
    cy.findByRole('button', { name: 'Delete Audit' }).click()
    cy.findByRole('button', { name: 'Delete' }).click()
    cy.findByText(/You haven't created any audits yet/)
  })

  it('online audit', () => {
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

    cy.get('button[type="submit"]')
      .should('not.have.class', 'bp3-disabled')
      .click()
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
    cy.get('input[value=online]').click({ force: true })
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
    cy.findAllByText('Review & Launch').should('have.length', 2)
    cy.logout(auditAdmin)
    cy.loginJurisdictionAdmin(jurisdictionAdmin)
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
      cy.get('table tbody tr').each(($el, index, list) => {
        // iterate through exactly the number of ballots available to avoid conditions
        if (index == 0) {
          cy.findByText('Audit First Ballot').click()
        }
        cy.get('input[type="checkbox"]')
          .first()
          .click({ force: true })
        cy.findByRole('button', { name: 'Submit Selections' }).click()
        cy.findByText('Confirm Selections').click()
        cy.findByText('Change Selections').should('not.exist')
      })
      cy.findByText(/Not Audited/).should('have.length', 1)
      cy.contains('Ballots for Audit Board #1')
      cy.findAllByText('Submit Audited Ballots').eq(1).click({ force: true })
      cy.findAllByText('Audit Board Member: Board Member 1')
        .siblings('input')
        .type('Board Member 1')
      cy.findAllByText('Audit Board Member: Board Member 2')
        .siblings('input')
        .type('Board Member 2')
      cy.findByText('Sign Off')
        .should('not.be.disabled')
        .click()
      cy.contains(/Auditing Complete/)
    })
  })
})
