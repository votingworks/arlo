import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import copy from 'copy-to-clipboard'
import { ToastContainer } from 'react-toastify'
import BatchRoundDataEntry from './BatchRoundDataEntry'
import { batchesMocks } from './_mocks'
import { IBatches, IBatchResultTallySheet } from './useBatchResults'
import { IContest } from '../../types'
import {
  renderWithRouter,
  withMockFetch,
  findAndCloseToast,
  serverError,
} from '../testUtilities'
import { queryClient } from '../../App'
import {
  contestMocks,
  roundMocks,
} from '../AuditAdmin/useSetupMenuItems/_mocks'

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
  putBatchResults: (
    batchId: string,
    resultTallySheets: IBatchResultTallySheet[]
  ) => ({
    url: `/api/election/1/jurisdiction/1/round/round-1/batches/${batchId}/results`,
    options: {
      method: 'PUT',
      body: JSON.stringify(resultTallySheets),
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

const batchesWithResults = (resultTallySheets: IBatchResultTallySheet[]) => [
  {
    ...batchesMocks.emptyInitial.batches[0],
    resultTallySheets,
  },
  ...batchesMocks.emptyInitial.batches.slice(1),
]

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
      expect(row1[1]).toBeEmpty()
      expect(row1[2]).toBeEmpty()
      expect(row1[3]).toBeEmpty()
      within(row1[4]).getByRole('button', { name: /Edit/ })

      const row2 = within(rows[2]).getAllByRole('cell')
      expect(row2).toHaveLength(5)
      expect(row2[0]).toHaveTextContent('Batch Two')
      expect(row2[1]).toBeEmpty()
      expect(row2[2]).toBeEmpty()
      expect(row2[3]).toBeEmpty()
      within(row2[4]).getByRole('button', { name: /Edit/ })

      const row3 = within(rows[3]).getAllByRole('cell')
      expect(row3).toHaveLength(5)
      expect(row3[0]).toHaveTextContent('Batch Three')
      expect(row3[1]).toBeEmpty()
      expect(row3[2]).toBeEmpty()
      expect(row3[3]).toBeEmpty()
      within(row3[4]).getByRole('button', { name: /Edit/ })

      const row4 = within(rows[4]).getAllByRole('cell')
      expect(row4).toHaveLength(5)
      expect(row4[0]).toHaveTextContent('Choice Total Votes')
      expect(row4[1]).toHaveTextContent('0')
      expect(row4[2]).toHaveTextContent('0')
      expect(row4[3]).toHaveTextContent('0')
      expect(row4[4]).toBeEmpty()
    })
  })

  it('edits the results for a batch', async () => {
    const tallySheet1 = {
      name: 'Tally Sheet #1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
      },
    }
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.putBatchResults('batch-1', [tallySheet1]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1]),
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

      // Try saving before filling out all choices
      userEvent.click(saveButton)

      // Should get a validation error
      const choice2Input = within(row1[2]).getByRole('spinbutton')
      await waitFor(() =>
        expect(choice2Input).toHaveStyle({ borderColor: 'red' })
      )
      expect(choice2Input).toHaveFocus()

      // Fill out the rest of the choices
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
      expect(row1[1]).toBeEmpty()
      expect(row1[2]).toBeEmpty()
      expect(row1[3]).toBeEmpty()
      within(row1[4]).getByRole('button', { name: /Edit/ })
    })
  })

  it('edits multiple tally sheets for a batch', async () => {
    const tallySheet1 = {
      name: 'Tally Sheet #1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
      },
    }
    const tallySheet2 = {
      name: 'Second Tally Sheet',
      results: {
        'choice-id-1': 3,
        'choice-id-2': 4,
      },
    }
    const expectedCalls = [
      apiCalls.getJAContests({ contests: contestMocks.oneTargeted }),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.putBatchResults('batch-1', [tallySheet1, tallySheet2]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1, tallySheet2]),
      }),
      apiCalls.putBatchResults('batch-1', [tallySheet2]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet2]),
      }),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet2]),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      const batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      userEvent.click(within(rows[1]).getByRole('button', { name: /More/ }))
      userEvent.click(screen.getByText('Use Multiple Tally Sheets'))

      let dialog = (await screen.findByRole('heading', {
        name: /Edit Tally Sheets for Batch: Batch One/,
      })).closest('.bp3-dialog')! as HTMLElement
      let tallySheetsTable = within(dialog).getByRole('table')

      const headers = within(tallySheetsTable).getAllByRole('columnheader')
      expect(headers).toHaveLength(4)
      expect(headers[0]).toHaveTextContent('Tally Sheet Label')
      expect(headers[1]).toHaveTextContent('Choice One')
      expect(headers[2]).toHaveTextContent('Choice Two')
      expect(headers[3]).toHaveTextContent('Actions')

      rows = within(tallySheetsTable).getAllByRole('row')
      expect(rows).toHaveLength(2)

      let row1 = within(rows[1]).getAllByRole('cell')
      expect(row1).toHaveLength(4)
      expect(within(row1[0]).getByRole('textbox')).toHaveValue('Tally Sheet #1')
      const choice1Input = within(row1[1]).getByRole('spinbutton')
      expect(choice1Input).toBeEmpty()
      const choice2Input = within(row1[2]).getByRole('spinbutton')
      expect(choice2Input).toBeEmpty()
      expect(
        within(row1[3]).getByRole('button', { name: /Delete/ })
      ).toBeDisabled()

      // Fill out one choice
      userEvent.type(choice1Input, '1')

      // Try saving before filling out all choices
      userEvent.click(screen.getByRole('button', { name: /Save/ }))

      // Should get a validation error
      await waitFor(() =>
        expect(choice2Input).toHaveStyle({ borderColor: 'red' })
      )
      expect(choice2Input).toHaveFocus()

      // Fill out the other choice
      userEvent.type(choice2Input, '2')

      // Add another tally sheet
      userEvent.click(screen.getByRole('button', { name: /Add Tally Sheet/ }))
      rows = within(tallySheetsTable).getAllByRole('row')
      const row2 = within(rows[2]).getAllByRole('cell')

      // Delete the default label
      const labelInput = within(row2[0]).getByRole('textbox')
      expect(labelInput).toHaveValue('Tally Sheet #2')
      userEvent.clear(labelInput)

      // Fill out the choices
      userEvent.type(within(row2[1]).getByRole('spinbutton'), '3')
      userEvent.type(within(row2[2]).getByRole('spinbutton'), '4')

      // Try saving
      userEvent.click(screen.getByRole('button', { name: /Save/ }))

      // Should get a validation error
      await waitFor(() =>
        expect(labelInput).toHaveStyle({ borderColor: 'red' })
      )
      expect(labelInput).toHaveFocus()

      // Enter a label
      userEvent.type(labelInput, 'Second Tally Sheet')

      // Now save - should show in main results table
      userEvent.click(screen.getByRole('button', { name: /Save/ }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      // Choice tally sheets should be summed
      expect(row1[1]).toHaveTextContent(`${1 + 3}`)
      expect(row1[2]).toHaveTextContent(`${2 + 4}`)
      expect(row1[3]).toHaveTextContent(`${1 + 3 + 2 + 4}`)
      const editTallySheetsButton = within(row1[4]).getByRole('button', {
        name: /Edit Tally Sheets/,
      })
      expect(
        within(row1[4]).queryByRole('button', { name: /More/ })
      ).not.toBeInTheDocument()

      // Reopen the tally sheets modal
      userEvent.click(editTallySheetsButton)
      dialog = (await screen.findByRole('heading', {
        name: /Edit Tally Sheets for Batch: Batch One/,
      })).closest('.bp3-dialog')! as HTMLElement
      tallySheetsTable = within(dialog).getByRole('table')
      rows = within(tallySheetsTable).getAllByRole('row')
      expect(rows).toHaveLength(3)

      // Delete the first tally sheet
      within(rows[1])
        .getByRole('button', { name: /Delete/ })
        .click()
      rows = within(tallySheetsTable).getAllByRole('row')
      expect(rows).toHaveLength(2)

      // Save the changes - should revert main results table to a single tally sheet
      userEvent.click(screen.getByRole('button', { name: /Save/ }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('3')
      expect(row1[2]).toHaveTextContent('4')
      expect(row1[3]).toHaveTextContent(`${3 + 4}`)
      within(row1[4]).getByRole('button', {
        name: /Edit/,
      })
      const moreButton = within(row1[4]).getByRole('button', { name: /More/ })

      // Open again
      userEvent.click(moreButton)
      userEvent.click(screen.getByText('Use Multiple Tally Sheets'))
      dialog = (await screen.findByRole('heading', {
        name: /Edit Tally Sheets for Batch: Batch One/,
      })).closest('.bp3-dialog')! as HTMLElement
      tallySheetsTable = within(dialog).getByRole('table')
      rows = within(tallySheetsTable).getAllByRole('row')
      expect(rows).toHaveLength(3)
      expect(within(rows[2]).getByRole('textbox')).toHaveValue('Tally Sheet #2')

      // Cancel - no changes in main table
      userEvent.click(screen.getByRole('button', { name: /Cancel/ }))
      await waitFor(() => expect(dialog).not.toBeInTheDocument())
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[1]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('3')
      expect(row1[2]).toHaveTextContent('4')
      expect(row1[3]).toHaveTextContent(`${3 + 4}`)
      within(row1[4]).getByRole('button', {
        name: /Edit/,
      })
      within(row1[4]).getByRole('button', { name: /More/ })
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
        apiCalls.putBatchResults('batch-1', [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ])
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
