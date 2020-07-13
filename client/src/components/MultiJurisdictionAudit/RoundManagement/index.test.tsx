import React from 'react'
import { render, screen } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import RoundManagement from './index'
import { roundMocks, auditBoardMocks } from '../_mocks'
import { dummyBallots } from '../../SingleJurisdictionAudit/_mocks'
import { withMockFetch } from '../../testUtilities'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  jurisdictionId: '1',
})

const apiCalls = {
  getBallots: {
    url: '/api/election/1/jurisdiction/1/round/round-1/ballots',
    response: dummyBallots,
  },
}

describe('RoundManagement', () => {
  it('renders initial state', async () => {
    const expectedCalls = [apiCalls.getBallots]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render(
        <RoundManagement
          round={roundMocks.singleIncomplete[0]}
          auditBoards={auditBoardMocks.empty}
          createAuditBoards={jest.fn()}
        />
      )
      await screen.findByText('Round 1 Audit Board Setup')
      expect(container).toMatchSnapshot()
    })
  })
})
