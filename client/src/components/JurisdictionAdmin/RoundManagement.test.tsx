import React from 'react'
import ReactPDF, { BlobProvider, Page } from '@react-pdf/renderer'
import { toast } from 'react-toastify'
import { screen, within } from '@testing-library/react'
import { Route } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import * as Sentry from '@sentry/react'
import {
  roundMocks,
  batchesMocks,
  batchResultsMocks,
  INullResultValues,
  fullHandTallyBatchResultMock,
} from './_mocks'
import { IBatch } from './useBatchResults'
import { jaApiCalls } from '../_mocks'
import { IAuditSettings } from '../useAuditSettings'
import { IFullHandTallyBatchResults } from './useFullHandTallyResults'
import RoundManagement, { IRoundManagementProps } from './RoundManagement'
import { renderWithRouter, withMockFetch } from '../testUtilities'
import { queryClient } from '../../App'
import AuthDataProvider from '../UserContext'
import { dummyBallots } from '../AuditBoard/_mocks'
import { IContest } from '../../types'
import {
  auditSettings,
  auditBoardMocks,
  contestMocks,
} from '../AuditAdmin/useSetupMenuItems/_mocks'

jest.mock('@react-pdf/renderer', () => ({
  ...jest.requireActual('@react-pdf/renderer'),

  // Mock @react-pdf/renderer to generate HTML instead of PDF content for easier testing
  Document: jest.fn(({ children }) => <div>{children}</div>),
  Page: jest.fn(({ children }) => <div>{children}</div>),
  Text: jest.fn(({ children }) => <div>{children}</div>),
  View: jest.fn(({ children }) => <div>{children}</div>),

  // Let individual tests mock BlobProvider as necessary
  BlobProvider: jest.fn(() => null),
}))

jest.mock('react-toastify', () => ({
  toast: {
    error: jest.fn(),
  },
}))

jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
}))

const renderView = (props: IRoundManagementProps) =>
  renderWithRouter(
    <Route
      path="/election/:electionId/jurisdiction/:jurisdictionId"
      render={routeProps => (
        <QueryClientProvider client={queryClient}>
          <AuthDataProvider>
            <RoundManagement {...routeProps} {...props} />
          </AuthDataProvider>
        </QueryClientProvider>
      )}
    />,
    {
      route: '/election/1/jurisdiction/jurisdiction-id-1',
    }
  )

const apiCalls = {
  getBallotCount: jaApiCalls.getBallotCount(dummyBallots.ballots),
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/settings',
    response,
  }),
  getJAContests: (response: { contests: IContest[] }) => ({
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/contest`,
    response,
  }),
  getResults: (response: INullResultValues) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/results',
    response,
  }),
  getBatches: (response: { batches: IBatch[] }) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches',
    response,
  }),
  getFullHandTallyBatchResults: (response: IFullHandTallyBatchResults) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/full-hand-tally/batch',
    response,
  }),
}

describe('RoundManagement', () => {
  beforeEach(() => {
    // Clear mock call counts, etc.
    jest.clearAllMocks()

    // Reset the BlobProvider mock's implementation since some tests override the default mock
    // implementation
    ;(BlobProvider as jest.Mock).mockImplementation(() => null)
  })

  it('renders audit setup with batch audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches(batchesMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: [],
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Round 1 Audit Board Setup')
      screen.getByText(/Batches to audit: 3/)
      screen.getByText(/Total ballots in batches: 300/)
      expect(container).toMatchSnapshot()
    })
  })

  it('renders audit setup with ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: [],
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Round 1 Audit Board Setup')
      screen.getByText('Ballots to audit: 27')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders complete view', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.complete,
        auditBoards: auditBoardMocks.signedOff,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Congratulations! Your Risk-Limiting Audit is now complete.'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('renders links & progress with online ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Download Aggregated Ballot Retrieval List')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders links & data entry with offline ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.offlineAll),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(batchResultsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Download Aggregated Ballot Retrieval List')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders links & data entry with batch audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
    ]
    ;(BlobProvider as jest.Mock).mockImplementation(
      ({ children, document }: ReactPDF.BlobProviderProps) => {
        return (
          <>
            {children({
              blob: null,
              error: null,
              loading: false,
              url: 'blob:http://blob-url',
            })}
            {/* BlobProvider doesn't normally render the document in the DOM, but we do so here to
              facilitate testing */}
            <div data-testid="pdf">{document}</div>
          </>
        )
      }
    )

    await withMockFetch(expectedCalls, async () => {
      renderView({
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
        round: roundMocks.incomplete,
      })
      await screen.findByRole('button', {
        name: /Download Aggregated Batch Retrieval List/,
      })
      const downloadBatchTallySheetsButton = screen.getByRole('button', {
        name: /Download Batch Tally Sheets/,
      })
      expect(downloadBatchTallySheetsButton).toHaveAttribute(
        'href',
        'blob:http://blob-url'
      )

      // Expect a @react-pdf/renderer Page per batch (note that a Page can span multiple actual
      // pages). Page contents are further tested in BatchTallySheet.test.tsx
      expect(Page).toHaveBeenCalledTimes(3)
      const pdf = screen.getByTestId('pdf')
      expect(
        within(pdf).queryAllByText('Audit Board Batch Tally Sheet')
      ).toHaveLength(3)
      await within(pdf).findByText('Batch One')
      await within(pdf).findByText('Batch Two')
      await within(pdf).findByText('Batch Three')
      expect(within(pdf).queryAllByText('Candidates/Choices')).toHaveLength(3)
      expect(within(pdf).queryAllByText('Enter Stack Totals')).toHaveLength(3)
      expect(within(pdf).queryAllByText('Choice One')).toHaveLength(3)
      expect(within(pdf).queryAllByText('Choice Two')).toHaveLength(3)

      screen.getByRole('table') // Tested in BatchRoundDataEntry.test.tsx
    })
  })

  it('handles failures to generate batch tally sheets PDF whoa', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
    ]
    const error = new Error('PDF generation failed')
    ;(BlobProvider as jest.Mock).mockImplementation(
      ({ children }: ReactPDF.BlobProviderProps) => {
        return children({
          blob: null,
          error,
          loading: false,
          url: null,
        })
      }
    )

    await withMockFetch(expectedCalls, async () => {
      renderView({
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
        round: roundMocks.incomplete,
      })
      await screen.findByRole('button', {
        name: /Download Batch Tally Sheets/,
      })
      const downloadBatchTallySheetsButton = screen.getByRole('button', {
        name: /Download Batch Tally Sheets/,
      })
      expect(downloadBatchTallySheetsButton).not.toHaveAttribute('href')
      expect(toast.error).toHaveBeenCalledTimes(1)
      expect(Sentry.captureException).toHaveBeenCalledTimes(1)
    })
  })

  it('shows a message when no ballots assigned', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      jaApiCalls.getBallotCount([]),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Your jurisdiction has not been assigned any ballots to audit in this round.'
      )
    })
  })

  it('shows a message when no batches assigned', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches({ batches: [] }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Your jurisdiction has not been assigned any ballots to audit in this round.'
      )
    })
  })

  it('shows full hand tally data entry when all ballots sampled', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.offlineAll),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getFullHandTallyBatchResults(fullHandTallyBatchResultMock.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.fullHandTallyIncomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Please audit all of the ballots in your jurisdiction (100 ballots)'
      )
      screen.getByText('No batches added. Add your first batch below.')
    })
  })
})
