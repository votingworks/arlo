import { describe, it, vi } from 'vitest'
import React from 'react'
import { screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useParams } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import RoundDataEntry from './RoundDataEntry'
import { IContest } from '../../types'
import { contestMocks, roundMocks } from '../_mocks'
import { resultsMocks, INullResultValues } from './_mocks'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
} from '../testUtilities'

vi.mock(import('react-router-dom'), async importActual => ({
  ...(await importActual()), // use actual for all non-hook parts
  useRouteMatch: vi.fn(),
  useParams: vi.fn(),
}))
const paramsMock = vi.mocked(useParams)
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

const renderComponent = () =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <RoundDataEntry round={roundMocks.singleIncomplete[0]} />
    </QueryClientProvider>,
    {
      route: '/election/1/jurisdiction/1',
    }
  )

describe('offline round data entry', () => {
  it('submits', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(resultsMocks.emptyInitial),
      apiCalls.putResults(resultsMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
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
      userEvent.click(screen.getByText('Submit Tallies'))
      await screen.findByText('Tallies Submitted')
    })
  })
})
