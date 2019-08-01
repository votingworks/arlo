import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import { statusStates } from './_mocks'

describe('SelectBallotsToAudit', () => {
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
  /*
  it('changes selected sampleSize', () => {
    const { getByLabelText } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
      />
    )

    const input: any = getByLabelText('78 samples')
    fireEvent.click(input)
    expect(input.hasAttribute('checked')).toBeTruthy()
  })
  */

  it('changes number of audits', () => {
    const { getByTestId } = render(
      <SelectBallotsToAudit
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
      />
    )

    const auditBoardInput: any = getByTestId('audit-boards')
    fireEvent.change(auditBoardInput, { target: { selected: 3 } })
    expect(auditBoardInput.selected).toBe(3)
  })
})
