import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Intent } from '@blueprintjs/core'
import { QueryClientProvider } from 'react-query'
import { Route } from 'react-router-dom'
import {
  jurisdictionMocks,
  auditSettings,
  roundMocks,
  auditBoardMocks,
  contestMocks,
} from '../useSetupMenuItems/_mocks'
import { withMockFetch, renderWithRouter } from '../../testUtilities'
import { aaApiCalls, jaApiCalls } from '../../_mocks'
import Progress, { IProgressProps } from './Progress'
import { dummyBallots } from '../../AuditBoard/_mocks'
import { batchesMocks } from '../../JurisdictionAdmin/_mocks'
import * as utilities from '../../utilities'
import { queryClient } from '../../../App'
import { IBatch } from '../../JurisdictionAdmin/useBatchResults'
import { IContest } from '../../../types'

// Borrowed from generateSheets.test.tsx
const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  const mockjspdf = new jsPDF({ format: 'letter' })
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
window.open = jest.fn()

const expectStatusTag = (cell: HTMLElement, status: string, intent: Intent) => {
  const statusTag = within(cell)
    .getByText(status)
    .closest('.bp3-tag') as HTMLElement
  if (intent === 'none') expect(statusTag.className).not.toMatch(/bp3-intent/)
  else expect(statusTag).toHaveClass(`bp3-intent-${intent}`)
}

// User-type agnostic API calls
const apiCalls = {
  getBatches: (response: { batches: IBatch[] }) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches',
    response,
  }),
  getJurisdictionContests: (response: { contests: IContest[] }) => ({
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/contest`,
    response,
  }),
}

const render = (props: Partial<IProgressProps> = {}) =>
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
      <Route
        path="/election/:electionId/progress"
        render={routeProps => (
          <Progress
            {...routeProps}
            jurisdictions={jurisdictionMocks.oneManifest}
            auditSettings={auditSettings.all}
            round={null}
            {...props}
          />
        )}
      />
    </QueryClientProvider>,
    { route: '/election/1/progress' }
  )

describe('Progress screen', () => {
  beforeEach(() => {
    // Clear mock call counts, etc.
    jest.clearAllMocks()
  })

  afterAll(() => jest.restoreAllMocks())

  it('shows ballot manifest upload status', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      screen.getByText('Audit Progress')

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(3)
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'Manifest upload failed', 'danger')
      expect(row1[2]).toBeEmpty()
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'No manifest uploaded', 'none')
      expect(row2[2]).toBeEmpty()
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expectStatusTag(row3[1], 'Manifest uploaded', 'success')
      expect(row3[2]).toHaveTextContent('2,117')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('2,117')

      expect(
        screen.queryByRole('checkbox', {
          name: 'Count unique sampled ballots',
        })
      ).not.toBeInTheDocument()
    })
  })

  it('shows round status', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      screen.getByText('Audit Progress')

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(5)
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Ballots Audited')
      expect(headers[4]).toHaveTextContent('Ballots Remaining')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(jurisdictionMocks.oneManifest.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'In progress', 'warning')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('4')
      expect(row1[4]).toHaveTextContent('6')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'Not started', 'none')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('0')
      expect(row2[4]).toHaveTextContent('0')
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expectStatusTag(row3[1], 'Complete', 'success')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toHaveTextContent('30')
      expect(row3[4]).toHaveTextContent('0')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('34')
      expect(footers[4]).toHaveTextContent('26')
    })
  })

  it('toggles between ballots and samples', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const ballotsSwitch = screen.getByRole('checkbox', {
        name: 'Count unique sampled ballots',
      })
      userEvent.click(ballotsSwitch)

      let rows = screen.getAllByRole('row')
      let row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expect(row1[3]).toHaveTextContent('5')
      expect(row1[4]).toHaveTextContent('6')
      let row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[3]).toHaveTextContent('0')
      expect(row2[4]).toHaveTextContent('22')
      let row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[3]).toHaveTextContent('31')
      expect(row3[4]).toHaveTextContent('0')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('36')
      expect(footers[4]).toHaveTextContent('28')

      userEvent.click(ballotsSwitch)

      rows = screen.getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expect(row1[3]).toHaveTextContent('4')
      expect(row1[4]).toHaveTextContent('6')
      row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[3]).toHaveTextContent('0')
      expect(row2[4]).toHaveTextContent('20')
      row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[3]).toHaveTextContent('30')
      expect(row3[4]).toHaveTextContent('0')
    })
  })

  it('shows additional columns during setup for batch audits', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.twoManifestsOneTallies,
        auditSettings: auditSettings.batchComparisonAll,
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const headers = screen.getAllByRole('columnheader')
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Batches in Manifest')
      expect(headers[4]).toHaveTextContent('Valid Voted Ballots in Batches')

      const rows = screen.getAllByRole('row')
      // Jurisdiction 1 - manifest errored, no ballot/batches count shown
      const row1 = within(rows[1]).getAllByRole('cell')
      expectStatusTag(row1[1], 'Upload failed', 'danger')
      expect(row1[2]).toBeEmpty()
      expect(row1[3]).toBeEmpty()
      expect(row1[4]).toBeEmpty()
      // Jurisdiction 2 - manifest success, no tallies
      const row2 = within(rows[2]).getAllByRole('cell')
      expectStatusTag(row2[1], '1/2 files uploaded', 'warning')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('10')
      expect(row2[4]).toBeEmpty()
      // Jurisdiction 3 - manifest success, tallies success
      const row3 = within(rows[3]).getAllByRole('cell')
      expectStatusTag(row3[1], '2/2 files uploaded', 'success')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toHaveTextContent('10')
      expect(row3[4]).toHaveTextContent('15')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('4,234')
      expect(footers[3]).toHaveTextContent('20')
      expect(footers[4]).toHaveTextContent('15')
    })
  })

  it('shows additional columns during setup for ballot comparison audits', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.allManifestsSomeCVRs,
        auditSettings: auditSettings.ballotComparisonAll,
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const headers = screen.getAllByRole('columnheader')
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Ballots in CVR')

      const rows = screen.getAllByRole('row')
      // Jurisdiction 1 - manifest success, no CVR
      const row1 = within(rows[1]).getAllByRole('cell')
      expectStatusTag(row1[1], '1/2 files uploaded', 'warning')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toBeEmpty()
      // Jurisdiction 2 - manifest success, CVR success
      const row2 = within(rows[2]).getAllByRole('cell')
      expectStatusTag(row2[1], '2/2 files uploaded', 'success')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('10')
      // Jurisdiction 3 - manifest success, no CVR
      const row3 = within(rows[3]).getAllByRole('cell')
      expectStatusTag(row3[1], '1/2 files uploaded', 'warning')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toBeEmpty()

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('10')

      // Shows manifest and cvrs in the modal
      userEvent.click(screen.getByText('2/2 files uploaded'))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 2' })
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
      const cvrsCard = within(modal)
        .getByRole('heading', {
          name: 'Cast Vote Records (CVR)',
        })
        .closest('div')!
      within(cvrsCard).getByText('Uploaded')
      const cvrsLink = within(cvrsCard).getByRole('link', {
        name: 'cvrs.csv',
      })
      expect(cvrsLink).toHaveAttribute(
        'href',
        '/api/election/1/jurisdiction/jurisdiction-id-2/cvrs/csv'
      )
      within(cvrsCard).getByText('(ClearBallot)')
    })
  })

  it('shows additional columns during setup for hybrid audits', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.hybridTwoManifestsOneCvr,
        auditSettings: auditSettings.hybridAll,
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const headers = screen.getAllByRole('columnheader')
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Non-CVR Ballots in Manifest')
      expect(headers[4]).toHaveTextContent('CVR Ballots in Manifest')
      expect(headers[5]).toHaveTextContent('Ballots in CVR')

      const rows = screen.getAllByRole('row')
      // Jurisdiction 1 - manifest success, no CVR
      const row1 = within(rows[1]).getAllByRole('cell')
      expectStatusTag(row1[1], '1/2 files uploaded', 'warning')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('117')
      expect(row1[4]).toHaveTextContent('2,000')
      expect(row1[5]).toBeEmpty()
      // Jurisdiction 2 - manifest success, CVR success
      const row2 = within(rows[2]).getAllByRole('cell')
      expectStatusTag(row2[1], '2/2 files uploaded', 'success')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('1,117')
      expect(row2[4]).toHaveTextContent('1,000')
      expect(row2[5]).toHaveTextContent('10')
      // Jurisdiction 3 - no manifest, no CVR
      const row3 = within(rows[3]).getAllByRole('cell')
      expectStatusTag(row3[1], '0/2 files uploaded', 'none')
      expect(row3[2]).toBeEmpty()
      expect(row3[3]).toBeEmpty()
      expect(row3[4]).toBeEmpty()
      expect(row3[5]).toBeEmpty()

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('4,234')
      expect(footers[3]).toHaveTextContent('1,234')
      expect(footers[4]).toHaveTextContent('3,000')
      expect(footers[5]).toHaveTextContent('10')
    })
  })

  it('shows a different toggle label for batch audits', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        auditSettings: auditSettings.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      screen.getByRole('checkbox', {
        name: 'Count unique sampled batches',
      })
    })
  })

  it('shows a button to download the table as a CSV', async () => {
    // JSDOM doesn't implement innerText, so we implement it using textContent
    // (but we have to strip out the label for the sorting icon)
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() {
        return this.textContent.replace('double-caret-vertical', '')
      },
      configurable: true,
    })
    const downloadFileMock = jest
      .spyOn(utilities, 'downloadFile')
      .mockImplementation()

    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: /Download as CSV/ }))
      expect(downloadFileMock).toHaveBeenCalled()
      expect(downloadFileMock.mock.calls[0][1]).toMatch(
        /audit-progress-Test Audit-/
      )
      const fileBlob = downloadFileMock.mock.calls[0][0] as Blob
      expect(fileBlob.type).toEqual('text/csv')
      expect(await new Response(fileBlob).text()).toEqual(
        '"Jurisdiction","Status","Ballots in Manifest","Ballots Audited","Ballots Remaining"\n' +
          '"Jurisdiction 1","In progress","2,117","4","6"\n' +
          '"Jurisdiction 2","Not started","2,117","0","20"\n' +
          '"Jurisdiction 3","Complete","2,117","30","0"\n' +
          '"Total","1/3 complete","6,351","34","26"'
      )

      downloadFileMock.mockRestore()
      delete HTMLElement.prototype.innerText
    })
  })

  it('filters by jurisdiction name', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const filter = screen.getByPlaceholderText(
        'Filter by jurisdiction name...'
      )
      userEvent.type(filter, '1')
      expect(screen.getAllByRole('row')).toHaveLength(1 + 2) // includes headers and footers
      screen.getByRole('cell', { name: 'Jurisdiction 1' })

      userEvent.clear(filter)
      userEvent.type(filter, 'Jurisdiction')
      expect(screen.getAllByRole('row')).toHaveLength(
        jurisdictionMocks.oneManifest.length + 2
      )
    })
  })

  it('sorts', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

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
      const statusHeader = screen.getByRole('columnheader', {
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
    })
  })

  it('sorts by status once the audit is in progress', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      let rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Not started' })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Complete' })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'In progress' })
    })
  })

  it('shows the detail modal before the audit starts', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

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
  })

  it('shows the detail modal with JA file download buttons after a ballot comparison audit starts', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByRole('heading', {
        name: 'Round 1 Data Entry',
      })

      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Ballot Retrieval List/,
        })
      )

      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots/retrieval-list'
      )

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

  it('shows the detail modal with JA file download buttons after a batch audit starts', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJurisdictionContests({ contests: contestMocks.oneTargeted }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        auditSettings: auditSettings.batchComparisonAll,
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleComplete[0],
      })

      // Open detail modal
      userEvent.click(
        await screen.findByRole('button', { name: 'Jurisdiction 1' })
      )
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByRole('heading', {
        name: 'Round 1 Data Entry',
      })

      userEvent.click(
        await within(modal).findByRole('button', {
          name: /Download Batch Retrieval List/,
        })
      )
      expect(window.open).toHaveBeenCalledWith(
        '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/retrieval-list'
      )

      userEvent.click(
        await within(modal).findByRole('button', {
          name: /Download Batch Tally Sheets/,
        })
      )
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith('Batch Tally Sheets.pdf', {
          returnPromise: true,
        })
      )
    })
  })

  it('shows a message in the detail modal when no ballots sampled', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('No ballots sampled')
    })
  })

  it('shows a message in the detail modal when no audit boards set up', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards([]),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.noneStarted,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText(
        'Waiting for jurisdiction to set up audit boards'
      )
    })
  })

  it('shows status for ballot manifest and batch tallies for batch comparison audits', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.twoManifestsOneTallies,
        auditSettings: auditSettings.batchComparisonAll,
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      // Shows aggregated status for multiple files
      let rows = screen.getAllByRole('row')

      expectStatusTag(
        within(rows[1]).getAllByRole('cell')[1],
        'Upload failed',
        'danger'
      )
      expectStatusTag(
        within(rows[2]).getAllByRole('cell')[1],
        '1/2 files uploaded',
        'warning'
      )
      expectStatusTag(
        within(rows[3]).getAllByRole('cell')[1],
        '2/2 files uploaded',
        'success'
      )

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

      // Shows manifest and tallies in the modal
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

  it('shows a message in the detail modal when no batches sampled', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBatches({ batches: [], resultsFinalizedAt: null }),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        auditSettings: auditSettings.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('No ballots sampled')
    })
  })

  it('shows a button to unfinalize batch results', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.single),
      jaApiCalls.getBatches(batchesMocks.complete),
      jaApiCalls.unfinalizeBatchResults,
    ]
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdictions: jurisdictionMocks.allComplete,
        auditSettings: auditSettings.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      userEvent.click(
        await screen.findByRole('button', { name: 'Jurisdiction 1' })
      )
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('Results finalized')

      Object.defineProperty(window, 'location', {
        writable: true,
        value: { reload: jest.fn() },
      })
      userEvent.click(
        within(modal).getByRole('button', { name: 'Unfinalize Results' })
      )
      await waitFor(() => {
        expect(window.location.reload).toHaveBeenCalled()
      })
    })
  })

  it('renders progress map with jurisdiction upload status', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.uploadingWithAlabamaJurisdictions,
        auditSettings: auditSettings.batchComparisonAll,
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })
      expect(container.querySelectorAll('.county.gray').length).toBe(1) // not started
      expect(container.querySelectorAll('.county.progress').length).toBe(1) // in progress
      expect(container.querySelectorAll('.county.danger').length).toBe(1) // errored

      // Check that the county tooltip shows on hover
      userEvent.hover(container.querySelector('.county.progress')!)
      expect(container.querySelector('#tooltip')).toBeVisible()
      expect(container.querySelector('#tooltip')).toHaveTextContent('Geneva')
      userEvent.unhover(container.querySelector('.county.progress')!)
      expect(container.querySelector('#tooltip')).not.toBeVisible()
    })
  })

  it('renders progress map with all completed jurisdictions', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions: jurisdictionMocks.allCompleteWithAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })
      expect(container.querySelectorAll('.county.success').length).toBe(3) // all completed
    })
  })

  it('renders progress map with 2 matched & completed jurisdictions', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions:
          jurisdictionMocks.allCompleteWithTwoMatchedAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })
      expect(container.querySelectorAll('.county.success').length).toBe(2) // all completed

      // should including showing map label
      expect(screen.queryAllByText('Complete').length).toBe(4)
    })
  })

  it('does not render progress map with 1 matched & completed jurisdictions', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions:
          jurisdictionMocks.allCompleteWithOneMatchedAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      // should not show map label
      expect(screen.queryAllByText('Complete').length).toBe(3) // all completed
    })
  })
})
