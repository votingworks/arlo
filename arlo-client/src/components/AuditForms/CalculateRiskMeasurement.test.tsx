import React from 'react'
import { render } from '@testing-library/react'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { mockAudit } from './_mocks'

it('renders corretly', () => {
  const container = render(
    <CalculateRiskMeasurement
      audit={mockAudit}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      electionId="1"
    />
  )
  expect(container).toMatchSnapshot()
})
