import 'cypress-file-upload'

before(() => cy.exec('./cypress/seed-test-db.sh'))

describe('Audit creation, filling in standard ballot comparison values', () => {
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
        cy.get('input[value="BALLOT_COMPARISON"]').check({ force: true })
        cy.findByText("Create Audit").click()
        cy.contains("Audit Setup")
    })

    it('Participating Jurisdictions - File errors', () => {
        cy.findAllByText('Upload File').spread((firstButton, secondButton) => {
            firstButton.click()
        })
        cy.contains("You must upload a file") 
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
        cy.get('.Toastify').get('.Toastify__toast-body').should('be.visible').contains('Missing required CSV field "Jurisdiction"').invoke('text')
        .then((text)=>{
            const toastText = text;
            expect(toastText).to.equal('Missing required CSV field "Jurisdiction"');
        })
        cy.get('.Toastify').find('div').should('not.have.class', 'Toastify__bounce-exit--top-right').get('.Toastify__close-button').click()

        cy.fixture('CSVs/jurisdiction/sample_jurisdiction_filesheet_admin_email_col_error.csv').then(fileContent => {
            cy.get('input[type="file"]').first().attachFile({
                fileContent: fileContent.toString(),
                fileName: 'sample_jurisdiction_filesheet_admin_email_col_error.csv',
                mimeType: 'csv'
            })
        })
        cy.findAllByText('Upload File',{timeout: 6000}).spread((firstButton, secondButton) => {
            firstButton.click()
        })
        cy.get('.Toastify').get('.Toastify__toast-body').should('be.visible').contains('Missing required CSV field "Admin Email"').invoke('text')
        .then((text)=>{
            const toastText = text;
            expect(toastText).to.equal('Missing required CSV field "Admin Email"');
        })
        cy.get('.Toastify').find('div').should('not.have.class', 'Toastify__bounce-exit--top-right').get('.Toastify__close-button').click()

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


    it('Standardized Contests - File errors', () => {
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

        cy.fixture('CSVs/contest/sample_standardized_contests_contest_name_col_error.csv').then(fileContent => {
            cy.get('input[type="file"]').last().attachFile({
                fileContent: fileContent.toString(),
                fileName: 'sample_standardized_contests_contest_name_col_error.csv',
                mimeType: 'csv'
            })
        })
        cy.findAllByText('Upload File').click()
        cy.contains("Missing required column: Contest Name.") 
        
        cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
            secondButton.click()
        })
        
        cy.fixture('CSVs/contest/sample_standardized_contests_jurisdiction_col_error.csv').then(fileContent => {
            cy.get('input[type="file"]').last().attachFile({
                fileContent: fileContent.toString(),
                fileName: 'sample_standardized_contests_jurisdiction_col_error.csv',
                mimeType: 'csv'
            })
        })
        cy.findAllByText('Upload File').click()
        cy.contains("Missing required column: Jurisdictions.")

        cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
            secondButton.click()
        })

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
        cy.findByText('Save & Next').click()
        cy.get('.Toastify').get('.Toastify__toast-body').should('be.visible').contains('Must have at least one targeted contest').invoke('text')
        .then((text)=>{
            const toastText = text;
            expect(toastText).to.equal('Must have at least one targeted contest');
         })
    })

    it('Ballot Manifest - File Errors', () => {
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
        cy.get('button[type="submit"]').should('not.have.class', 'bp3-disabled').click()
        cy.findAllByText('Target Contests').should('have.length', 2)
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
        cy.contains('Participating in an audit in your local jurisdiction?')
        cy.loginJurisdictionAdmin(jurisdictionAdmin)
        cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
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
        cy.findByText('Replace File').click()
        cy.findAllByText('Upload File').should('have.length',2)
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

    it('Cast Vote Records - File Errors', () => {
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
        cy.get('button[type="submit"]').should('not.have.class', 'bp3-disabled').click()
        cy.findAllByText('Target Contests').should('have.length', 2)
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
        cy.contains('Participating in an audit in your local jurisdiction?')
        cy.loginJurisdictionAdmin(jurisdictionAdmin)
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
    
        cy.fixture('CSVs/cvr/ballot_comparison_cvr_col_error.csv').then(fileContent => {
        cy.get('input[type="file"]').last().attachFile({
            fileContent: fileContent.toString(),
            fileName: 'ballot_comparison_cvr_col_error.csv',
            mimeType: 'csv'
        })
        })
        cy.findAllByText('Upload File').last().click()
        cy.contains(/Invalid contest name/)
        cy.findAllByText('Replace File').spread((firstButton, secondButton) => {
            secondButton.click()
          })
        cy.findByText('Upload File')
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

    it('Audit Board - Submit empty Ballot Error', () => {
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
        cy.get('button[type="submit"]').should('not.have.class', 'bp3-disabled').click()
        cy.findAllByText('Target Contests').should('have.length', 2)
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
        cy.contains('Participating in an audit in your local jurisdiction?')
        cy.loginJurisdictionAdmin(jurisdictionAdmin)
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
        cy.logout(jurisdictionAdmin)
        cy.loginAuditAdmin(auditAdmin)
        cy.findByText(`TestAudit${id}`).click()
        cy.findByText('Review & Launch').click()
        cy.findByText('Launch Audit').click()
        cy.findAllByText('Launch Audit').spread((firstButton, secondButton) => {
        secondButton.click()
        })
        cy.contains('Drawing a random sample of ballots...')
        cy.get('tbody').children('tr').its('length').should('be.gt', 0)
        cy.logout(auditAdmin)
        cy.contains('Participating in an audit in your local jurisdiction?')
        cy.loginJurisdictionAdmin(jurisdictionAdmin)
        cy.findByText(`Jurisdictions - TestAudit${id}`).siblings('button').click()
        cy.contains('Number of Audit Boards')
        cy.findByText('Save & Next').click()
        cy.findByText('Download Audit Board Credentials').click()
        cy.logout(jurisdictionAdmin)
        cy.task('getPdfContent', `cypress/downloads/Audit Board Credentials\ -\ Death Star\ -\ TestAudit${id}.pdf`).then((content) => {
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
        cy.get('.Toastify').get('.Toastify__toast-body').should('be.visible').contains('Must include an interpretation for each contest.').invoke('text')
            .then((text) => {
                const toastText = text
                expect(toastText).to.equal('Must include an interpretation for each contest.')
            }) 
        })
    })
})