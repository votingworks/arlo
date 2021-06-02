import React from 'react'
import { screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useParams } from 'react-router-dom'
import { contestMocks } from '../useSetupMenuItems/_mocks'
import {
  offlineBatchMocks,
  offlineBatchResultsMocks,
  roundMocks,
} from './_mocks'
import { renderWithRouter, withMockFetch } from '../../testUtilities'
import { IContest } from '../../../types'
import { IBatch } from './useBatchResults'
import OfflineBatchRoundDataEntry from './OfflineBatchRoundDataEntry'
import {
  IOfflineBatchResult,
  IOfflineBatchResults,
} from './useOfflineBatchResults'

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
  getResults: (response: IOfflineBatchResults) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/results/batch',
    response,
  }),
  postResults: (results: IOfflineBatchResult) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/results/batch/',
    options: {
      method: 'POST',
      body: JSON.stringify(results),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  }),
  putResults: (results: IOfflineBatchResult, previousBatchName: string) => ({
    url: `/api/election/1/jurisdiction/1/round/round-1/results/batch/${previousBatchName}`,
    options: {
      method: 'PUT',
      body: JSON.stringify(results),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  }),
  deleteResults: (batchName: string) => ({
    url: `/api/election/1/jurisdiction/1/round/round-1/results/batch/${batchName}`,
    options: {
      method: 'DELETE',
    },
    response: { status: 'ok' },
  }),
  finalizeResults: {
    url: '/api/election/1/jurisdiction/1/round/round-1/results/batch/finalize',
    options: {
      method: 'POST',
    },
    response: { status: 'ok' },
  },
}

describe('offline batch round data entry', () => {
  it('renders', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('No batches added. Add your first batch below.')
      expect(container).toMatchSnapshot()
    })
  })

  it('validation error for blank submission', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('No batches added. Add your first batch below.')
      const addButton = screen.getByRole('button', { name: /Add batch/ })
      await userEvent.click(addButton)

      const dialog = (await screen.findByRole('heading', {
        name: /Add Batch/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Batch Info')
      userEvent.click(
        within(dialog).getByRole('button', { name: 'Save Batch' })
      )

      await screen.findByText(
        'Please fill in the empty fields above before saving this batch.'
      )
      expect(container).toMatchSnapshot()
    })
  })

  it('submits offline batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.empty),
      apiCalls.postResults(offlineBatchResultsMocks.complete),
      apiCalls.getResults(offlineBatchMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('No batches added. Add your first batch below.')
      const addButton = screen.getByRole('button', { name: /Add batch/ })
      userEvent.click(addButton)

      const dialog = (await screen.findByRole('heading', {
        name: /Add Batch/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Batch Info')

      const batchNameInput = within(dialog).getByLabelText('Batch Name')
      userEvent.type(batchNameInput, 'Batch1')

      const choiceOneInput = within(dialog).getByLabelText('Choice One')
      fireEvent.change(choiceOneInput, { target: { value: 10 } })

      const choiceTwoInput = within(dialog).getByLabelText('Choice Two')
      fireEvent.change(choiceTwoInput, { target: { value: 20 } })

      userEvent.selectOptions(
        within(dialog).getByLabelText('Batch Type'),
        'Other'
      )

      fireEvent.click(
        within(dialog).getByRole('button', { name: 'Save Batch' })
      )
      await screen.findByText('Batch1')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders with offline batches', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Batch1')

      expect(container).toMatchSnapshot()
    })
  })

  it('renders with proper totals', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.completeWithMultipleBatch),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Batch1')

      const totalRow = screen
        .getAllByText('Total')[1]
        .closest('tr')! as HTMLElement

      // checking if total is proper
      within(totalRow).getByText('30')

      expect(container).toMatchSnapshot()
    })
  })

  it('edits offline batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.complete),
      apiCalls.putResults(offlineBatchResultsMocks.updated, 'Batch1'),
      apiCalls.getResults(offlineBatchMocks.updated),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )

      await screen.findByText('Batch1')
      userEvent.click(screen.getByText(/Edit/))

      const dialog = (await screen.findByRole('heading', {
        name: /Edit Batch/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Batch Info')

      const batchNameInput = within(dialog).getByLabelText('Batch Name')
      userEvent.type(batchNameInput, '2')

      fireEvent.click(
        within(dialog).getByRole('button', { name: 'Save Batch' })
      )
      await screen.findByText('Batch12')

      expect(container).toMatchSnapshot()
    })
  })

  it('deletes offline batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.complete),
      apiCalls.deleteResults(offlineBatchResultsMocks.complete.batchName),
      apiCalls.getResults(offlineBatchMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )

      await screen.findByText('Batch1')
      userEvent.click(screen.getByText(/Edit/))

      const dialog = (await screen.findByRole('heading', {
        name: /Edit Batch/,
      })).closest('.bp3-dialog')! as HTMLElement
      within(dialog).getByText('Batch Info')

      fireEvent.click(
        within(dialog).getByRole('button', { name: 'Remove Batch' })
      )
      await screen.findByText('No batches added. Add your first batch below.')

      expect(container).toMatchSnapshot()
    })
  })

  it('finalizes offline batches', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getResults(offlineBatchMocks.complete),
      apiCalls.finalizeResults,
      apiCalls.getResults(offlineBatchMocks.finalized),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderWithRouter(
        <OfflineBatchRoundDataEntry
          round={roundMocks.sampledAllBallotsIncomplete}
        />,
        {
          route: '/election/1/jurisdiction/1',
        }
      )
      await screen.findByText('Batch1')

      fireEvent.click(screen.getByRole('button', { name: 'Finalize Results' }))

      const dialog = (await screen.findByRole('heading', {
        name: /Are you sure you want to finalize your results?/,
      })).closest('.bp3-dialog')! as HTMLElement

      within(dialog).getByText('This action cannot be undone.')

      fireEvent.click(
        within(dialog).getByRole('button', { name: 'Finalize Results' })
      )

      await screen.findByText(/Results finalized at/)

      expect(container).toMatchSnapshot()
    })
  })
})
