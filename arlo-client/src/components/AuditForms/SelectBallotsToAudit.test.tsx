import React from 'react'
import { render } from '@testing-library/react'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates } from './_mocks'

it('renders correctly', () => {
  const container = render(
    <SelectBallotsToAudit
      audit={statusStates[1]}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
      electionId="1"
    />
  )
  expect(container).toMatchSnapshot()
})

it('has radio for selecting sampleSize', () => {
  const { getByText, getByLabelText } = render(
    <SelectBallotsToAudit
      audit={statusStates[1]}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
      electionId="1"
    />
  )

  // all options should be present
  expect(getByText('BRAVO Average Sample Number: 269 samples')).toBeTruthy()
  expect(
    getByText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
  ).toBeTruthy()
  expect(getByText('78 samples'))

  // correct default should be selected
  expect(
    getByLabelText('BRAVO Average Sample Number: 269 samples').hasAttribute(
      'checked'
    )
  ).toBeTruthy()
})

it('does not display duplicate sampleSize options', () => {
  const statusState = { ...statusStates[1] }
  statusState.contests[0].sampleSizeOptions = [{ size: 30 }, { size: 30 }]
  const { queryAllByText } = render(
    <SelectBallotsToAudit
      audit={statusState}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
      electionId="1"
    />
  )

  expect(queryAllByText('30 samples').length).toBe(1)
})

it('uses the highest prob value from duplicate sampleSizes', () => {
  const statusState = { ...statusStates[1] }
  statusState.contests[0].sampleSizeOptions = [
    { size: 30, prob: 0.9 },
    { size: 30, prob: 0.8 },
  ]
  const { queryAllByText } = render(
    <SelectBallotsToAudit
      audit={statusState}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
      electionId="1"
    />
  )

  expect(
    queryAllByText(
      '30 samples (90% chance of reaching risk limit and completing the audit in one round)'
    ).length
  ).toBe(1)
})

it('changes sampleSize based on audit.rounds.contests.sampleSize', () => {
  const { getByLabelText } = render(
    <SelectBallotsToAudit
      audit={statusStates[4]}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
      electionId="1"
    />
  )

  expect(
    getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    ).hasAttribute('checked')
  ).toBeTruthy()
})
