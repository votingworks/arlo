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
import { jaApiCalls, aaApiCalls } from '../_mocks'
import { dummyBallots } from '../../DataEntry/_mocks'
import * as utilities from '../../utilities'

jest.mock('react-router', () => ({
  useParams: jest.fn().mockReturnValue({ electionId: '1' }),
}))

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

describe('Progress screen', () => {
  afterAll(() => jest.restoreAllMocks())

  it('shows ballot manifest upload status', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneManifest}
          auditSettings={auditSettings.all}
          round={null}
        />
      )

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
      expect(row1[1]).toHaveTextContent('Manifest upload failed')
      expect(row1[2]).toBeEmpty()
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expect(row2[1]).toHaveTextContent('No manifest uploaded')
      expect(row2[2]).toBeEmpty()
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expect(row3[1]).toHaveTextContent('Manifest uploaded')
      expect(row3[2]).toHaveTextContent('2,117')

      const footers = within(rows[4]).getAllByRole('cell')
      expect(footers[0]).toHaveTextContent('Total')
      expect(footers[1]).toHaveTextContent('1/3 complete')
      expect(footers[2]).toHaveTextContent('2,117')
    })
  })

  it('shows round status', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      expect(row1[1]).toHaveTextContent('In progress')
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('4')
      expect(row1[4]).toHaveTextContent('6')
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[0]).toHaveTextContent('Jurisdiction 2')
      expect(row2[1]).toHaveTextContent('Not started')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('0')
      expect(row2[4]).toHaveTextContent('0')
      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3[0]).toHaveTextContent('Jurisdiction 3')
      expect(row3[1]).toHaveTextContent('Complete')
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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.twoManifestsOneTallies}
          auditSettings={auditSettings.batchComparisonAll}
          round={null}
        />
      )

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
      expect(row1[2]).toBeEmpty()
      expect(row1[3]).toBeEmpty()
      expect(row1[4]).toBeEmpty()
      // Jurisdiction 2 - manifest success, no tallies
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('10')
      expect(row2[4]).toBeEmpty()
      // Jurisdiction 3 - manifest success, tallies success
      const row3 = within(rows[3]).getAllByRole('cell')
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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.allManifestsSomeCVRs}
          auditSettings={auditSettings.ballotComparisonAll}
          round={null}
        />
      )

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
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toBeEmpty()
      // Jurisdiction 2 - manifest success, CVR success
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('10')
      // Jurisdiction 3 - manifest success, no CVR
      const row3 = within(rows[3]).getAllByRole('cell')
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
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.hybridTwoManifestsOneCvr}
          auditSettings={auditSettings.hybridAll}
          round={null}
        />
      )

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
      expect(row1[2]).toHaveTextContent('2,117')
      expect(row1[3]).toHaveTextContent('117')
      expect(row1[4]).toHaveTextContent('2,000')
      expect(row1[5]).toBeEmpty()
      // Jurisdiction 2 - manifest success, CVR success
      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2[2]).toHaveTextContent('2,117')
      expect(row2[3]).toHaveTextContent('1,117')
      expect(row2[4]).toHaveTextContent('1,000')
      expect(row2[5]).toHaveTextContent('10')

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.batchComparisonAll}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneManifest}
          auditSettings={auditSettings.all}
          round={null}
        />
      )

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      const filter = screen.getByPlaceholderText(
        'Filter by jurisdiction name...'
      )
      await userEvent.type(filter, '1')
      expect(screen.getAllByRole('row')).toHaveLength(1 + 2) // includes headers and footers
      screen.getByRole('cell', { name: 'Jurisdiction 1' })

      userEvent.clear(filter)
      await userEvent.type(filter, 'Jurisdiction')
      expect(screen.getAllByRole('row')).toHaveLength(
        jurisdictionMocks.oneManifest.length + 2
      )
    })
  })

  it('sorts', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { rerender, container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneManifest}
          auditSettings={auditSettings.all}
          round={null}
        />
      )

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
  })

  it('shows the detail modal before the audit starts', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneManifest}
          auditSettings={auditSettings.all}
          round={null}
        />
      )

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
      userEvent.click(screen.queryAllByText('Manifest uploaded')[1])
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
      userEvent.click(screen.queryAllByText('No manifest uploaded')[1])
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

  it('shows the detail modal with JA file download buttons after the audit starts', async () => {
    jest.setTimeout(10000)
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
      jaApiCalls.getBallots(dummyBallots.ballots),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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

      window.open = jest.fn()
      userEvent.click(
        within(modal).getByRole('button', {
          name: /Download Aggregated Ballot Retrieval List/,
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

  it('shows a message in the detail modal when no ballots sampled', async () => {
    const expectedCalls = [
      aaApiCalls.getMapData,
      jaApiCalls.getAuditBoards(auditBoardMocks.unfinished),
      jaApiCalls.getBallotCount([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

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
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.twoManifestsOneTallies}
          auditSettings={auditSettings.batchComparisonAll}
          round={null}
        />
      )

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

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
      jaApiCalls.getBatches([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneComplete}
          auditSettings={auditSettings.batchComparisonAll}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })

      userEvent.click(screen.getByRole('button', { name: 'Jurisdiction 1' }))
      const modal = screen
        .getByRole('heading', { name: 'Jurisdiction 1' })
        .closest('div.bp3-dialog')! as HTMLElement
      await within(modal).findByText('No batches sampled')
    })
  })

  it('renders progress map with jurisdictions filled', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <Progress
          jurisdictions={jurisdictionMocks.oneCompleteWithAlbamaJurisdictions}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })
      expect(container.querySelectorAll('.county.success').length).toBe(1) // completed
      expect(container.querySelectorAll('.county.progress').length).toBe(1) // in-progress
      expect(container.querySelectorAll('.county.gray').length).toBe(1) // not started
    })
  })

  it('renders progress map with all completed jurisdictions', async () => {
    const expectedCalls = [aaApiCalls.getMapData]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        // jurisdiction name also contains "County" name
        <Progress
          jurisdictions={jurisdictionMocks.allCompleteWithAlbamaJurisdictions}
          auditSettings={auditSettings.all}
          round={roundMocks.singleIncomplete[0]}
        />
      )

      expect(container.querySelectorAll('.d3-component').length).toBe(1)

      await waitFor(() => {
        expect(container.querySelectorAll('.bp3-spinner').length).toBe(0)
      })
      expect(container.querySelectorAll('.county.success').length).toBe(3) // all completed
    })
  })
})
