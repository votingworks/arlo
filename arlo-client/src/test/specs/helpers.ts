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

export const fillFormOne = () => {
  $('#audit-name').addValue('Election')
  $('input[name="contests[0].name"]').addValue('Contest')
  $('input[name="contests[0].choices[0].name"]').addValue('Choice One')
  $('input[name="contests[0].choices[0].numVotes"]').addValue('792')
  $('input[name="contests[0].choices[1].name"]').addValue('Choice Two')
  $('input[name="contests[0].choices[1].numVotes"]').addValue('1325')
  $('input[name="contests[0].totalBallotsCast"]').addValue('2123')
  $('#random-seed').addValue('1234567890')
}

export const submitFormOne = () => {
  $('.bp3-button.bp3-intent-primary').click()
  $('.bp3-heading=Select Ballots to Audit').waitForExist(10000)
}

export const fillFormTwo = () => {
  $('input[name="manifest"]').setValue(filePath)
}

export const submitFormTwo = () => {
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
