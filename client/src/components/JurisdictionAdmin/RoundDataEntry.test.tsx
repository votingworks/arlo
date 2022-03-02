import React from 'react'
import { screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useParams } from 'react-router-dom'
import RoundDataEntry from './RoundDataEntry'
import { IContest } from '../../types'
import {
  contestMocks,
  roundMocks,
} from '../AuditAdmin/useSetupMenuItems/_mocks'
import { resultsMocks, INullResultValues } from './_mocks'
import { withMockFetch, renderWithRouter } from '../testUtilities'

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
  putResults: (results: INullResultValues) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/results',
    options: {
      method: 'PUT',
      body: JSON.stringify(results),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
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
      await screen.findByText('Votes for Choice One:')
      expect(container).toMatchSnapshot()
    })
  })

  it('submits', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(resultsMocks.emptyInitial),
      apiCalls.putResults(resultsMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <RoundDataEntry round={roundMocks.singleIncomplete[0]} />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Votes for Choice One:')
      fireEvent.change(screen.getByLabelText('Votes for Choice One:'), {
        target: { value: '1' },
      })
      fireEvent.change(screen.getByLabelText('Votes for Choice Two:'), {
        target: { value: '2' },
      })
      fireEvent.change(screen.getByLabelText('Votes for Choice Three:'), {
        target: { value: '1' },
      })
      fireEvent.change(screen.getByLabelText('Votes for Choice Four:'), {
        target: { value: '2' },
      })
      userEvent.click(screen.getByText('Submit Data for Round 1'))
      await screen.findByText('Already Submitted Data for Round 1')
      expect(container).toMatchSnapshot()
    })
  })
})
