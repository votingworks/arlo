import React from 'react'
import { screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useParams } from 'react-router-dom'
import BatchRoundDataEntry from './BatchRoundDataEntry'
import { roundMocks, contestMocks } from '../useSetupMenuItems/_mocks'
import { batchesMocks, batchResultsMocks, INullResultValues } from './_mocks'
import { renderWithRouter, withMockFetch } from '../../testUtilities'
import { IContest } from '../../../types'
import { IBatch } from './useBatchResults'

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
  getBatches: (response: { batches: IBatch[] }) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/batches',
    response,
  }),
  putResults: (results: INullResultValues) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/batches/results',
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
      apiCalls.getBatches(batchesMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <BatchRoundDataEntry round={roundMocks.singleIncomplete[0]} />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Round 1 Data Entry')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders after submission', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <BatchRoundDataEntry round={roundMocks.singleIncomplete[0]} />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Round 1 Data Entry')
      expect(container).toMatchSnapshot()
    })
  })

  it('submits', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.putResults(batchResultsMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <BatchRoundDataEntry round={roundMocks.singleIncomplete[0]} />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Round 1 Data Entry')
      ;[0, 1, 2].forEach(batch => {
        fireEvent.change(
          screen.getAllByLabelText('Votes for Choice One:')[batch],
          {
            target: { value: '1' },
          }
        )
        fireEvent.change(
          screen.getAllByLabelText('Votes for Choice Two:')[batch],
          {
            target: { value: '2' },
          }
        )
      })
      userEvent.click(screen.getByText('Submit Data for Round 1'))
      await screen.findByText('Already Submitted Data for Round 1')
      expect(container).toMatchSnapshot()
    })
  })
})
