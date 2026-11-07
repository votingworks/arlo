import { afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import { Route } from 'react-router-dom'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
  readBlobAsText,
} from '../../testUtilities'
import {
  aaApiCalls,
  jaApiCalls,
  jurisdictionMocks,
  auditSettingsMocks,
  roundMocks,
  auditBoardMocks,
  manifestMocks,
  talliesMocks,
  contestMocks,
  lastLoginByJurisdictionMocks,
} from '../../_mocks'
import Progress, { IProgressProps } from './Progress'
import {
  BatchContestDecision,
  BatchDiscrepancyStatus,
  BatchDiscrepanciesByJurisdiction,
  IBatchDiscrepancies,
} from '../../useJurisdictions'
import { dummyBallots } from '../../AuditBoard/_mocks'
import copy from 'copy-to-clipboard'
import * as utilities from '../../utilities'
import { ExtendedIntent } from '../../Atoms/StatusTag'

vi.mock(import('copy-to-clipboard'), async importActual => ({
  ...(await importActual()),
  default: vi.fn(() => true),
}))

const mockSavePDF = vi.hoisted(() => vi.fn())
vi.mock(import('jspdf'), async importActual => {
  const { default: mockJsPDFModule } = await import('../../mockJsPDF')
  return mockJsPDFModule(await importActual(), mockSavePDF)
})
window.URL.createObjectURL = vi.fn()
window.open = vi.fn()

const expectStatusTag = (
  cell: HTMLElement,
  status: string,
  intent: ExtendedIntent
) => {
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
            jurisdictions={props.jurisdictions ?? jurisdictionMocks.oneManifest}
            auditSettings={auditSettingsMocks.all}
            contests={contestMocks.one}
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
    vi.clearAllMocks()
  })

  afterAll(() => vi.restoreAllMocks())

  function getDefaultExpectedCalls() {
    return [aaApiCalls.getLastLoginByJurisdiction(), aaApiCalls.getMapData]
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
      userEvent.hover(within(row2[1]).getByText('Logged in'))
      await screen.findByText(
        `ja-2@example.com at ${lastLoginByJurisdictionMocks.allLogins['jurisdiction-id-2'].timestamp}`
      )
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

  it('shows not-logged-in status when no logins exist and audit has not started', async () => {
    const expectedCalls = [
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
    ]
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
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expectStatusTag(row2[1], 'Not logged in', 'none')
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

  it('sorts difference from expected ballots with discrepancies first, then zeros, then empty rows', async () => {
    const expectedCalls = getDefaultExpectedCalls()
    await withMockFetch(expectedCalls, async () => {
      const numBallots =
        jurisdictionMocks.allManifests[0].ballotManifest!.numBallots!
      render({
        jurisdictions: [
          {
            ...jurisdictionMocks.allManifests[0],
            name: 'Zero',
            expectedBallotManifestNumBallots: numBallots,
          },
          {
            ...jurisdictionMocks.allManifests[1],
            name: 'Surplus',
            expectedBallotManifestNumBallots: numBallots - 10,
          },
          {
            ...jurisdictionMocks.allManifests[2],
            name: 'Deficit',
            expectedBallotManifestNumBallots: numBallots + 20,
          },
          {
            ...jurisdictionMocks.noManifests[0],
            name: 'No Manifest',
            expectedBallotManifestNumBallots: 30,
          },
          {
            ...jurisdictionMocks.allManifests[1],
            name: 'No Expected',
            expectedBallotManifestNumBallots: null,
          },
        ],
      })

      await screen.findByRole('heading', { name: 'Audit Progress' })

      const differenceHeader = screen.getByRole('columnheader', {
        name: 'Difference From Expected Ballots',
      })

      const expectRowOrder = (discrepancyRows: [string, string][]) => {
        const rows = screen.getAllByRole('row')
        discrepancyRows.forEach(([name, difference], i) => {
          const cells = within(rows[i + 1]).getAllByRole('cell')
          expect(cells[0]).toHaveTextContent(name)
          expect(cells[4]).toHaveTextContent(difference)
        })
        // The two empty rows tie, so their relative order isn't guaranteed
        const emptyRows = [4, 5].map(i => within(rows[i]).getAllByRole('cell'))
        expect(emptyRows.map(cells => cells[0].textContent).sort()).toEqual([
          'No Expected',
          'No Manifest',
        ])
        emptyRows.forEach(cells => expect(cells[4]).toBeEmptyDOMElement())
      }

      // Ascending: discrepancies in signed order, then zeros, then empty rows
      userEvent.click(differenceHeader)
      expectRowOrder([
        ['Deficit', '-20'],
        ['Surplus', '10'],
        ['Zero', '0'],
      ])

      // Descending: discrepancies flip, zeros and empty rows stay at the bottom
      userEvent.click(differenceHeader)
      expectRowOrder([
        ['Surplus', '10'],
        ['Deficit', '-20'],
        ['Zero', '0'],
      ])
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
      expectStatusTag(row1[1], 'In progress', 'in-progress')
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
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
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
      expect(row3[3].querySelector('.bp3-icon-flag')).toBeInTheDocument()
      expect(row3[4]).toHaveTextContent('30')
      expect(row3[5]).toHaveTextContent('0')

      const reviewDiscrepanciesButton = screen.getByRole('button', {
        name: /Review 2/,
      })
      userEvent.click(reviewDiscrepanciesButton)
      await waitFor(() => {
        screen.getByText('Jurisdiction 2 Review')
      })
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 2 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('ballot1')
      within(dialog).getByRole('heading', { level: 6, name: /Contest 1/ })

      const discrepancyTableHeaders =
        within(dialog).getAllByRole('columnheader')
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
    })
  })

  it('shows round and discrepancy status for batch comparison', async () => {
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({
        [jurisdictionMocks.oneComplete[2].id]: {
          notes: [],
          batches: {
            'batch-id-1': {
              name: 'batch1',
              isExtra: false,
              discrepancies: {
                [contestMocks.one[0].id]: {
                  reportedVotes: { [contestMocks.one[0].choices[0].id]: 5 },
                  auditedVotes: { [contestMocks.one[0].choices[0].id]: 6 },
                  changeInMargin: 1,
                  numBallots: 100,
                  status: 'NEEDS_REVIEW',
                },
              },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests(
        [contestMocks.one[0]],
        jurisdictionMocks.oneComplete[2].id
      ),
      {
        url: `/api/election/1/jurisdiction/${jurisdictionMocks.oneComplete[2].id}/round/round-1/batches/finalize`,
        options: { method: 'DELETE' },
        response: { status: 'ok' },
      },
      aaApiCalls.getDiscrepancies({
        [jurisdictionMocks.oneComplete[2].id]: {
          notes: [],
          batches: {
            'batch-id-1': {
              name: 'batch1',
              isExtra: false,
              discrepancies: {
                [contestMocks.one[0].id]: {
                  reportedVotes: { [contestMocks.one[0].choices[0].id]: 5 },
                  auditedVotes: { [contestMocks.one[0].choices[0].id]: 6 },
                  changeInMargin: 1,
                  numBallots: 100,
                  status: 'NEEDS_REVIEW',
                },
              },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
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
      expect(headers).toHaveLength(7)
      expect(headers[0]).toHaveTextContent('Jurisdiction')
      expect(headers[1]).toHaveTextContent('Status')
      expect(headers[2]).toHaveTextContent('Ballots in Manifest')
      expect(headers[3]).toHaveTextContent('Change in Margin')
      expect(headers[4]).toHaveTextContent('Batches Audited')
      expect(headers[5]).toHaveTextContent('Batches Remaining')
      expect(headers[6]).toHaveTextContent('Last Tally Update')

      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(jurisdictionMocks.oneComplete.length + 2) // includes headers and footers
      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[0]).toHaveTextContent('Jurisdiction 1')
      expectStatusTag(row1[1], 'In progress', 'in-progress')
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
      expectStatusTag(row3[1], 'Needs Review', 'danger')
      expect(row3[2]).toHaveTextContent('2,117')
      expect(row3[3]).toHaveTextContent('Review 1')
      expect(row3[3].querySelector('.bp3-icon-flag')).toBeInTheDocument()
      expect(row3[4]).toHaveTextContent('30')
      expect(row3[5]).toHaveTextContent('0')
      // No jurisdiction sampled extra batches, so there's nothing to exclude
      expect(
        screen.queryByRole('checkbox', { name: 'Exclude extra batches' })
      ).not.toBeInTheDocument()

      const reviewDiscrepanciesButton = screen.getByRole('button', {
        name: /Review 1/,
      })
      userEvent.click(reviewDiscrepanciesButton)
      await waitFor(() => {
        screen.getByText('Jurisdiction 3 Review')
      })
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 3 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Jurisdiction Admins')
      within(dialog).getByText('jurisdiction-3@example.com')
      within(dialog).getByText('jurisdiction-3-deputy@example.com')
      const copyEmailButtons = within(dialog).getAllByRole('button', {
        name: 'Copy email',
      })
      expect(copyEmailButtons).toHaveLength(2)
      userEvent.click(copyEmailButtons[1])
      expect(copy).toHaveBeenCalledWith('jurisdiction-3-deputy@example.com', {
        format: 'text/plain',
      })
      within(dialog).getByText('batch1')
      expectStatusTag(
        within(dialog).getByRole('heading', { level: 6, name: /Contest 1/ }),
        'Needs Review',
        'danger'
      )
      userEvent.click(
        within(dialog).getByRole('button', { name: 'Copy batch name' })
      )
      expect(copy).toHaveBeenCalledWith('batch1', { format: 'text/plain' })
      userEvent.click(
        within(dialog).getByRole('button', { name: 'Copy contest name' })
      )
      expect(copy).toHaveBeenCalledWith('Contest 1', { format: 'text/plain' })
      within(dialog).getByText('Choice One 5')
      within(dialog).getByText('Choice One 6')
      userEvent.click(
        within(dialog).getByRole('button', { name: 'Copy audited votes' })
      )
      expect(copy).toHaveBeenCalledWith('Choice One 6', {
        format: 'text/plain',
      })
      within(dialog).getByText('Ballots in batch')
      within(dialog).getByText('100')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('0/3 complete')
      expect(footers[2]).toHaveTextContent('6,351')
      expect(footers[3]).toHaveTextContent('1')
      expect(footers[4]).toHaveTextContent('34')
      expect(footers[5]).toHaveTextContent('26')

      userEvent.click(
        within(dialog).getByRole('button', { name: 'Unfinalize Tallies' })
      )
      await waitFor(() => {
        expect(
          within(dialog).getByRole('button', { name: 'Unfinalize Tallies' })
        ).toBeEnabled()
      })
    })
  })

  it("doesn't offer unfinalizing tallies or decisions after the round ends", async () => {
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({
        [jurisdictionMocks.oneComplete[2].id]: {
          notes: [],
          batches: {
            'batch-id-1': {
              name: 'batch1',
              isExtra: false,
              discrepancies: {
                [contestMocks.one[0].id]: {
                  reportedVotes: { [contestMocks.one[0].choices[0].id]: 5 },
                  auditedVotes: { [contestMocks.one[0].choices[0].id]: 6 },
                  changeInMargin: 1,
                  numBallots: 100,
                  status: 'NEEDS_REVIEW',
                },
              },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
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
        round: roundMocks.singleComplete[0],
      })
      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      userEvent.click(screen.getByRole('button', { name: /Review 1/ }))
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 3 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      expect(
        within(dialog).queryByRole('button', { name: 'Unfinalize Tallies' })
      ).not.toBeInTheDocument()
      expectStatusTag(
        within(dialog).getByRole('heading', { level: 6, name: /Contest 1/ }),
        'Needs Review',
        'danger'
      )
      expect(
        within(dialog).queryByRole('button', { name: 'Accept' })
      ).not.toBeInTheDocument()
    })
  })

  it('marks a batch contacted, accepts it, and sorts batches to review first', async () => {
    const contest = contestMocks.one[0]
    const [j1, j2, j3] = jurisdictionMocks.allComplete
    const batch = (
      name: string,
      status: BatchDiscrepancyStatus,
      changeInMargin: number
    ): IBatchDiscrepancies => ({
      name,
      isExtra: false,
      discrepancies: {
        [contest.id]: {
          reportedVotes: { [contest.choices[0].id]: 5 },
          auditedVotes: { [contest.choices[0].id]: 5 + changeInMargin },
          changeInMargin,
          numBallots: 100,
          status,
        },
      },
    })
    const discrepancies = (
      batch1Status: BatchDiscrepancyStatus,
      notes: string[]
    ): BatchDiscrepanciesByJurisdiction => ({
      [j1.id]: {
        notes: notes.map((text, i) => ({
          createdAt: `2026-11-06T15:0${i}:00+00:00`,
          text,
        })),
        batches: {
          'batch-id-1': batch('batch1', batch1Status, 1),
          'batch-id-2': batch('batch2', 'MATCHES', 0),
        },
      },
      [j2.id]: {
        notes: [],
        batches: { 'batch-id-3': batch('batch3', 'ACCEPTED', 5) },
      },
      [j3.id]: {
        notes: [],
        batches: { 'batch-id-4': batch('batch4', 'JURISDICTION_CONTACTED', 2) },
      },
    })
    const setStatus = (status: BatchContestDecision) => ({
      url: `/api/election/1/jurisdiction/${j1.id}/round/round-1/batches/batch-id-1/discrepancy-status`,
      options: {
        method: 'PUT',
        body: JSON.stringify({ contestId: contest.id, status }),
        headers: { 'Content-Type': 'application/json' },
      },
      response: { status: 'ok' },
    })
    const expectedCalls = [
      aaApiCalls.getDiscrepancies(discrepancies('NEEDS_REVIEW', [])),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests([contest], j1.id),
      setStatus('JURISDICTION_CONTACTED'),
      aaApiCalls.getDiscrepancies(
        discrepancies('JURISDICTION_CONTACTED', [
          'Marked batch1 for Contest 1 contacted',
        ])
      ),
      setStatus('ACCEPTED'),
      aaApiCalls.getDiscrepancies(
        discrepancies('ACCEPTED', [
          'Marked batch1 for Contest 1 contacted',
          'Accepted batch1 for Contest 1',
        ])
      ),
      setStatus('NEEDS_REVIEW'),
      aaApiCalls.getDiscrepancies(
        discrepancies('NEEDS_REVIEW', [
          'Marked batch1 for Contest 1 contacted',
          'Accepted batch1 for Contest 1',
          'Marked batch1 for Contest 1 needs review',
        ])
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render({
        auditSettings: auditSettingsMocks.batchComparisonAll,
        jurisdictions: jurisdictionMocks.allComplete,
        round: roundMocks.singleIncomplete[0],
      })
      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      // A jurisdiction with a batch to review is flagged; one with nothing
      // left to review is checked off
      const column = (index: number) =>
        screen
          .getAllByRole('row')
          .slice(1, 4)
          .map(row => within(row).getAllByRole('cell')[index])
      const reviewCells = () => column(3)
      const reviewButtonTexts = () =>
        reviewCells().map(
          cell => cell.querySelector('.bp3-button-text')!.textContent
        )
      const statusCells = () => column(1)
      expect(reviewCells()[0]).toHaveTextContent('Review 1')
      expect(reviewCells()[0].querySelector('.bp3-icon-flag')).toHaveClass(
        'bp3-intent-danger'
      )
      expect(reviewCells()[1]).toHaveTextContent('Review 5')
      expect(
        reviewCells()[1].querySelector('.bp3-icon-tick-circle')
      ).toBeInTheDocument()
      expect(reviewCells()[2]).toHaveTextContent('Review 2')
      expect(reviewCells()[2].querySelector('.bp3-icon-flag')).toHaveClass(
        'bp3-intent-warning'
      )
      expectStatusTag(statusCells()[0], 'Needs Review', 'danger')
      expectStatusTag(statusCells()[1], 'Complete', 'success')
      expectStatusTag(statusCells()[2], 'Contacted', 'warning')
      const footer = () =>
        within(screen.getAllByRole('row')[4]).getAllByRole('cell')[1]
      expect(footer()).toHaveTextContent('1/3 complete')

      // Jurisdictions needing review sort first, then those contacted, in
      // both directions
      const header = screen.getByRole('columnheader', {
        name: 'Change in Margin',
      })
      userEvent.click(header)
      expect(reviewButtonTexts()).toEqual(['Review 1', 'Review 2', 'Review 5'])
      userEvent.click(header)
      expect(reviewButtonTexts()).toEqual(['Review 1', 'Review 2', 'Review 5'])
      userEvent.click(header)
      expect(reviewButtonTexts()).toEqual(['Review 1', 'Review 5', 'Review 2'])

      userEvent.click(within(reviewCells()[0]).getByRole('button'))
      const dialog = (
        await screen.findByRole('heading', { name: /Jurisdiction 1 Review/ })
      ).closest('.bp3-dialog')! as HTMLElement
      // Each batch's one contest, with the batch's status and decisions
      const contestHeading = (batchName: RegExp) =>
        within(
          within(dialog).getByRole('heading', { level: 5, name: batchName })
            .parentElement!
        ).getByRole('heading', { level: 6 })
      expectStatusTag(contestHeading(/batch1/), 'Needs Review', 'danger')
      expectStatusTag(contestHeading(/batch2/), 'Matches', 'success')
      expect(
        within(contestHeading(/batch2/)).queryByRole('button', {
          name: 'Accept',
        })
      ).not.toBeInTheDocument()

      userEvent.click(
        within(contestHeading(/batch1/)).getByRole('button', {
          name: 'Mark Contacted',
        })
      )
      await within(dialog).findByText('Marked batch1 for Contest 1 contacted')
      expectStatusTag(contestHeading(/batch1/), 'Contacted', 'warning')
      expect(
        within(contestHeading(/batch1/)).queryByRole('button', {
          name: 'Mark Contacted',
        })
      ).not.toBeInTheDocument()
      expect(reviewCells()[0].querySelector('.bp3-icon-flag')).toHaveClass(
        'bp3-intent-warning'
      )

      userEvent.click(
        within(contestHeading(/batch1/)).getByRole('button', {
          name: 'Accept',
        })
      )
      await within(dialog).findByText('Accepted batch1 for Contest 1')
      expectStatusTag(contestHeading(/batch1/), 'Accepted', 'success')
      expect(
        within(contestHeading(/batch1/)).queryByRole('button', {
          name: 'Accept',
        })
      ).not.toBeInTheDocument()
      expect(reviewCells()[0]).toHaveTextContent('Review 1')
      expect(
        reviewCells()[0].querySelector('.bp3-icon-tick-circle')
      ).toBeInTheDocument()
      expectStatusTag(statusCells()[0], 'Complete', 'success')
      expect(footer()).toHaveTextContent('2/3 complete')

      // Accepting can be undone
      userEvent.click(
        within(contestHeading(/batch1/)).getByRole('button', {
          name: 'Mark Needs Review',
        })
      )
      await within(dialog).findByText(
        'Marked batch1 for Contest 1 needs review'
      )
      expectStatusTag(contestHeading(/batch1/), 'Needs Review', 'danger')
      expect(reviewCells()[0].querySelector('.bp3-icon-flag')).toHaveClass(
        'bp3-intent-danger'
      )
      expectStatusTag(statusCells()[0], 'Needs Review', 'danger')
      expect(footer()).toHaveTextContent('1/3 complete')
    })
  })

  it('keeps a noted jurisdiction in review and takes notes', async () => {
    const [reTallying, , finalized] = jurisdictionMocks.oneComplete
    const note = {
      createdAt: '2026-11-05T15:00:00+00:00',
      text: 'Unfinalized tallies',
    }
    const newNote = {
      createdAt: '2026-11-05T16:00:00+00:00',
      text: 'JA is re-tallying Batch 1',
    }
    // A jurisdiction under review lists its audited batches with statuses
    const contest = contestMocks.one[0]
    const matchingBatch = {
      'batch-id-1': {
        name: 'batch1',
        isExtra: false,
        discrepancies: {
          [contest.id]: {
            reportedVotes: { [contest.choices[0].id]: 5 },
            auditedVotes: { [contest.choices[0].id]: 5 },
            changeInMargin: 0,
            numBallots: 100,
            status: 'MATCHES' as const,
          },
        },
      },
    }
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({
        [reTallying.id]: { notes: [note], batches: matchingBatch },
        [finalized.id]: { notes: [note], batches: matchingBatch },
      }),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests([contestMocks.one[0]], reTallying.id),
      {
        url: `/api/election/1/jurisdiction/${reTallying.id}/discrepancy-notes`,
        options: {
          method: 'POST',
          body: JSON.stringify({ text: newNote.text }),
          headers: { 'Content-Type': 'application/json' },
        },
        response: { status: 'ok' },
      },
      aaApiCalls.getDiscrepancies({
        [reTallying.id]: {
          notes: [note, newNote],
          batches: matchingBatch,
        },
        [finalized.id]: { notes: [note], batches: matchingBatch },
      }),
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

      const rows = screen.getAllByRole('row')
      expectStatusTag(
        within(rows[1]).getAllByRole('cell')[1],
        'Re-tallying',
        'in-progress'
      )
      // The icon's name is part of the button's accessible name
      const reTallyingReview = within(rows[1]).getByRole('button', {
        name: 'Review',
      })
      expect(
        within(rows[2]).queryByRole('button', { name: /Review/ })
      ).not.toBeInTheDocument()
      const finalizedReview = within(rows[3]).getByRole('button', {
        name: /Review/,
      })
      expect(
        finalizedReview.querySelector('.bp3-icon-tick-circle')
      ).toBeInTheDocument()

      userEvent.click(reTallyingReview)
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 1 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Notes')
      // Unfinalized to re-tally, though its one batch contest matched
      within(dialog).getByText('Re-tallying')
      within(dialog).getByText(note.text)
      within(dialog).getByText(new Date(note.createdAt).toLocaleString())
      const addNote = within(dialog).getByRole('button', { name: 'Add Note' })
      expect(addNote).toBeDisabled()
      userEvent.type(within(dialog).getByRole('textbox'), newNote.text)
      userEvent.click(addNote)
      await within(dialog).findByText(newNote.text)
      expect(within(dialog).getByRole('textbox')).toHaveValue('')
    })
  })

  it('excludes extra batches from batch comparison discrepancies', async () => {
    const jurisdiction = jurisdictionMocks.oneComplete[2] // Complete
    const contest = contestMocks.one[0]
    const contestDiscrepancy = {
      reportedVotes: { [contest.choices[0].id]: 5 },
      auditedVotes: { [contest.choices[0].id]: 6 },
      changeInMargin: 1,
      numBallots: 100,
      status: 'NEEDS_REVIEW' as const,
    }
    const expectedCalls = [
      aaApiCalls.getDiscrepancies({
        [jurisdiction.id]: {
          notes: [],
          batches: {
            'batch-id-1': {
              name: 'batch1',
              isExtra: false,
              discrepancies: { [contest.id]: contestDiscrepancy },
            },
            'batch-id-2': {
              name: 'batch2',
              isExtra: true,
              discrepancies: {
                [contest.id]: { ...contestDiscrepancy, changeInMargin: -1 },
              },
            },
          },
        },
      }),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
      jaApiCalls.getJurisdictionContests([contest], jurisdiction.id),
    ]
    // One of the complete jurisdiction's 30 batches is an extra that hasn't
    // been audited
    const jurisdictions = jurisdictionMocks.oneComplete.map(j =>
      j.id === jurisdiction.id
        ? {
            ...j,
            currentRoundStatus: {
              ...j.currentRoundStatus!,
              numSamplesAudited: 30,
              numUniqueAudited: 29,
              extras: {
                numSamples: 2,
                numSamplesAudited: 1,
                numUnique: 2,
                numUniqueAudited: 1,
              },
            },
          }
        : j
    )
    await withMockFetch(expectedCalls, async () => {
      const { container, history } = render({
        auditSettings: auditSettingsMocks.batchComparisonAll,
        jurisdictions,
        round: roundMocks.singleIncomplete[0],
      })
      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      const cells = () =>
        within(screen.getAllByRole('row')[3]).getAllByRole('cell')
      expect(cells()[4]).toHaveTextContent('29')
      expect(cells()[5]).toHaveTextContent('1')

      userEvent.click(screen.getByRole('button', { name: /Review 2/ }))
      const dialogWithExtras = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 3 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      expect(
        within(dialogWithExtras)
          .getAllByRole('heading', { level: 5 })
          .map(heading => heading.querySelector('span')!.textContent)
      ).toEqual(['batch1', '(Extra) batch2'])
      userEvent.click(
        within(dialogWithExtras).getByRole('button', { name: 'Close' })
      )
      await waitFor(() => {
        expect(dialogWithExtras).not.toBeInTheDocument()
      })

      // Excluding extra batches leaves the batches the audit math drew, in the
      // discrepancies and the counts, and sticks in the URL
      userEvent.click(
        screen.getByRole('checkbox', { name: 'Exclude extra batches' })
      )
      expect(history.location.search).toEqual('?excludeExtraBatches=true')
      expect(cells()[4]).toHaveTextContent('28')
      expect(cells()[5]).toHaveTextContent('0')
      userEvent.click(screen.getByRole('button', { name: /Review 1/ }))
      const dialog = (
        await screen.findByRole('heading', {
          name: /Jurisdiction 3 Review/,
        })
      ).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('batch1')
      expect(within(dialog).queryByText('batch2')).not.toBeInTheDocument()
      userEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
      await waitFor(() => {
        expect(dialog).not.toBeInTheDocument()
      })

      userEvent.click(
        screen.getByRole('checkbox', { name: 'Exclude extra batches' })
      )
      expect(history.location.search).toEqual('')
      screen.getByRole('button', { name: /Review 2/ })
    })
  })

  describe('contest select', () => {
    const jurisdiction = jurisdictionMocks.oneComplete[2] // Complete
    const noExtras = {
      numSamples: 0,
      numSamplesAudited: 0,
      numUnique: 0,
      numUniqueAudited: 0,
    }
    const contestA = contestMocks.two[0]
    // Contest B is only in the complete jurisdiction
    const contestB = {
      ...contestMocks.two[1],
      jurisdictionIds: [jurisdiction.id],
    }
    // The complete jurisdiction's numbers broken down by contest
    const jurisdictions = jurisdictionMocks.oneComplete.map(j =>
      j.id === jurisdiction.id
        ? {
            ...j,
            ballotManifest: {
              ...j.ballotManifest,
              numBallotsByContestId: {
                [contestA.id]: 1500,
                [contestB.id]: 600,
              },
            },
            currentRoundStatusByContestId: {
              [contestA.id]: {
                numSamples: 20,
                numSamplesAudited: 20,
                numUnique: 20,
                numUniqueAudited: 20,
                extras: noExtras,
              },
              [contestB.id]: {
                numSamples: 12,
                numSamplesAudited: 10,
                numUnique: 10,
                numUniqueAudited: 8,
                extras: noExtras,
              },
            },
          }
        : j
    )

    it('scopes a batch comparison table to the selected contest', async () => {
      const expectedCalls = [
        aaApiCalls.getDiscrepancies({}),
        aaApiCalls.getLastLoginByJurisdiction({
          response: lastLoginByJurisdictionMocks.noLogins,
        }),
        aaApiCalls.getMapData,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container, history } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions,
          contests: [contestA, contestB],
          round: roundMocks.singleIncomplete[0],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
        expect(screen.getAllByRole('row')).toHaveLength(5)

        // Only the jurisdictions in the contest are listed, with the contest's
        // ballots and unique batch counts
        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          contestB.id
        )
        expect(history.location.search).toEqual(`?contest=${contestB.id}`)
        const rows = screen.getAllByRole('row')
        expect(rows).toHaveLength(3) // header, row, footer
        const cells = within(rows[1]).getAllByRole('cell')
        expect(cells[0]).toHaveTextContent('Jurisdiction 3')
        expect(cells[2]).toHaveTextContent('600')
        expect(cells[4]).toHaveTextContent('8')
        expect(cells[5]).toHaveTextContent('2')
        const footers = within(rows[2]).getAllByRole('cell')
        expect(footers[2]).toHaveTextContent('600')
        expect(footers[4]).toHaveTextContent('8')
        expect(footers[5]).toHaveTextContent('2')

        // Counting every sampled batch instead of unique ones
        userEvent.click(
          screen.getByRole('checkbox', { name: /Count unique sampled/ })
        )
        expect(cells[4]).toHaveTextContent('10')
        expect(cells[5]).toHaveTextContent('2')

        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          ''
        )
        expect(history.location.search).toEqual('')
        expect(screen.getAllByRole('row')).toHaveLength(5)
      })
    })

    it("opens a jurisdiction's discrepancies on the selected contest", async () => {
      const discrepancy = (contest: typeof contestA) => ({
        reportedVotes: { [contest.choices[0].id]: 5 },
        auditedVotes: { [contest.choices[0].id]: 6 },
        changeInMargin: 1,
        numBallots: 100,
        status: 'NEEDS_REVIEW' as const,
      })
      const [reTallying, notStarted] = jurisdictionMocks.oneComplete
      // Contest C has no batches drawn in this jurisdiction; contest D does,
      // without discrepancies
      const contestC = {
        ...contestMocks.two[1],
        id: 'contest-id-3',
        name: 'Contest 3',
        jurisdictionIds: [jurisdiction.id],
      }
      const contestD = {
        ...contestMocks.two[1],
        id: 'contest-id-4',
        name: 'Contest 4',
        jurisdictionIds: [jurisdiction.id],
      }
      const oneSample = {
        numSamples: 1,
        numSamplesAudited: 1,
        numUnique: 1,
        numUniqueAudited: 1,
        extras: noExtras,
      }
      const jurisdictionsWithContestD = jurisdictions.map(j => {
        if (j.id === jurisdiction.id) {
          return {
            ...j,
            currentRoundStatusByContestId: {
              ...j.currentRoundStatusByContestId,
              [contestD.id]: {
                numSamples: 3,
                numSamplesAudited: 3,
                numUnique: 3,
                numUniqueAudited: 3,
                extras: noExtras,
              },
            },
          }
        }
        // The re-tallying jurisdiction's one batch is for contest B; the
        // not-started jurisdiction has nothing sampled for it
        if (j.id === reTallying.id) {
          return {
            ...j,
            currentRoundStatusByContestId: { [contestB.id]: oneSample },
          }
        }
        return j
      })
      const expectedCalls = [
        aaApiCalls.getDiscrepancies({
          [jurisdiction.id]: {
            notes: [],
            batches: {
              'batch-id-1': {
                name: 'batch1',
                isExtra: false,
                discrepancies: {
                  [contestA.id]: discrepancy(contestA),
                  [contestB.id]: {
                    ...discrepancy(contestB),
                    status: 'ACCEPTED',
                  },
                },
              },
              'batch-id-2': {
                name: 'batch2',
                isExtra: false,
                discrepancies: { [contestA.id]: discrepancy(contestA) },
              },
            },
          },
          // Unfinalized to re-tally, with contest B's one batch matching
          [reTallying.id]: {
            notes: [],
            batches: {
              'batch-id-3': {
                name: 'batch3',
                isExtra: false,
                discrepancies: {
                  [contestB.id]: {
                    ...discrepancy(contestB),
                    changeInMargin: 0,
                    status: 'MATCHES',
                  },
                },
              },
            },
          },
        }),
        aaApiCalls.getLastLoginByJurisdiction({
          response: lastLoginByJurisdictionMocks.noLogins,
        }),
        aaApiCalls.getMapData,
        jaApiCalls.getJurisdictionContests(
          [contestA, contestB, contestC, contestD],
          jurisdiction.id
        ),
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container, history } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions: jurisdictionsWithContestD,
          contests: [
            contestA,
            {
              ...contestB,
              jurisdictionIds: [reTallying.id, notStarted.id, jurisdiction.id],
            },
          ],
          round: roundMocks.singleIncomplete[0],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
        screen.getByRole('button', { name: /Review 3/ })
        // Across every contest the jurisdiction needs review; for a contest
        // whose batch contests are all accepted, it stands at Accepted. The
        // re-tallying jurisdiction says so in both views.
        const statusCell = (name: string) =>
          within(
            screen.getByRole('cell', { name }).closest('tr')!
          ).getAllByRole('cell')[1]
        expectStatusTag(statusCell('Jurisdiction 3'), 'Needs Review', 'danger')
        expectStatusTag(
          statusCell('Jurisdiction 1'),
          'Re-tallying',
          'in-progress'
        )

        // Only the selected contest's discrepancies are counted and shown
        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          contestB.id
        )
        expectStatusTag(statusCell('Jurisdiction 3'), 'Accepted', 'success')
        expectStatusTag(
          statusCell('Jurisdiction 1'),
          'Matches (Re-tallying)',
          'success'
        )
        expectStatusTag(statusCell('Jurisdiction 2'), 'No samples', 'success')
        userEvent.click(screen.getByRole('button', { name: /Review 1/ }))
        const dialog = (
          await screen.findByRole('heading', {
            name: /Jurisdiction 3 Review/,
          })
        ).closest('.bp3-dialog')! as HTMLElement
        const batchHeadings = () =>
          within(dialog)
            .queryAllByRole('heading', { level: 5 })
            .map(heading => heading.querySelector('span')!.textContent)
        const contestHeadings = () =>
          within(dialog)
            .getAllByRole('heading', { level: 6 })
            .map(heading => heading.querySelector('span')!.textContent)
        const dialogSelect = within(dialog).getByRole('combobox', {
          name: 'Contest',
        })
        expect(dialogSelect).toHaveValue(contestB.id)
        expect(batchHeadings()).toEqual(['batch1'])
        expect(contestHeadings()).toEqual(['Contest 2'])

        // The dialog's select only changes the dialog
        userEvent.selectOptions(dialogSelect, '')
        expect(batchHeadings()).toEqual(['batch1', 'batch2'])
        expect(contestHeadings()).toEqual([
          'Contest 1',
          'Contest 2',
          'Contest 1',
        ])
        userEvent.selectOptions(dialogSelect, contestA.id)
        expect(batchHeadings()).toEqual(['batch1', 'batch2'])
        expect(contestHeadings()).toEqual(['Contest 1', 'Contest 1'])
        userEvent.selectOptions(dialogSelect, contestC.id)
        expect(batchHeadings()).toEqual([])
        within(dialog).getByText('No batches sampled for this contest')
        userEvent.selectOptions(dialogSelect, contestD.id)
        expect(batchHeadings()).toEqual([])
        within(dialog).getByText('No discrepancies for this contest')
        expect(history.location.search).toEqual(`?contest=${contestB.id}`)
        screen.getByRole('button', { name: /Review 1/ })
      })
    })

    it('scopes a pre-round batch comparison table to the selected contest', async () => {
      // Jurisdiction 3 has processed both files, with its manifest and valid
      // voted ballots broken down by contest and an expected count for the
      // whole jurisdiction
      const preRoundJurisdictions = [
        ...jurisdictionMocks.twoManifestsOneTallies.slice(0, 2),
        {
          ...jurisdictionMocks.twoManifestsOneTallies[2],
          expectedBallotManifestNumBallots: 2000,
          ballotManifest: {
            ...manifestMocks.processed,
            numBallotsByContestId: { [contestA.id]: 2117, [contestB.id]: 600 },
          },
          batchTallies: {
            ...talliesMocks.processed,
            numBallotsByContestId: { [contestA.id]: 1400, [contestB.id]: 550 },
          },
        },
      ]
      const header = (name: string) =>
        screen.queryByRole('columnheader', { name })
      await withMockFetch(getDefaultExpectedCalls(), async () => {
        const { container } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions: preRoundJurisdictions,
          contests: [contestA, contestB],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
        expect(screen.getAllByRole('row')).toHaveLength(5)
        expect(header('Expected Ballots in Manifest')).toBeInTheDocument()
        expect(header('Difference From Expected Ballots')).toBeInTheDocument()
        expect(header('Valid Voted Ballots in Batches')).toBeInTheDocument()

        // With a contest selected: only its jurisdictions, its manifest and
        // valid voted ballots, and no comparison to the whole-jurisdiction
        // expected count
        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          contestB.id
        )
        let rows = screen.getAllByRole('row')
        expect(rows).toHaveLength(3) // header, row, footer
        expect(header('Expected Ballots in Manifest')).not.toBeInTheDocument()
        expect(
          header('Difference From Expected Ballots')
        ).not.toBeInTheDocument()
        expect(header('Valid Voted Ballots in Batches')).toBeInTheDocument()
        const cells = within(rows[1]).getAllByRole('cell')
        expect(cells[0]).toHaveTextContent('Jurisdiction 3')
        expect(cells[2]).toHaveTextContent('600')
        expect(cells[4]).toHaveTextContent('550')
        const footers = within(rows[2]).getAllByRole('cell')
        expect(footers[2]).toHaveTextContent('600')
        expect(footers[4]).toHaveTextContent('550')

        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          contestA.id
        )
        rows = screen.getAllByRole('row')
        expect(rows).toHaveLength(5)
        expect(header('Expected Ballots in Manifest')).not.toBeInTheDocument()
        const row3 = within(rows[3]).getAllByRole('cell')
        expect(row3[2]).toHaveTextContent('2,117')
        expect(row3[4]).toHaveTextContent('1,400')
      })
    })

    it('is only offered for a multi-contest batch comparison audit', async () => {
      const batchComparisonCalls = [
        aaApiCalls.getDiscrepancies({}),
        aaApiCalls.getLastLoginByJurisdiction({
          response: lastLoginByJurisdictionMocks.noLogins,
        }),
        aaApiCalls.getMapData,
      ]
      await withMockFetch(batchComparisonCalls, async () => {
        const { container } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions,
          contests: [contestA],
          round: roundMocks.singleIncomplete[0],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(
          screen.queryByRole('combobox', { name: 'Contest' })
        ).not.toBeInTheDocument()
      })
      await withMockFetch(getDefaultExpectedCalls(), async () => {
        const { container } = render({ contests: [contestA, contestB] })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(
          screen.queryByRole('combobox', { name: 'Contest' })
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('last tally update', () => {
    const lastTalliedAt: Record<string, string> = {
      'jurisdiction-id-1': '2026-11-09T14:14:00+00:00',
      'jurisdiction-id-3': '2026-11-08T09:05:00+00:00',
    }
    const jurisdictions = jurisdictionMocks.oneComplete.map(jurisdiction => ({
      ...jurisdiction,
      currentRoundStatus: jurisdiction.currentRoundStatus && {
        ...jurisdiction.currentRoundStatus,
        lastTalliedAt: lastTalliedAt[jurisdiction.id] ?? null,
      },
    }))
    const expectedCalls = () => [
      aaApiCalls.getDiscrepancies({}),
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
      aaApiCalls.getMapData,
    ]

    it('shows and sorts by when each jurisdiction last saved tallies', async () => {
      await withMockFetch(expectedCalls(), async () => {
        const { container } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions,
          round: roundMocks.singleIncomplete[0],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        const header = screen.getByRole('columnheader', {
          name: /Last Tally Update/,
        })
        const column = () =>
          screen
            .getAllByRole('row')
            .slice(1, -1)
            .map(row => within(row).getAllByRole('cell'))
            .map(cells => [cells[0].textContent, cells[6].textContent])
        expect(column()).toEqual([
          ['Jurisdiction 1', 'Nov 9, 2:14 PM'],
          ['Jurisdiction 2', ''],
          ['Jurisdiction 3', 'Nov 8, 9:05 AM'],
        ])

        // Oldest first, then newest first; a jurisdiction yet to save stays
        // at the bottom either way
        userEvent.click(header)
        expect(column().map(([name]) => name)).toEqual([
          'Jurisdiction 3',
          'Jurisdiction 1',
          'Jurisdiction 2',
        ])
        userEvent.click(header)
        expect(column().map(([name]) => name)).toEqual([
          'Jurisdiction 1',
          'Jurisdiction 3',
          'Jurisdiction 2',
        ])
      })
    })

    it('is hidden once the round ends', async () => {
      await withMockFetch(expectedCalls(), async () => {
        const { container } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions,
          round: roundMocks.singleComplete[0],
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        expect(
          screen.queryByRole('columnheader', { name: /Last Tally Update/ })
        ).not.toBeInTheDocument()
      })
    })

    it('keeps the upload statuses before the round starts', async () => {
      await withMockFetch(getDefaultExpectedCalls(), async () => {
        const { container } = render({
          auditSettings: auditSettingsMocks.batchComparisonAll,
          jurisdictions: jurisdictionMocks.twoManifestsOneTallies,
          contests: contestMocks.two,
        })
        await waitFor(() => {
          expect(container.querySelectorAll('.d3-component').length).toBe(1)
        })
        userEvent.selectOptions(
          screen.getByRole('combobox', { name: 'Contest' }),
          contestMocks.two[0].id
        )
        const rows = screen.getAllByRole('row')
        const statusCell = (row: HTMLElement) =>
          within(row).getAllByRole('cell')[1]
        expectStatusTag(statusCell(rows[1]), 'Manifest upload failed', 'danger')
        expectStatusTag(
          statusCell(rows[2]),
          '1/2 files uploaded',
          'in-progress'
        )
        expectStatusTag(statusCell(rows[3]), '2/2 files uploaded', 'success')
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
      expectStatusTag(row1[1], 'Manifest upload failed', 'danger')
      expect(row1[2]).toBeEmpty()
      expect(row1[3]).toBeEmpty()
      expect(row1[4]).toBeEmpty()
      // Jurisdiction 2 - manifest success, no tallies
      const row2 = within(rows[2]).getAllByRole('cell')
      expectStatusTag(row2[1], '1/2 files uploaded', 'in-progress')
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
      expectStatusTag(row1[1], '1/2 files uploaded', 'in-progress')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toBeEmpty()
      // Jurisdiction 2 - manifest success, CVR success
      const row2 = within(rows[2]).getAllByRole('cell')
      expectStatusTag(row2[1], '2/2 files uploaded', 'success')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('10')
      // Jurisdiction 3 - manifest success, no CVR
      const row3 = within(rows[3]).getAllByRole('cell')
      expectStatusTag(row3[1], '1/2 files uploaded', 'in-progress')
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
      expectStatusTag(row1[1], '1/2 files uploaded', 'in-progress')
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
      aaApiCalls.getLastLoginByJurisdiction(),
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
    const downloadFileMock = vi
      .spyOn(utilities, 'downloadFile')
      .mockResolvedValue(undefined)

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
      expect(await readBlobAsText(fileBlob)).toEqual(
        '"Jurisdiction","Status","Ballots in Manifest","Ballots Audited","Ballots Remaining"\n' +
          '"Jurisdiction 1","In progress","2,117","4","6"\n' +
          '"Jurisdiction 2","Logged in","2,117","0","20"\n' +
          '"Jurisdiction 3","Complete","2,117","30","0"\n' +
          '"Total","1/3 complete","6,351","34","26"'
      )

      downloadFileMock.mockRestore()
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

      const filter = screen.getByPlaceholderText('Filter by name...')
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

  it('sorts based on logged-in status when round status exists', async () => {
    const expectedCalls = [
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.oneLogin,
      }),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, history } = render({
        jurisdictions: jurisdictionMocks.noneStarted,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(history.location.search).toEqual('')

      // Toggle sorting by status
      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Status&dir=asc')
      })
      let rows = screen.getAllByRole('row')
      rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Not logged in')
      within(rows[2]).getByText('Logged in')
      within(rows[3]).getByText('Complete')
    })
  })

  it('sorts based on logged-in status when round has not started and there are 0 uploads', async () => {
    const expectedCalls = [
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.oneLogin,
      }),
      aaApiCalls.getMapData,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, history } = render({
        jurisdictions: jurisdictionMocks.noManifests,
      })

      await waitFor(() => {
        expect(container.querySelectorAll('.d3-component').length).toBe(1)
      })
      expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)

      expect(history.location.search).toEqual('')

      // Toggle sorting by status
      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      await waitFor(() => {
        expect(history.location.search).toEqual('?sort=Status&dir=asc')
      })
      let rows = screen.getAllByRole('row')
      rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Not logged in')
      within(rows[2]).getByText('Not logged in')
      within(rows[3]).getByText('Logged in')
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
      aaApiCalls.getLastLoginByJurisdiction({
        response: lastLoginByJurisdictionMocks.noLogins,
      }),
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
        jurisdictions: [
          {
            ...jurisdictionMocks.twoManifestsOneTallies[0],
            ballotManifest: manifestMocks.processed,
            batchTallies: talliesMocks.errored,
          },
          ...jurisdictionMocks.twoManifestsOneTallies.slice(1),
        ],
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
        'Tallies upload failed',
        'danger'
      )
      expectStatusTag(
        within(rows[2]).getAllByRole('cell')[1],
        '1/2 files uploaded',
        'in-progress'
      )
      expectStatusTag(
        within(rows[3]).getAllByRole('cell')[1],
        '2/2 files uploaded',
        'success'
      )

      userEvent.hover(within(rows[1]).getByText('Tallies upload failed'))
      await screen.findByText('Invalid CSV')

      // Toggle sorting by status
      const statusHeader = screen.getByRole('columnheader', {
        name: 'Status',
      })
      userEvent.click(statusHeader)
      rows = screen.getAllByRole('row')
      within(rows[1]).getByText('Tallies upload failed')

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
      expect(container.querySelectorAll('.county.progress-2').length).toBe(1) // in progress
      expect(container.querySelectorAll('.county.danger').length).toBe(1) // errored

      // Check that the county tooltip shows on hover
      userEvent.hover(container.querySelector('.county.progress-2')!)
      expect(container.querySelector('#tooltip')).toBeVisible()
      expect(container.querySelector('#tooltip')).toHaveTextContent('Geneva')
      userEvent.unhover(container.querySelector('.county.progress-2')!)
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
