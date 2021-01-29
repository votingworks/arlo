import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Pre-launch file uploads', () => {
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
    cy.wait(3000) // gets stuck in an infinite loop without a wait here
    cy.findByText('Next').click()
    cy.findAllByText('Target Contests').should('have.length', 2)
    cy.get('input[type="checkbox"]').first().check({ force: true })
    cy.findByText('Save & Next').click()
    cy.findAllByText('Opportunistic Contests').should('have.length', 2)
    cy.logout()
    cy.contains('Participating in an audit in your local jurisdiction?')
    cy.loginJurisdictionAdmin('wtarkin@empire.gov')
    cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
  })

  it('Ballot Manifest - Column Error', () => {
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
  })


  it('Ballot Manifest - Value Error', () => {
    cy.fixture('CSVs/manifest/ballot_comparison_manifest_value_error.csv').then(fileContent => {
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_manifest_value_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
      firstButton.click()
    })
    cy.contains(/Expected a number in column Number of Ballots/)
  })

  it('Ballot Manifest - Replace File', () => {
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
    cy.findByText('Replace File').click()
    cy.findAllByText('Upload File').should('have.length',2)
  })

  it('Ballot Manifest - Delete File', () => {
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
    cy.findByText('Delete File').click()
    cy.findAllByText('Upload File').should('have.length',2)
  })

  it('Ballot Manifest - Success', () => {
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
  })

  it('Cast Vote Records - Column Error', () => {
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

    cy.fixture('CSVs/cvr/ballot_comparison_cvr_col_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr_col_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').last().click()
    cy.contains(/Invalid contest name/)
  })

  it('Cast Vote Records - Value Error', () => {
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

    cy.fixture('CSVs/cvr/ballot_comparison_cvr_value_error.csv').then(fileContent => {
      cy.get('input[type="file"]').last().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr_value_error.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').last().click()
    cy.contains(/Invalid contest name/)
  })

  it('Cast Vote Records - Replace File', () => {
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
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByText('Upload File')
  })

  it('Cast Vote Records - Delete File', () => {
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
      cy.get('input[type="file"]').first().attachFile({
        fileContent: fileContent.toString(),
        fileName: 'ballot_comparison_cvr.csv',
        mimeType: 'csv'
      })
    })
    cy.findAllByText('Upload File').click()
    cy.findAllByText(/Upload successfully completed/).should('have.length', 2)
    cy.findAllByText('Delete File').spread((firstButton, secondButton) => {
      secondButton.click()
    })
    cy.findByText('Upload File')
  })

  it('Cast Vote Records - Success', () => {
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
  })

  afterEach(() => {
    cy.logout()
  })
})