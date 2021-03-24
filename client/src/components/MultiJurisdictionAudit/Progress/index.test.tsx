import React from 'react'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Progress from '.'
import {
  jurisdictionMocks,
  auditSettings,
  roundMocks,
  auditBoardMocks,
} from '../useSetupMenuItems/_mocks'
import { withMockFetch } from '../../testUtilities'
import { jaApiCalls } from '../_mocks'
import { dummyBallots } from '../../DataEntry/_mocks'

jest.mock('react-router', () => ({
  useParams: jest.fn().mockReturnValue({ electionId: '1' }),
}))

// Borrowed from generateSheets.test.tsx
const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const realjspdf = jest.requireActual('jspdf')
  const mockjspdf = new realjspdf({ format: 'letter' })
  // eslint-disable-next-line func-names
  return function() {
    return {
      ...mockjspdf,
      addImage: jest.fn(),
      save: mockSavePDF,
    }
  }
})
window.URL.createObjectURL = jest.fn()

describe('Progress screen', () => {
  afterAll(() => jest.restoreAllMocks())

  it('shows ballot manifest upload status', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneManifest}
        auditSettings={auditSettings.all}
        round={null}
      />
    )
    screen.getByText('Audit Progress')
    screen.getByRole('columnheader', { name: 'Jurisdiction' })
    screen.getByRole('columnheader', { name: 'Status' })
    screen.getByRole('columnheader', { name: 'Ballots in Manifest' })
    expect(
      screen.queryByRole('columnheader', { name: 'Ballots Audited' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('columnheader', { name: 'Ballots Remaining' })
    ).not.toBeInTheDocument()
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 1) // includes headers
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
    within(rows[1]).getByRole('cell', {
      name: 'Manifest upload failed',
    })
    within(rows[2]).getByRole('cell', { name: 'Jurisdiction 2' })
    within(rows[2]).getByRole('cell', { name: 'No manifest uploaded' })
    within(rows[3]).getByRole('cell', { name: 'Jurisdiction 3' })
    within(rows[3]).getByRole('cell', { name: '2,117' })
    within(rows[3]).getByRole('cell', { name: 'Manifest uploaded' })
  })

  it('shows round status', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneComplete}
        auditSettings={auditSettings.all}
        round={roundMocks.singleIncomplete[0]}
      />
    )

    screen.getByText('Audit Progress')
    screen.getByRole('columnheader', { name: 'Jurisdiction' })
    screen.getByRole('columnheader', { name: 'Status' })
    screen.getByRole('columnheader', { name: 'Ballots in Manifest' })
    screen.getByRole('columnheader', { name: 'Ballots Audited' })
    screen.getByRole('columnheader', { name: 'Ballots Remaining' })
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 1) // includes headers
    within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
    within(rows[1]).getByRole('cell', { name: 'In progress' })
    within(rows[1]).getByRole('cell', { name: '4' })
    within(rows[1]).getByRole('cell', { name: '2,117' })
    within(rows[1]).getByRole('cell', { name: '6' })
    within(rows[2]).getByRole('cell', { name: 'Jurisdiction 2' })
    within(rows[2]).getByRole('cell', { name: 'Not started' })
    within(rows[2]).getByRole('cell', { name: '0' })
    within(rows[2]).getByRole('cell', { name: '0' })
    within(rows[2]).getByRole('cell', { name: '20' })
    within(rows[3]).getByRole('cell', { name: 'Jurisdiction 3' })
    within(rows[3]).getByRole('cell', { name: 'Complete' })
    within(rows[3]).getByRole('cell', { name: '30' })
    within(rows[3]).getByRole('cell', { name: '2,117' })
    within(rows[3]).getByRole('cell', { name: '0' })
  })

  it('toggles between ballots and samples', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneComplete}
        auditSettings={auditSettings.all}
        round={roundMocks.singleIncomplete[0]}
      />
    )

    const ballotsSwitch = screen.getByRole('checkbox', {
      name: 'Count unique sampled ballots',
    })
    userEvent.click(ballotsSwitch)
    let rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: '5' })
    within(rows[1]).getByRole('cell', { name: '6' })
    within(rows[2]).getByRole('cell', { name: '0' })
    within(rows[2]).getByRole('cell', { name: '22' })
    within(rows[3]).getByRole('cell', { name: '31' })
    within(rows[3]).getByRole('cell', { name: '0' })

    userEvent.click(ballotsSwitch)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: '4' })
    within(rows[1]).getByRole('cell', { name: '6' })
    within(rows[2]).getByRole('cell', { name: '0' })
    within(rows[2]).getByRole('cell', { name: '20' })
    within(rows[3]).getByRole('cell', { name: '30' })
    within(rows[3]).getByRole('cell', { name: '0' })
  })

  it('shows a different toggle label for batch audits', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneComplete}
        auditSettings={auditSettings.batchComparisonAll}
        round={roundMocks.singleIncomplete[0]}
      />
    )
    screen.getByRole('checkbox', {
      name: 'Count unique sampled batches',
    })
  })

  it('filters by jurisdiction name', async () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneManifest}
        auditSettings={auditSettings.all}
        round={null}
      />
    )

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
      <Progress
        jurisdictions={jurisdictionMocks.oneManifest}
        auditSettings={auditSettings.all}
        round={null}
      />
    )

    // Toggle sorting by name
    // First click doesn't change order because they are sorted by name by default
    const nameHeader = screen.getByRole('columnheader', {
      name: 'Jurisdiction',
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
    within(rows[1]).getByText('No manifest uploaded')

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: 'Manifest uploaded' })

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', {
      name: 'Manifest upload failed',
    })

    // Toggle sorting by status once audit begins
    rerender(
      <Progress
        jurisdictions={jurisdictionMocks.oneComplete}
        auditSettings={auditSettings.all}
        round={roundMocks.singleIncomplete[0]}
      />
    )

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

  it('shows the detail modal before the audit starts', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.oneManifest}
        auditSettings={auditSettings.all}
        round={null}
      />
    )

    // Click on a jurisdiction name to open the detail modal
    userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
    let modal = screen
      .getByRole('heading', { name: 'Jurisdiction 1' })
      .closest('div.bp3-dialog')! as HTMLElement
    within(modal).getByRole('heading', {
      name: 'Jurisdiction Files',
    })
    let manifestCard = within(modal)
      .getByRole('heading', {
        name: 'Ballot Manifest',
      })
      .closest('div')!
    within(manifestCard).getByText('Upload failed')
    within(manifestCard).getByText('Invalid CSV')
    const manifestLink = within(manifestCard).getByRole('link', {
      name: 'manifest.csv',
    })
    expect(manifestLink).toHaveAttribute(
      'href',
      '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest/csv'
    )

    // Close the detail modal
    userEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(modal).not.toBeInTheDocument()

    // Click on a different jurisdiction's status tag to open the modal
    userEvent.click(screen.getByText('Manifest uploaded'))
    modal = screen
      .getByRole('heading', { name: 'Jurisdiction 3' })
      .closest('div.bp3-dialog')! as HTMLElement
    manifestCard = within(modal)
      .getByRole('heading', {
        name: 'Ballot Manifest',
      })
      .closest('div')!
    within(manifestCard).getByText('Uploaded')
    within(manifestCard).getByRole('link', {
      name: 'manifest.csv',
    })
    userEvent.click(screen.getByRole('button', { name: 'Close' }))

    // Check the last jurisdiction with no manifest uploaded
    userEvent.click(screen.getByText('No manifest uploaded'))
    modal = screen
      .getByRole('heading', { name: 'Jurisdiction 2' })
      .closest('div.bp3-dialog')! as HTMLElement
    manifestCard = within(modal)
      .getByRole('heading', {
        name: 'Ballot Manifest',
      })
      .closest('div')!
    within(manifestCard).getByText('No file uploaded')
    userEvent.click(screen.getByRole('button', { name: 'Close' }))
  })

  it('shows the detail modal with JA file download buttons after the audit starts', async () => {
    const expectedCalls = [
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
      jaApiCalls.getRetrievalList,
      jaApiCalls.getBallots(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByRole('heading', {
        name: 'Round 1 Data Entry',
      })

      window.open = jest.fn()
      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Aggregated Ballot Retrieval List/,
        })
      )

      expect(
        screen.getByRole('button', {
          name: /Download Aggregated Ballot Retrieval List/,
        })
      ).toBeDisabled()
      // expect(window.open).toHaveBeenCalledWith(
      //   '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots/retrieval-list'
      // )

      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Placeholder Sheets/,
        })
      )
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Placeholders - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
      mockSavePDF.mockClear()
      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Ballot Labels/,
        })
      )
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Round 1 Labels - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
      mockSavePDF.mockClear()
      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Audit Board Credentials/,
        })
      )
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Audit Board Credentials - Jurisdiction 1 - Test Audit.pdf',
          { returnPromise: true }
        )
      )
    })
  })

  it('shows a message in the detail modal when no ballots sampled', async () => {
    const expectedCalls = [
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('No ballots sampled')
    })
  })

  it('shows a message in the detail modal when no audit boards set up', async () => {
    const expectedCalls = [
      jaApiCalls.getAuditBoards([]),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText(
        'Waiting for jurisdiction to set up audit boards'
      )
    })
  })

  it('shows status for ballot manifest and batch tallies for batch comparison audits', () => {
    render(
      <Progress
        jurisdictions={jurisdictionMocks.twoManifestsOneTallies}
        auditSettings={auditSettings.all}
        round={null}
      />
    )
    // Shows aggregated status for multiple files
    let rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', {
      name: 'Upload failed',
    })
    within(rows[2]).getByRole('cell', { name: '1/2 files uploaded' })
    within(rows[3]).getByRole('cell', { name: '2/2 files uploaded' })

    // Toggle sorting by status
    const statusHeader = screen.getByRole('columnheader', {
      name: 'Status',
    })
    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByText('Upload failed')

    userEvent.click(statusHeader)
    rows = screen.getAllByRole('row')
    within(rows[1]).getByRole('cell', { name: '2/2 files uploaded' })

    // Shows manifest and tallies the modal
    userEvent.click(screen.getByText('2/2 files uploaded'))
    const modal = screen
      .getByRole('heading', { name: 'Jurisdiction 3' })
      .closest('div.bp3-dialog')! as HTMLElement
    within(modal).getByRole('heading', {
      name: 'Jurisdiction Files',
    })
    const manifestCard = within(modal)
      .getByRole('heading', {
        name: 'Ballot Manifest',
      })
      .closest('div')!
    within(manifestCard).getByText('Uploaded')
    const talliesCard = within(modal)
      .getByRole('heading', {
        name: 'Candidate Totals by Batch',
      })
      .closest('div')!
    within(talliesCard).getByText('Uploaded')
    const talliesLink = within(talliesCard).getByRole('link', {
      name: 'tallies.csv',
    })
    expect(talliesLink).toHaveAttribute(
      'href',
      '/api/election/1/jurisdiction/jurisdiction-id-3/batch-tallies/csv'
    )
  })
})
