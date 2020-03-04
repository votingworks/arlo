import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import { statusStates } from './_mocks'
import StatusBox from './StatusBox'

describe('StatusBox', () => {
  it('renders a complete state', () => {
    const { container } = render(
      <StatusBox
        electionId="election-id"
        audit={statusStates[5]}
        launched
        started
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders the rounds in progress state', () => {
    const { container } = render(
      <StatusBox
        electionId="election-id"
        audit={statusStates[4]}
        launched
        started
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('downloads final report', async () => {
    window.open = jest.fn()
    const { findByText } = render(
      <StatusBox
        electionId="election-id"
        audit={statusStates[5]}
        launched
        started
      />
    )

    const button = await findByText('Download Audit Reports')
    fireEvent.click(button, { bubbles: true })

    expect(window.open).toBeCalledTimes(1)
    expect(window.open).toBeCalledWith('/election/election-id/audit/report')
  })
})
