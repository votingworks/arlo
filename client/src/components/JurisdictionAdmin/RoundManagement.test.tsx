import React from 'react'
import { screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import {
  roundMocks,
  batchesMocks,
  batchResultsMocks,
  INullResultValues,
  fullHandTallyBatchResultMock,
} from './_mocks'
import { IBatch } from './useBatchResults'
import {
  jaApiCalls,
  auditSettings,
  auditBoardMocks,
  contestMocks,
} from '../_mocks'
import { IAuditSettings } from '../useAuditSettings'
import { IFullHandTallyBatchResults } from './useFullHandTallyResults'
import RoundManagement, { IRoundManagementProps } from './RoundManagement'
import {
  renderWithRouter,
  withMockFetch,
  createQueryClient,
} from '../testUtilities'
import AuthDataProvider from '../UserContext'
import { dummyBallots } from '../AuditBoard/_mocks'
import { IContest } from '../../types'

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

const renderView = (props: IRoundManagementProps) =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <AuthDataProvider>
        <Route
          path="/election/:electionId/jurisdiction/:jurisdictionId"
          render={routeProps => <RoundManagement {...routeProps} {...props} />}
        />
      </AuthDataProvider>
    </QueryClientProvider>,
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

  it('renders audit board setup for ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.incomplete,
        auditBoards: [],
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Set Up Audit Boards')
      screen.getByText('Ballots to audit: 27')
      // TODO test this form
      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })

  it('renders message when audit complete', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.complete,
        auditBoards: auditBoardMocks.signedOff,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Audit Complete')
      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })

  it('renders audit board progress for online ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByRole('heading', { name: 'Prepare Ballots' })
      screen.getByText('Ballots to audit: 27')
      // TODO test these buttons
      screen.getByRole('button', { name: /Download Ballot Retrieval List/ })
      screen.getByRole('button', { name: /Download Placeholder Sheets/ })
      screen.getByRole('button', { name: /Download Ballot Labels/ })
      screen.getByRole('button', { name: /Download Audit Board Credentials/ })

      screen.getByRole('heading', { name: 'Audit Board Progress' })
      screen.getByText('Audit Board #01: 0 of 30 ballots audited')
      // Tested further in RoundProgress.test.tsx

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })

  it('renders tally entry form for offline ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.offlineAll),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(batchResultsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByRole('heading', { name: 'Prepare Ballots' })
      screen.getByText('Ballots to audit: 27')
      // TODO test these buttons
      screen.getByRole('button', { name: /Download Ballot Retrieval List/ })
      screen.getByRole('button', { name: /Download Placeholder Sheets/ })
      screen.getByRole('button', { name: /Download Ballot Labels/ })

      await screen.findByRole('heading', { name: 'Enter Tallies' })
      screen.getByRole('heading', { name: 'Contest 1' })
      // Tested further in RoundDataEntry.test.tsx

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })

  it('renders batch audit 3-step flow', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        auditBoards: [],
        createAuditBoards: jest.fn(),
        round: roundMocks.incomplete,
      })

      await screen.findByRole('heading', { name: 'Prepare Batches' })
      // Tested further in BatchRoundSteps.test.tsx

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
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
      await screen.findByRole('heading', { name: 'No ballots to audit' })
      screen.getByText(
        'Your jurisdiction has not been assigned any ballots to audit in this round.'
      )

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
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
        auditBoards: [],
        createAuditBoards: jest.fn(),
      })
      await screen.findByRole('heading', { name: 'No ballots to audit' })
      screen.getByText(
        'Your jurisdiction has not been assigned any ballots to audit in this round.'
      )

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
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

      screen.getByText(/Jurisdiction One/)
      screen.getByText(/audit one/)
    })
  })
})
