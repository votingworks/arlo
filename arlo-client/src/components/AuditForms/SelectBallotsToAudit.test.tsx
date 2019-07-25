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

it('changes sampleSize based on audit.rounds.contests.sampleSize', () => {
  const { getByLabelText } = render(
    <SelectBallotsToAudit
      audit={statusStates[4]}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
    />
  )

  expect(
    getByLabelText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    ).hasAttribute('checked')
  ).toBeTruthy()
})
