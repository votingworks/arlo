import {
  start,
  fillFormOne,
  fillFormTwo,
  formThreeNext,
  submitFormOne,
  submitFormTwo,
} from './helpers'

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
    start()
    fillFormOne()
    submitFormOne()
  })
})

describe('form two', () => {
  it('should submit', () => {
    start()
    fillFormOne()
    submitFormOne()
    fillFormTwo()
    submitFormTwo()
  })
})

describe('form three', () => {
  it('should go to the next round', () => {
    start()
    fillFormOne()
    submitFormOne()
    fillFormTwo()
    submitFormTwo()
    formThreeNext()
  })

  it('should cycle through several rounds', () => {
    start()
    fillFormOne()
    submitFormOne()
    fillFormTwo()
    submitFormTwo()
    formThreeNext()
    formThreeNext()
    formThreeNext()
  })

  it('should complete the audit', () => {
    start()
    fillFormOne()
    submitFormOne()
    fillFormTwo()
    submitFormTwo()
    formThreeNext()
    const inputs = $$('.bp3-input')
    inputs[inputs.length - 2].addValue('100')
    inputs[inputs.length - 1].addValue('160')
    $(`form[data-testid="form-three-2"] .bp3-intent-primary`).click()
    $('.bp3-button-text=Download Audit Report').waitForExist(10000)
  })
})
