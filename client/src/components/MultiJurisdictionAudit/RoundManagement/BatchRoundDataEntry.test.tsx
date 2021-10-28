import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import copy from 'copy-to-clipboard'
import { ToastContainer } from 'react-toastify'
import BatchRoundDataEntry from './BatchRoundDataEntry'
import { roundMocks, contestMocks } from '../useSetupMenuItems/_mocks'
import { batchesMocks } from './_mocks'
import {
  renderWithRouter,
  withMockFetch,
  serverError,
  findAndCloseToast,
} from '../../testUtilities'
import { IContest } from '../../../types'
import { IBatches, IBatchResults } from './useBatchResults'
import { queryClient } from '../../../App'

jest.mock('copy-to-clipboard', () => jest.fn(() => true))

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
  getBatches: (response: IBatches) => ({
    url: '/api/election/1/jurisdiction/1/round/round-1/batches',
    response,
  }),
  putBatchResults: (batchId: string, results: IBatchResults) => ({
    url: `/api/election/1/jurisdiction/1/round/round-1/batches/${batchId}/results`,
    options: {
      method: 'PUT',
      body: JSON.stringify(results),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  }),
  finalizeBatchResults: () => ({
    url: `/api/election/1/jurisdiction/1/round/round-1/batches/finalize`,
    options: { method: 'POST' },
    response: { status: 'ok' },
  }),
}

const render = () =>
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
      <BatchRoundDataEntry round={roundMocks.singleIncomplete[0]} />
      <ToastContainer />
    </QueryClientProvider>,
    {
      route: '/election/1/jurisdiction/1',
    }
  )

describe('Batch comparison data entry', () => {
  it('shows a table of batches and a button to edit results for each batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const batchTable = await screen.findByRole('table')

      const headers = within(batchTable).getAllByRole('columnheader')
      expect(headers).toHaveLength(5)
      expect(headers[0]).toHaveTextContent('Batch Name')
      expect(headers[1]).toHaveTextContent('Choice One')
      expect(headers[2]).toHaveTextContent('Choice Two')
      expect(headers[3]).toHaveTextContent('Batch Total Votes')
      expect(headers[4]).toHaveTextContent('Actions')

      const rows = within(batchTable).getAllByRole('row')
      expect(rows).toHaveLength(5)

      const row1 = within(rows[1]).getAllByRole('cell')
      expect(row1).toHaveLength(5)
      expect(row1[0]).toHaveTextContent('Batch One')
      expect(row1[1]).toHaveTextContent('')
      expect(row1[2]).toHaveTextContent('')
      expect(row1[3]).toHaveTextContent('')
      within(row1[4]).getByRole('button', { name: /Edit/ })

      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2).toHaveLength(5)
      expect(row2[0]).toHaveTextContent('Batch Two')
      expect(row2[1]).toHaveTextContent('')
      expect(row2[2]).toHaveTextContent('')
      expect(row2[3]).toHaveTextContent('')
      within(row2[4]).getByRole('button', { name: /Edit/ })

      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3).toHaveLength(5)
      expect(row3[0]).toHaveTextContent('Batch Three')
      expect(row3[1]).toHaveTextContent('')
      expect(row3[2]).toHaveTextContent('')
      expect(row3[3]).toHaveTextContent('')
      within(row3[4]).getByRole('button', { name: /Edit/ })

      const row4 = within(rows[4]).getAllByRole('cell')
      expect(row4).toHaveLength(5)
      expect(row4[0]).toHaveTextContent('Choice Total Votes')
      expect(row4[1]).toHaveTextContent('0')
      expect(row4[2]).toHaveTextContent('0')
      expect(row4[3]).toHaveTextContent('0')
      expect(row4[4]).toHaveTextContent('')
    })
  })

  it('edits the results for a batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.putBatchResults('batch-1', {
        'choice-id-1': 1,
        'choice-id-2': 2,
      }),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: [
          {
            ...batchesMocks.emptyInitial.batches[0],
            results: { 'choice-id-1': 1, 'choice-id-2': 2 },
          },
          ...batchesMocks.emptyInitial.batches.slice(1),
        ],
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      userEvent.click(within(rows[1]).getByRole('button', { name: /Edit/ }))

      const saveButton = await screen.findByRole('button', {
        name: /Save/,
      })
      rows = within(batchTable).getAllByRole('row')
      let row1 = within(rows[1]).getAllByRole('cell')

      const choice1Input = within(row1[1]).getByRole('spinbutton')
      userEvent.type(choice1Input, '1')
      await waitFor(
        () => expect(row1[3]).toHaveTextContent('1') // Batch total should update
      )

      // Try saving before filling out all batches
      userEvent.click(saveButton)

      // Should get a validation error
      const choice2Input = within(row1[2]).getByRole('spinbutton')
      await waitFor(() =>
        expect(choice2Input).toHaveStyle({ borderColor: 'red' })
      )
      expect(choice2Input).toHaveFocus()

      // Fill out the rest of the batches
      userEvent.type(choice2Input, '2')
      await waitFor(
        () => expect(row1[3]).toHaveTextContent('3') // Batch total should update
      )

      userEvent.click(saveButton)

      await waitFor(() => expect(saveButton).not.toBeInTheDocument())
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      within(row1[4]).getByRole('button', { name: /Edit/ })
      expect(row1[1]).toHaveTextContent('1')
      expect(row1[2]).toHaveTextContent('2')
      expect(row1[3]).toHaveTextContent('3')

      const row4 = within(rows[4]).getAllByRole('cell')
      expect(row4[1]).toHaveTextContent('1')
      expect(row4[2]).toHaveTextContent('2')
      expect(row4[3]).toHaveTextContent('3')

      // Test copy button
      const copyButton = screen.getByRole('button', {
        name: /Copy to clipboard/,
      })
      userEvent.click(copyButton)

      expect(copy).toHaveBeenCalled()
      expect((copy as jest.Mock).mock.calls[0][0]).toMatchSnapshot()
    })
  })

  it('cancels editing the results for a batch', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      userEvent.click(within(rows[1]).getByRole('button', { name: /Edit/ }))

      const cancelButton = await screen.findByRole('button', {
        name: /Cancel/,
      })
      rows = within(batchTable).getAllByRole('row')
      let row1 = within(rows[1]).getAllByRole('cell')

      const choice1Input = within(row1[1]).getByRole('spinbutton')
      userEvent.type(choice1Input, '1')
      const choice2Input = within(row1[2]).getByRole('spinbutton')
      userEvent.type(choice2Input, '2')

      userEvent.click(cancelButton)
      await waitFor(() => expect(cancelButton).not.toBeInTheDocument())

      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('')
      expect(row1[2]).toHaveTextContent('')
      expect(row1[3]).toHaveTextContent('')
      within(row1[4]).getByRole('button', { name: /Edit/ })
    })
  })

  it('finalizes results', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      apiCalls.finalizeBatchResults(),
      apiCalls.getBatches(batchesMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const finalizeButton = await screen.findByRole('button', {
        name: /Finalize Results/,
      })
      userEvent.click(finalizeButton)

      const dialog = (await screen.findByRole('heading', {
        name: 'Are you sure you want to finalize your results?',
      })).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: /Confirm/ }))

      await screen.findByText('Results finalized')
      expect(finalizeButton).toBeDisabled()
      const editButtons = screen.getAllByRole('button', { name: /Edit/ })
      editButtons.forEach(button => expect(button).toBeDisabled())
      expect(
        screen.getByRole('button', { name: /Copy to clipboard/ })
      ).toBeEnabled()
    })
  })

  it('disallows finalizing until all batches have results', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches({
        batches: [
          batchesMocks.emptyInitial.batches[0],
          ...batchesMocks.complete.batches.slice(1),
        ],
        resultsFinalizedAt: null,
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const finalizeButton = await screen.findByRole('button', {
        name: /Finalize Results/,
      })
      userEvent.click(finalizeButton)

      await findAndCloseToast(
        'Please enter results for all batches before finalizing.'
      )
    })
  })

  it('handles errors on save', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      serverError(
        'putBatchResults',
        apiCalls.putBatchResults('batch-1', {
          'choice-id-1': 1,
          'choice-id-2': 2,
        })
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      userEvent.click(within(rows[1]).getByRole('button', { name: /Edit/ }))

      const saveButton = await screen.findByRole('button', {
        name: /Save/,
      })
      rows = within(batchTable).getAllByRole('row')
      const row1 = within(rows[1]).getAllByRole('cell')

      const choice1Input = within(row1[1]).getByRole('spinbutton')
      userEvent.type(choice1Input, '1')
      const choice2Input = within(row1[2]).getByRole('spinbutton')
      userEvent.type(choice2Input, '2')

      userEvent.click(saveButton)

      await findAndCloseToast('something went wrong: putBatchResults')
      expect(saveButton).toBeInTheDocument()
    })
  })

  it('handles errors on finalize', async () => {
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      serverError('finalizeBatchResults', apiCalls.finalizeBatchResults()),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      userEvent.click(
        await screen.findByRole('button', { name: /Finalize Results/ })
      )
      const dialog = (await screen.findByRole('heading', {
        name: 'Are you sure you want to finalize your results?',
      })).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: /Confirm/ }))
      await findAndCloseToast('something went wrong: finalizeBatchResults')
    })
  })
})
