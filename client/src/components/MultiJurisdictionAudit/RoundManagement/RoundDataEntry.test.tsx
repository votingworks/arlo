import React from 'react'
import { screen } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import RoundDataEntry from './RoundDataEntry'
import { roundMocks, contestMocks } from '../_mocks'
import { resultsMocks, INullResultValues } from './_mocks'
import { renderWithRouter, withMockFetch } from '../../testUtilities'
import { IContest } from '../../../types'
// import { IResultValues } from './useResults'

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
  getJAContests: (response: { contests: IContest[] }) => ({
    url: `/api/election/1/jurisdiction/1/contest`,
    response,
  }),
  getResults: (response: INullResultValues) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/results',
    response,
  }),
}

describe('offline round data entry', () => {
  it('renders', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(resultsMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <RoundDataEntry round={roundMocks.singleIncomplete[0]} />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Round 1 Data Entry')
      expect(container).toMatchSnapshot()
    })
  })
})
