import React from 'react'
import { render } from '@testing-library/react'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { mockAudit } from './_mocks'

it('renders corretly', () => {
  const container = render(
    <SelectBallotsToAudit
      audit={mockAudit}
      isLoading={false}
      setIsLoading={jest.fn()}
      updateAudit={jest.fn()}
      getStatus={jest.fn()}
    />
  )
  expect(container).toMatchSnapshot()
})
