import React from 'react'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Progress from '.'
import { jurisdictionMocks } from '../_mocks'

jest.mock('react-router', () => ({
  useParams: jest.fn().mockReturnValue({ electionId: '1' }),
}))

describe('Progress screen', () => {
  it('shows ballot manifest upload status', () => {
    const { container } = render(
      <Progress jurisdictions={jurisdictionMocks.oneManifest} />
    )

    screen.getByText('Audit Progress by Jurisdiction')
    screen.getByRole('columnheader', { name: 'Jurisdiction Name' })
    screen.getByRole('columnheader', { name: 'Status' })
    screen.getByRole('columnheader', { name: 'Total Audited' })
    screen.getByRole('columnheader', { name: 'Remaining in Round' })
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 1) // includes headers
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
    within(rows[1]).getByRole('cell', {
      name: 'Manifest upload failed: Invalid CSV',
    })
    within(rows[2]).getByRole('cell', { name: 'Jurisdiction 2' })
    within(rows[2]).getByRole('cell', { name: 'No manifest uploaded' })
    within(rows[3]).getByRole('cell', { name: 'Jurisdiction 3' })
    within(rows[3]).getByRole('cell', { name: 'Manifest received' })
    expect(container).toMatchSnapshot()
  })

  it('shows round status', () => {
    const { container } = render(
      <Progress jurisdictions={jurisdictionMocks.oneComplete} />
    )

    screen.getByText('Audit Progress by Jurisdiction')
    screen.getByRole('columnheader', { name: 'Jurisdiction Name' })
    screen.getByRole('columnheader', { name: 'Status' })
    screen.getByRole('columnheader', { name: 'Total Audited' })
    screen.getByRole('columnheader', { name: 'Remaining in Round' })
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 1) // includes headers
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
    within(rows[1]).getByRole('cell', { name: 'In progress' })
    within(rows[1]).getByRole('cell', { name: '4' })
    within(rows[1]).getByRole('cell', { name: '6' })
    within(rows[2]).getByRole('cell', { name: 'Jurisdiction 2' })
    within(rows[2]).getByRole('cell', { name: 'Not started' })
    within(rows[2]).getByRole('cell', { name: '0' })
    within(rows[2]).getByRole('cell', { name: '20' })
    within(rows[3]).getByRole('cell', { name: 'Jurisdiction 3' })
    within(rows[3]).getByRole('cell', { name: 'Complete' })
    within(rows[3]).getByRole('cell', { name: '30' })
    within(rows[3]).getByRole('cell', { name: '0' })
    expect(container).toMatchSnapshot()
  })

  it('shows the detail modal', () => {
    const { container } = render(
      <Progress jurisdictions={jurisdictionMocks.oneManifest} />
    )

    // Click on a jurisdiction name to open the detail modal
    userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
    screen.getByText('Jurisdiction 1 Audit Information')
    expect(container).toMatchSnapshot()

    // Close the detail modal
    userEvent.click(screen.getAllByRole('button', { name: 'Close' })[0])
    expect(
      screen.queryByText('Jurisdiction 1 Audit Information')
    ).not.toBeInTheDocument()
  })

  it('filters by jurisdiction name', async () => {
    render(<Progress jurisdictions={jurisdictionMocks.oneManifest} />)

    const filter = screen.getByPlaceholderText('Filter by jurisdiction name...')
    await userEvent.type(filter, '1')
    expect(screen.getAllByRole('row')).toHaveLength(1 + 1) // includes headers
    screen.getByRole('cell', { name: 'Jurisdiction 1' })

    userEvent.clear(filter)
    await userEvent.type(filter, 'Jurisdiction')
    expect(screen.getAllByRole('row')).toHaveLength(
      jurisdictionMocks.oneManifest.length + 1
    )
  })

  it('sorts', () => {
    const { rerender } = render(
      <Progress jurisdictions={jurisdictionMocks.oneManifest} />
    )

    // Toggle sorting by name
    // First click doesn't change order because they are sorted by name by default
    const nameHeader = screen.getByRole('columnheader', {
      name: 'Jurisdiction Name',
    })
    userEvent.click(nameHeader)
    let rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })

    userEvent.click(nameHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 3' })

    userEvent.click(nameHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })

    // Toggle sorting by status
    let statusHeader = screen.getByRole('columnheader', {
      name: 'Status',
    })
    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'No manifest uploaded' })

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Manifest received' })

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', {
      name: 'Manifest upload failed: Invalid CSV',
    })

    // Toggle sorting by status once audit begins
    rerender(<Progress jurisdictions={jurisdictionMocks.oneComplete} />)

    statusHeader = screen.getByRole('columnheader', {
      name: 'Status',
    })
    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Not started' })

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Complete' })

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'In progress' })
  })
})
