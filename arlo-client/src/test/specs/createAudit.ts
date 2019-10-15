import * as path from 'path'

const filePath = path.join(
  __dirname,
  '../_mocks/Ballot Manifest May 2019 Election - WYANDOTTE.csv'
)

export const start = () => {
  browser.url('/')
  $('.bp3-button-text=Create a New Audit').click()
  $('#audit-name').waitForExist(5000)
}

export const formOne = () => {
  start()
  $('#audit-name').addValue('Election')
  $('input[name="contests[0].name"]').addValue('Contest')
  $('input[name="contests[0].choices[0].name"]').addValue('Choice One')
  $('input[name="contests[0].choices[0].numVotes"]').addValue('792')
  $('input[name="contests[0].choices[1].name"]').addValue('Choice Two')
  $('input[name="contests[0].choices[1].numVotes"]').addValue('1325')
  $('input[name="contests[0].totalBallotsCast"]').addValue('2123')
  $('#random-seed').addValue('1234567890')
  $('.bp3-button.bp3-intent-primary').click()

  $('.bp3-heading=Select Ballots to Audit').waitForExist(10000)
}

export const formTwo = () => {
  formOne()
  $('input[name="manifest"]').setValue(filePath)
  $('.bp3-button-text=Select Ballots To Audit').click()

  $('.bp3-heading=Round 1').waitForExist(10000)
}

export const formThreeNext = () => {
  const roundHeaders = $$('h2*=Round')
  const lastRound = Number(
    roundHeaders[roundHeaders.length - 1].getText().split(' ')[1]
  )
  $(`form[data-testid="form-three-${lastRound}"] .bp3-intent-primary`).click()

  $(`h2=Round ${lastRound + 1}`).waitForExist(10000)
}

describe('create audit page', () => {
  it('should have a button', () => {
    browser.url('/')
    const title = browser.getTitle()
    expect(title).toBe('Arlo (by VotingWorks)')

    const createBtn = $('.bp3-button-text=Create a New Audit')
    expect(createBtn.getText()).toBe('Create a New Audit')
  })

  it('should create a new audit', () => {
    start()
  })
})

describe('form one', () => {
  it('should submit', () => {
    formOne()
  })
})

describe('form two', () => {
  it('should submit', () => {
    formTwo()
  })
})

describe('form three', () => {
  it('should go to the next round', () => {
    formTwo()
    formThreeNext()
  })

  it('should cycle through several rounds', () => {
    formTwo()
    formThreeNext()
    formThreeNext()
    formThreeNext()
  })

  it('should complete the audit', () => {
    formTwo()
    formThreeNext()
    const inputs = $$('.bp3-input')
    inputs[inputs.length - 2].addValue('100')
    inputs[inputs.length - 1].addValue('160')
    $(`form[data-testid="form-three-2"] .bp3-intent-primary`).click()
    $('.bp3-button-text=Download Audit Report').waitForExist(10000)
  })
})
