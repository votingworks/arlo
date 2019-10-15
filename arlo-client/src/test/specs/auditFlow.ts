import { formTwo } from './helpers'

const ballotNext = () => {
  const callout = $('.bp3-callout*=Round 1: auditing ballot')
    .getText()
    .split(' ')
  const ballot = Number(callout[callout.length - 3])
  const lastBallot = Number(callout[callout.length - 1])
  $('.radio-text=Yes/For').click()
  $('.bp3-button-text=Review').click()
  const submit = $('.bp3-button-text=Submit & Next Ballot')
  submit.waitForExist()
  submit.click()
  if (lastBallot === ballot) {
    return false
  } else {
    return true
  }
}

describe('audit flow', () => {
  it('has a happy path', () => {
    formTwo()
    $('a=Audit Board #1').click()
    $('h1*=Ballot Cards to Audit').waitForExist(10000)
    $('a=Start Auditing').click()
    while (ballotNext())
      $('.bp3-callout*=Round 1: auditing ballot').waitForExist()
    $('h1*=Ballot Cards to Audit').waitForExist(10000)
  })
})
