import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Intent } from '@blueprintjs/core'
import { QueryClientProvider } from 'react-query'
import { Route } from 'react-router-dom'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
} from '../../testUtilities'
import {
  aaApiCalls,
  jaApiCalls,
  jurisdictionMocks,
  auditSettingsMocks,
  roundMocks,
  auditBoardMocks,
  manifestMocks,
  contestMocks,
} from '../../_mocks'
import Progress, { IProgressProps } from './Progress'
import { dummyBallots } from '../../AuditBoard/_mocks'
import * as utilities from '../../utilities'

// Borrowed from generateSheets.test.tsx
const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function mockJsPDF(options?: any) {
    return {
      ...new jsPDF(options),
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

const render = (props: Partial<IProgressProps> = {}, searchParams = '') =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <Route
        path="/election/:electionId/progress"
        render={routeProps => (
          <Progress
            {...routeProps}
            jurisdictions={jurisdictionMocks.oneManifest}
            auditSettings={auditSettingsMocks.all}
            round={null}
            {...props}
          />
        )}
      />
    </QueryClientProvider>,
    { route: `/election/1/progress${searchParams}` }
  )

describe('Progress screen', () => {
  beforeEach(() => {
    // Clear mock call counts, etc.
    jest.clearAllMocks()
  })

  afterAll(() => jest.restoreAllMocks())

  function getDefaultExpectedCalls() {
    return [
      aaApiCalls.getLastLoginByJurisdiction(new Date()),
      aaApiCalls.getMapData,
    ]
  }

  it('shows ballot manifest upload status', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()
      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })

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
      expectStatusTag(row2[1], 'Logged in', 'warning')
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

  it('shows expected number of ballots in manifest and difference if provided', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      render({
        jurisdictions: [
          {
            ...jurisdictionMocks.allManifests[0],
            expectedBallotManifestNumBallots:
              jurisdictionMocks.allManifests[0].ballotManifest!.numBallots! +
              10,
          },
          {
            ...jurisdictionMocks.allManifests[1],
            expectedBallotManifestNumBallots:
              jurisdictionMocks.allManifests[1].ballotManifest!.numBallots! -
              20,
          },
          {
            ...jurisdictionMocks.noManifests[0],
            expectedBallotManifestNumBallots: 30,
          },
          {
            ...jurisdictionMocks.allManifests[2],
            expectedBallotManifestNumBallots: null,
          },
        ],
      })

      await screen.findByRole('heading', { name: 'Audit Progress' })

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(5)
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Expected Ballots in Manifest')
      expect(headers[4]).toHaveTextContent('Difference From Expected Ballots')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(4 + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('2,127')
      expect(row1[4]).toHaveTextContent('-10')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('2,097')
      expect(row2[4]).toHaveTextContent('20')
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[2]).toHaveTextContent('')
      expect(row3[3]).toHaveTextContent('30')
      expect(row3[4]).toHaveTextContent('')
      const row4 = within(rows[4]).getAllByRole('cell')
      expect(row4[2]).toHaveTextContent('2,117')
      expect(row4[3]).toHaveTextContent('')
      expect(row4[4]).toHaveTextContent('')

      const footers = within(rows[5]).getAllByRole('cell')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('4,254')
    })
  })

  it('shows round status for ballot polling', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })

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
      expect(rows).toHaveLength(jurisdictionMocks.oneComplete.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'In progress', 'warning')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('4')
      expect(row1[4]).toHaveTextContent('6')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'Logged in', 'warning')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('0')
      expect(row2[4]).toHaveTextContent('20')
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

      expect(
        screen.queryByRole('button', { name: /Download Discrepancy Report/ })
      ).not.toBeInTheDocument()
    })
  })

  it('shows round and discrepancy status for ballot comparison', async () => {
    const expectedCalls = [
      // aaApiCalls.getMapData,
      aaApiCalls.getDiscrepancies({
        [jurisdictionMocks.oneComplete[1].id]: {
          ballot1: {
            [contestMocks.two[0].id]: {
              reportedVotes: { [contestMocks.two[0].choices[0].id]: '1' },
              auditedVotes: { [contestMocks.two[0].choices[0].id]: 'u' },
              discrepancies: { [contestMocks.two[0].choices[0].id]: 1 },
            },
            [contestMocks.two[1].id]: {
              reportedVotes: {}, // undefined, seemingly can occur if no vote was reported
              auditedVotes: { [contestMocks.two[1].choices[0].id]: 'o' },
              discrepancies: { [contestMocks.two[1].choices[0].id]: 1 },
            },
          },
        },
        [jurisdictionMocks.oneComplete[2].id]: {
          ballot2: {
            [contestMocks.one[0].id]: {
              reportedVotes: { [contestMocks.one[0].choices[0].id]: '0' },
              auditedVotes: { [contestMocks.one[0].choices[0].id]: '1' },
              discrepancies: { [contestMocks.one[0].choices[0].id]: -1 },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdictionEmpty(),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests(
        contestMocks.two,
        jurisdictionMocks.oneComplete[1].id
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        auditSettings: auditSettingsMocks.ballotComparisonAll,
        jurisdictions: jurisdictionMocks.allComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      screen.getByText('Audit Progress')

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(6)
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Discrepancies')
      expect(headers[4]).toHaveTextContent('Ballots Audited')
      expect(headers[5]).toHaveTextContent('Ballots Remaining')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(jurisdictionMocks.oneComplete.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'Complete', 'success')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('')
      expect(row1[4]).toHaveTextContent('10')
      expect(row1[5]).toHaveTextContent('0')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'Complete', 'success')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('Review 2')
      expect(row2[4]).toHaveTextContent('20')
      expect(row2[5]).toHaveTextContent('0')
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expectStatusTag(row3[1], 'Complete', 'success')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toHaveTextContent('Review 1')
      expect(row3[4]).toHaveTextContent('30')
      expect(row3[5]).toHaveTextContent('0')

      const reviewDiscrepanciesButton = screen.getByRole('button', {
        name: /Review 2/,
      })
      userEvent.click(reviewDiscrepanciesButton)
      await waitFor(() => {
        screen.getByText('Jurisdiction 2 Discrepancies')
      })
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 2 Discrepancies/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('ballot1 - Contest 1')

      const discrepancyTableHeaders = within(dialog).getAllByRole(
        'columnheader'
      )
      expect(discrepancyTableHeaders).toHaveLength(8) // 4 headers * 2 tables
      expect(discrepancyTableHeaders[0]).toHaveTextContent('Choice')
      expect(discrepancyTableHeaders[1]).toHaveTextContent('Reported Votes')
      expect(discrepancyTableHeaders[2]).toHaveTextContent('Audited Votes')
      expect(discrepancyTableHeaders[3]).toHaveTextContent('Discrepancy')

      const discrepancyTablesRows = within(dialog).getAllByRole('row')
      expect(discrepancyTablesRows).toHaveLength(4)
      const discrepancyTable1Row1 = within(
        discrepancyTablesRows[1]
      ).getAllByRole('cell')
      expect(discrepancyTable1Row1[0]).toHaveTextContent('Choice One')
      expect(discrepancyTable1Row1[1]).toHaveTextContent('1')
      expect(discrepancyTable1Row1[2]).toHaveTextContent('Undervote')
      expect(discrepancyTable1Row1[3]).toHaveTextContent('1')

      const discrepancyTable2Row1 = within(
        discrepancyTablesRows[3]
      ).getAllByRole('cell')
      expect(discrepancyTable2Row1[0]).toHaveTextContent('Choice Three')
      expect(discrepancyTable2Row1[1]).toHaveTextContent('0')
      expect(discrepancyTable2Row1[2]).toHaveTextContent('Overvote')
      expect(discrepancyTable2Row1[3]).toHaveTextContent('1')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('3/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('3')
      expect(footers[4]).toHaveTextContent('60')
      expect(footers[5]).toHaveTextContent('0')

      userEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
      await waitFor(() => {
        expect(dialog).not.toBeInTheDocument()
      })

      const downloadReportButton = screen.getByRole('button', {
        name: /Download Discrepancy Report/,
      })
      const mockDownloadWindow: { onbeforeunload?: () => void } = {}
      window.open = jest.fn().mockReturnValue(mockDownloadWindow)
      userEvent.click(downloadReportButton)
      expect(downloadReportButton).toBeDisabled()
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledTimes(1)
        expect(window.open).toBeCalledWith(`/api/election/1/discrepancy-report`)
      })
      mockDownloadWindow.onbeforeunload!()
      await waitFor(() => {
        expect(downloadReportButton).toBeEnabled()
      })
    })
  })

  it('shows round and discrepancy status for batch comparison', async () => {
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({
        [jurisdictionMocks.oneComplete[2].id]: {
          batch1: {
            [contestMocks.one[0].id]: {
              reportedVotes: { [contestMocks.one[0].choices[0].id]: 5 },
              auditedVotes: { [contestMocks.one[0].choices[0].id]: 6 },
              discrepancies: { [contestMocks.one[0].choices[0].id]: 1 },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdictionEmpty(),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests(
        [contestMocks.one[0]],
        jurisdictionMocks.oneComplete[2].id
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        auditSettings: auditSettingsMocks.batchComparisonAll,
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      screen.getByText('Audit Progress')

      const headers = screen.getAllByRole('columnheader')
      expect(headers).toHaveLength(6)
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Discrepancies')
      expect(headers[4]).toHaveTextContent('Batches Audited')
      expect(headers[5]).toHaveTextContent('Batches Remaining')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(jurisdictionMocks.oneComplete.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'In progress', 'warning')
      expect(row1[2]).toHaveTextContent('2,117')
      // Discrepancies hidden until jurisdiction is complete
      expect(row1[3]).toHaveTextContent('')
      expect(row1[4]).toHaveTextContent('4')
      expect(row1[5]).toHaveTextContent('6')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'Not logged in', 'none')
      expect(row2[2]).toHaveTextContent('2,117')
      // Discrepancies hidden until jurisdiction is complete
      expect(row2[3]).toHaveTextContent('')
      expect(row2[4]).toHaveTextContent('0')
      expect(row2[5]).toHaveTextContent('0')
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expectStatusTag(row3[1], 'Complete', 'success')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toHaveTextContent('Review 1')
      expect(row3[4]).toHaveTextContent('30')
      expect(row3[5]).toHaveTextContent('0')

      const reviewDiscrepanciesButton = screen.getByRole('button', {
        name: /Review 1/,
      })
      userEvent.click(reviewDiscrepanciesButton)
      await waitFor(() => {
        screen.getByText('Jurisdiction 3 Discrepancies')
      })
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 3 Discrepancies/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('batch1 - Contest 1')
      const discrepancyTableHeaders = within(dialog).getAllByRole(
        'columnheader'
      )
      expect(discrepancyTableHeaders).toHaveLength(4)
      expect(discrepancyTableHeaders[0]).toHaveTextContent('Choice')
      expect(discrepancyTableHeaders[1]).toHaveTextContent('Reported Votes')
      expect(discrepancyTableHeaders[2]).toHaveTextContent('Audited Votes')
      expect(discrepancyTableHeaders[3]).toHaveTextContent('Discrepancy')

      const discrepancyTableRows = within(dialog).getAllByRole('row')
      expect(discrepancyTableRows).toHaveLength(2)
      const discrepancyTableRow1 = within(discrepancyTableRows[1]).getAllByRole(
        'cell'
      )
      expect(discrepancyTableRow1[0]).toHaveTextContent('Choice One')
      expect(discrepancyTableRow1[1]).toHaveTextContent('5')
      expect(discrepancyTableRow1[2]).toHaveTextContent('6')
      expect(discrepancyTableRow1[3]).toHaveTextContent('1')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('1')
      expect(footers[4]).toHaveTextContent('34')
      expect(footers[5]).toHaveTextContent('26')

      const downloadReportButton = screen.getByRole('button', {
        name: /Download Discrepancy Report/,
      })
      const mockDownloadWindow: { onbeforeunload?: () => void } = {}
      window.open = jest.fn().mockReturnValue(mockDownloadWindow)
      userEvent.click(downloadReportButton)
      expect(downloadReportButton).toBeDisabled()
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledTimes(1)
        expect(window.open).toBeCalledWith(`/api/election/1/discrepancy-report`)
      })
      mockDownloadWindow.onbeforeunload!()
      await waitFor(() => {
        expect(downloadReportButton).toBeEnabled()
      })
    })
  })

  it('toggles between ballots and samples', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

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
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.twoManifestsOneTallies,
        auditSettings: auditSettingsMocks.batchComparisonAll,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

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
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.allManifestsSomeCVRs,
        auditSettings: auditSettingsMocks.ballotComparisonAll,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

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
    })
  })

  it('shows additional columns during setup for hybrid audits', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.hybridTwoManifestsOneCvr,
        auditSettings: auditSettingsMocks.hybridAll,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })

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
      expectStatusTag(row3[1], 'Logged in', 'warning')
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
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({}),
      aaApiCalls.getLastLoginByJurisdiction(new Date()),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        auditSettings: auditSettingsMocks.batchComparisonAll,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })

      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

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

    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      userEvent.click(
        screen.getByRole('button', { name: /Download Table as CSV/ })
      )
      expect(downloadFileMock).toHaveBeenCalled()
      expect(downloadFileMock.mock.calls[0][1]).toMatch(
        /audit-progress-Test Audit-/
      )
      const fileBlob = downloadFileMock.mock.calls[0][0] as Blob
      expect(fileBlob.type).toEqual('text/csv')
      expect(await new Response(fileBlob).text()).toEqual(
        '"Jurisdiction","Status","Ballots in Manifest","Ballots Audited","Ballots Remaining"\n' +
          '"Jurisdiction 1","In progress","2,117","4","6"\n' +
          '"Jurisdiction 2","Logged in","2,117","0","20"\n' +
          '"Jurisdiction 3","Complete","2,117","30","0"\n' +
          '"Total","1/3 complete","6,351","34","26"'
      )

      downloadFileMock.mockRestore()
      delete HTMLElement.prototype.innerText
    })
  })

  it('filters by jurisdiction name', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container, history } = render()
      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      expect(history.location.search).toEqual('')

      const filter = screen.getByPlaceholderText(
        'Filter by jurisdiction name...'
      )
      userEvent.type(filter, '1')
      expect(screen.getAllByRole('row')).toHaveLength(1 + 2) // includes headers and footers
      screen.getByRole('cell', { name: 'Jurisdiction 1' })
      expect(history.location.search).toEqual('?filter=1')

      userEvent.clear(filter)
      expect(history.location.search).toEqual('')
      userEvent.type(filter, 'Jurisdiction')
      expect(screen.getAllByRole('row')).toHaveLength(
        jurisdictionMocks.oneManifest.length + 2
      )
      expect(history.location.search).toEqual('?filter=Jurisdiction')
    })
  })

  it('sorts', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container, history } = render()

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(history.location.search).toEqual('')

      // Toggle sorting by name
      // First click doesn't change order because they are sorted by name by default
      const nameHeader = screen.getByRole('columnheader', {
        name: 'Jurisdiction',
      })
      userEvent.click(nameHeader)
      let rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Jurisdiction&dir=asc')
      })

      userEvent.click(nameHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Jurisdiction 3' })
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Jurisdiction&dir=desc')
      })

      userEvent.click(nameHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Jurisdiction 1' })
      await waitFor(() => {
        expect(history.location.search).toEqual('')
      })

      // Toggle sorting by status
      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Logged in')
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Status&dir=asc')
      })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Manifest uploaded' })
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Status&dir=desc')
      })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', {
        name: 'Manifest upload failed',
      })
      await waitFor(() => {
        expect(history.location.search).toEqual('')
      })
    })
  })

  it('loads initial sort/filter state from URL search params', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        {
          jurisdictions: jurisdictionMocks.oneManifest.map((j, i) => ({
            ...j,
            name: `${j.name} ${i % 2 === 0 ? 'Odd' : 'Even'}`,
          })),
        },
        '?sort=Jurisdiction&dir=desc&filter=Odd'
      )
      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const rows = screen.getAllByRole('row')
      expect(rows.length).toEqual(2 + 2) // includes headers and footers
      within(rows[1]).getByRole('cell', { name: 'Jurisdiction 3 Odd' })
    })
  })

  it('sorts by status once the audit is in progress', async () => {
    const expectedCalls = [
      aaApiCalls.getLastLoginByJurisdictionEmpty(),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      let rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Not logged in' })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'Complete' })

      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByRole('cell', { name: 'In progress' })
    })
  })

  it('shows the detail modal with file upload status before the audit starts', async () => {
    const expectedCalls = [
      ...getDefaultExpectedCalls(),
      jaApiCalls.getBallotManifestFile(manifestMocks.errored),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      // Click on a jurisdiction name to open the detail modal
      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      within(modal).getByRole('heading', {
        name: 'Jurisdiction Files',
      })
      const manifestCard = (
        await within(modal).findByRole('heading', {
          name: 'Ballot Manifest',
        })
      ).closest('.bp3-card') as HTMLElement
      within(manifestCard).getByText('Upload Failed')

      // Close the detail modal
      userEvent.click(screen.getByRole('button', { name: 'Close' }))
      expect(modal).not.toBeInTheDocument()

      // Tested further in JurisdictionDetail.test.tsx
    })
  })

  it('shows the detail modal with round status after an audit starts', async () => {
    const expectedCalls = [
      ...getDefaultExpectedCalls(),
      jaApiCalls.getBallotManifestFile(manifestMocks.processed),
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.oneComplete,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByRole('heading', {
        name: 'Current Audit Round',
      })

      // Tested further in JurisdictionDetail.test.tsx
    })
  })

  it('shows status for ballot manifest and batch tallies for batch comparison audits', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.twoManifestsOneTallies,
        auditSettings: auditSettingsMocks.batchComparisonAll,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

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
    })
  })

  it('renders progress map with jurisdiction upload status', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        jurisdictions: jurisdictionMocks.uploadingWithAlabamaJurisdictions,
        auditSettings: auditSettingsMocks.batchComparisonAll,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(container.querySelectorAll('.county.gray').length).toBe(1) // not logged in
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
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions: jurisdictionMocks.allCompleteWithAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(container.querySelectorAll('.county.success').length).toBe(3) // all completed
    })
  })

  it('renders progress map with 2 matched & completed jurisdictions', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions:
          jurisdictionMocks.allCompleteWithTwoMatchedAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(container.querySelectorAll('.county.success').length).toBe(2) // all completed

      // should including showing map label
      expect(screen.queryAllByText('Complete').length).toBe(4)
    })
  })

  it('does not render progress map with 1 matched & completed jurisdictions', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        // jurisdiction name also contains "County" name
        jurisdictions:
          jurisdictionMocks.allCompleteWithOneMatchedAlabamaJurisdictions,
        round: roundMocks.singleIncomplete[0],
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      // should not show map label
      expect(screen.queryAllByText('Complete').length).toBe(3) // all completed
    })
  })
})
