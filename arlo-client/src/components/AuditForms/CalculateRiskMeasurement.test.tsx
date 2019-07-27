import React from 'react'
import { render } from '@testing-library/react'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'
import { statusStates } from './_mocks'

describe('CalculateRiskMeasurement', () => {
  it('renders first round corretly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders completion in first round corretly', () => {
    const container = render(
      <CalculateRiskMeasurement
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })
})
