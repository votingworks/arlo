describe('create audit page', () => {
  it('should have a button', () => {
    browser.url('/')
    const title = browser.getTitle()
    expect(title).toBe('Arlo (by VotingWorks)')

    const createBtn = $('.bp3-button-text=Create a New Audit')
    expect(createBtn.getText()).toBe('Create a New Audit')
  })

  it('should create a new audit', () => {
    browser.url('/')
    const createBtn = $('.bp3-button-text=Create a New Audit')
    createBtn.click()
    const electionFld = $('#audit-name')
    electionFld.waitForExist(5000)
  })

  it('should submit form one', () => {
    browser.url('/')
    $('.bp3-button-text=Create a New Audit').click()
    const electionFld = $('#audit-name')
    electionFld.waitForExist(5000)

    electionFld.addValue('Election')
    $('input[name="contests[0].name"]').addValue('Contest')
    $('input[name="contests[0].choices[0].name"]').addValue('Choice One')
    $('input[name="contests[0].choices[0].numVotes"]').addValue('10')
    $('input[name="contests[0].choices[1].name"]').addValue('Choice Two')
    $('input[name="contests[0].choices[1].numVotes"]').addValue('20')
    $('input[name="contests[0].totalBallotsCast"]').addValue('30')
    $('#random-seed').addValue('1234567890')
    $('.bp3-button.bp3-intent-primary').click()

    $('.bp3-heading=Select Ballots to Audit').waitForExist(10000)
  })
})
