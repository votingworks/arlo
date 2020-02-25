import {
  fillFormTwo,
  start,
  fillFormOne,
  submitFormOne,
  submitFormTwo,
} from './helpers'
// import { voteValue } from '../../components/AuditFlow/BlockRadio'

const ballotNext = (option: string) => {
  const callout = $('.bp3-callout*=auditing ballot')
    .getText()
    .split(' ')
  const ballot = Number(callout[callout.length - 3])
  const lastBallot = Number(callout[callout.length - 1])
  $(`.radio-text=${option}`).click()
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

const ballotPrev = () => {
  const callout = $('.bp3-callout*=auditing ballot')
    .getText()
    .split(' ')
  const ballot = Number(callout[callout.length - 3])
  $('.bp3-button-text=Back').click()
  if (ballot === 1) {
    return false
  } else {
    return true
  }
}

const ballotSkip = (count: number) => {
  Array.from(Array(count).keys()).forEach(() => {
    $(`.bp3-button-text*=not found - move to next ballot`).click()
  })
}

const memberFill = () => {
  $('h3.bp3-heading + label input').addValue('Han')
  $('h3.bp3-heading + label input').addValue('Solo')
  $('.bp3-button-text=Next').click()
}

beforeEach(() => {
  start()
  fillFormOne(true)
  submitFormOne()
  fillFormTwo()
  submitFormTwo()
  $('a=Audit Board #1').click()
  memberFill()
  $('h1*=Ballot Cards to Audit').waitForExist(10000)
})

describe('audit flow', () => {
  it('has a happy path', () => {
    $('a=Start Auditing').click()
    ballotNext('Choice One')
    ballotNext('Yes/For')
    for (let i = 0; ballotNext('Yes/For') && i < 20; i++) {
      $('.bp3-callout*=auditing ballot').waitForExist()
    }
    if (ballotNext('Yes/For')) {
      $('.bp3-button=Return to audit overview').click()
    }
    $('h1*=Ballot Cards to Audit').waitForExist(10000)
  })

  it('handles all four voting options', () => {
    $('a=Start Auditing').click()
    ballotNext('Yes/For')
    $('.bp3-callout*=auditing ballot 2 of').waitForExist()
    ballotNext('No/Against')
    $('.bp3-callout*=auditing ballot 3 of').waitForExist()
    ballotNext('No audit board consensus')
    $('.bp3-callout*=auditing ballot 4 of').waitForExist()
    ballotNext('Blank vote/no mark')
    $('.bp3-callout*=auditing ballot 5 of').waitForExist()
  })

  it('enters a comment', () => {
    $('a=Start Auditing').click()
    $('.bp3-button-text=Add comment').click()
    const comment = $('textarea[name="comment"]')
    comment.waitForExist()
    comment.addValue('Test comment text')
    $(`.radio-text=Choice One`).click()
    $('.bp3-button-text=Review').click()
    $('p=COMMENT: Test comment text').waitForExist()
  })

  it('skips forward and back', () => {
    $('a=Start Auditing').click()
    ballotSkip(4)
    while (ballotPrev()) $('.bp3-callout*=auditing ballot').waitForExist()
    $('h1*=Ballot Cards to Audit').waitForExist(10000)
  })

  it('has the right name for the contest', () => {
    $('a=Start Auditing').click()
    expect($('h3=Contest Name')).toBeTruthy()
  })
})
