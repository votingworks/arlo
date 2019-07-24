import React from 'react'
import { render } from '@testing-library/react'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates } from './_mocks'

it('renders corretly', () => {
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
  const { getByText } = render(
    <SelectBallotsToAudit
      audit={statusStates[1]}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
    />
  )

  expect(getByText('BRAVO Average Sample Number: 269 samples')).toBeTruthy()
  expect(
    getByText(
      '379 samples (80% chance of reaching risk limit and completing the audit in one round)'
    )
  ).toBeTruthy()
  expect(getByText('78 samples'))
})
