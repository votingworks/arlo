import React from 'react'
import { waitFor, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import { toast } from 'react-toastify'
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

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  return function mockJsPDF() {
    return {
      ...new jsPDF({ format: 'letter' }),
      save: mockSavePDF,
    }
  }
})

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
    await withMockFetch(expectedCalls, async () => {
      renderView({
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
        round: roundMocks.incomplete,
      })

      await screen.findByRole('button', {
        name: /Download Aggregated Batch Retrieval List/,
      })

      userEvent.click(
        await screen.findByRole('button', {
          name: /Download Batch Tally Sheets/,
        })
      )
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith('Batch Tally Sheets.pdf', {
          returnPromise: true,
        })
      )

      screen.getByRole('table') // Tested in BatchRoundDataEntry.test.tsx
    })
  })

  it('handles failures to generate batch tally sheets PDF', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
    ]
    mockSavePDF.mockImplementationOnce(() => Promise.reject(new Error('Whoa!')))
    await withMockFetch(expectedCalls, async () => {
      renderView({
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
        round: roundMocks.incomplete,
      })

      userEvent.click(
        await screen.findByRole('button', {
          name: /Download Batch Tally Sheets/,
        })
      )
      await waitFor(() => expect(toast.error).toHaveBeenCalledTimes(1))
      await waitFor(() =>
        expect(Sentry.captureException).toHaveBeenCalledTimes(1)
      )
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
