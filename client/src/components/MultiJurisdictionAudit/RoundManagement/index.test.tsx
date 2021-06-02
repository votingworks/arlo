import React from 'react'
import { screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import { renderWithRouter, withMockFetch } from '../../testUtilities'
import RoundManagement, { IRoundManagementProps } from './index'
import {
  roundMocks,
  batchesMocks,
  batchResultsMocks,
  INullResultValues,
  offlineBatchMocks,
} from './_mocks'
import { dummyBallots } from '../../DataEntry/_mocks'
import {
  auditSettings,
  auditBoardMocks,
  contestMocks,
} from '../useSetupMenuItems/_mocks'
import { IContest } from '../../../types'
import { IBatch } from './useBatchResults'
import { jaApiCalls } from '../_mocks'
import AuthDataProvider from '../../UserContext'
import { IAuditSettings } from '../useAuditSettings'
import { IOfflineBatchResults } from './useOfflineBatchResults'

const renderView = (props: IRoundManagementProps) =>
  renderWithRouter(
    <Route
      path="/election/:electionId/jurisdiction/:jurisdictionId"
      render={routeProps => (
        <AuthDataProvider>
          <RoundManagement {...routeProps} {...props} />
        </AuthDataProvider>
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
  getBatchResults: (response: INullResultValues) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/results',
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
  getOfflineBatchResults: (response: IOfflineBatchResults) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/results/batch',
    response,
  }),
}

describe('RoundManagement', () => {
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
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatchResults(batchResultsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText('Download Aggregated Batch Retrieval List')
      expect(container).toMatchSnapshot()
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
        'Your jurisdiction has not been assigned any batches to audit in this round.'
      )
    })
  })

  it('shows offline batch results data entry when all ballots sampled', async () => {
    const expectedCalls = [
      apiCalls.getSettings(auditSettings.offlineAll),
      jaApiCalls.getUser,
      apiCalls.getBallotCount,
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getOfflineBatchResults(offlineBatchMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderView({
        round: roundMocks.sampledAllBallotsIncomplete,
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
