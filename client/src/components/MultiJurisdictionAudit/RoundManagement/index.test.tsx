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
} from './_mocks'
import { dummyBallots } from '../../SingleJurisdictionAudit/_mocks'
import {
  auditSettings,
  auditBoardMocks,
  contestMocks,
} from '../useSetupMenuItems/_mocks'
import { IAuditSettings, IContest } from '../../../types'
import { IBatch } from './useBatchResults'
import { jaApiCalls } from '../_mocks'
import AuthDataProvider from '../../UserContext'

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
  getBallots: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots',
    response: dummyBallots,
  },
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
}

describe('RoundManagement', () => {
  it('renders null when still loading', async () => {
    const expectedCalls = [
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.blank),
      jaApiCalls.getUser,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: [],
        createAuditBoards: jest.fn(),
      })
      expect(container).toMatchSnapshot()
      await screen.findByText('Loading...')
    })
  })

  it('renders audit setup with batch audit', async () => {
    const expectedCalls = [
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
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
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
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
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
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
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.all),
      jaApiCalls.getUser,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Download Aggregated Ballot Retrieval List for Round 1'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('renders links & data entry with offline ballot audit', async () => {
    const expectedCalls = [
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.offlineAll),
      jaApiCalls.getUser,
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(batchResultsMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView({
        round: roundMocks.incomplete,
        auditBoards: auditBoardMocks.unfinished,
        createAuditBoards: jest.fn(),
      })
      await screen.findByText(
        'Download Aggregated Ballot Retrieval List for Round 1'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('renders links & data entry with batch audit', async () => {
    const expectedCalls = [
      apiCalls.getBallots,
      apiCalls.getSettings(auditSettings.batchComparisonAll),
      jaApiCalls.getUser,
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
      await screen.findByText(
        'Download Aggregated Batch Retrieval List for Round 1'
      )
      expect(container).toMatchSnapshot()
    })
  })
})
