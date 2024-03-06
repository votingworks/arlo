import React from 'react'
import { render, screen, within, waitFor } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { ToastContainer } from 'react-toastify'
import { Classes } from '@blueprintjs/core'
import BatchRoundTallyEntry from './BatchRoundTallyEntry'
import { batchesMocks } from '../../_mocks'
import { IBatches, IBatchResultTallySheet } from '../../useBatchResults'
import { IContest } from '../../../../types'
import {
  withMockFetch,
  findAndCloseToast,
  serverError,
  createQueryClient,
} from '../../../testUtilities'
import { contestMocks } from '../../../_mocks'

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
    lastEditedBy: 'ja@example.com',
  },
  ...batchesMocks.emptyInitial.batches.slice(1),
]

const renderComponent = () =>
  render(
    <QueryClientProvider client={createQueryClient()}>
      <BatchRoundTallyEntry
        electionId="1"
        jurisdictionId="1"
        roundId="round-1"
      />
      <ToastContainer />
    </QueryClientProvider>
  )

describe('Batch comparison data entry', () => {
  it('shows a table of batches and a button to edit results for each batch', async () => {
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.one }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      await screen.findByRole('tab', { name: 'Vote Totals' })

      for (const batch of ['Batch One', 'Batch Two', 'Batch Three']) {
        userEvent.click(screen.getByRole('button', { name: batch }))
        // eslint-disable-next-line no-await-in-loop
        await screen.findByRole('heading', { name: batch })
        const batchTable = screen.getByRole('table')

        const headers = within(batchTable).getAllByRole('columnheader')
        expect(headers).toHaveLength(3)
        expect(headers[0]).toHaveTextContent('Contest 1')
        expect(headers[1]).toHaveTextContent('Choice')
        expect(headers[2]).toHaveTextContent('Votes')

        const rows = within(batchTable).getAllByRole('row')
        expect(rows).toHaveLength(4)

        const row1 = within(rows[2]).getAllByRole('cell')
        const row2 = within(rows[3]).getAllByRole('cell')
        expect(row1).toHaveLength(2)
        expect(row2).toHaveLength(2)

        expect(row1[0]).toHaveTextContent('Choice One')
        expect(row1[1]).toHaveTextContent('')
        expect(row2[0]).toHaveTextContent('Choice Two')
        expect(row2[1]).toHaveTextContent('')

        screen.getByRole('button', { name: /Edit Tallies/ })
      }
    })
  })

  it('edits the results for a batch', async () => {
    const tallySheet1 = {
      name: 'Sheet 1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
      },
    }
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.one }),
      apiCalls.putBatchResults('batch-1', [tallySheet1]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1]),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      let batchTable = await screen.findByRole('table')

      userEvent.click(screen.getByRole('button', { name: /Edit Tallies/ }))

      batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      let row1 = within(rows[2]).getAllByRole('cell')
      let row2 = within(rows[3]).getAllByRole('cell')
      const choice1VotesInput = within(row1[1]).getByRole('spinbutton')
      let choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      expect(choice1VotesInput).toHaveFocus()
      userEvent.type(choice1VotesInput, '1')
      userEvent.clear(choice2VotesInput)

      // Try saving before filling out all choices
      const saveButton = screen.getByRole('button', { name: /Save Tallies/ })
      userEvent.click(saveButton)

      // Should get a validation error
      choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      await waitFor(() =>
        expect(choice2VotesInput).toHaveClass(Classes.INTENT_DANGER)
      )
      expect(choice2VotesInput).toHaveFocus()

      // Fill out the rest of the choices
      userEvent.type(choice2VotesInput, '2')
      userEvent.click(saveButton)
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Tallies/ })
        ).not.toBeInTheDocument()
      )

      batchTable = screen.getByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[2]).getAllByRole('cell')
      row2 = within(rows[3]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('1')
      expect(row2[1]).toHaveTextContent('2')
      screen.getByText('Last edited by: ja@example.com')
    })
  })

  it('cancels editing the results for a batch', async () => {
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.one }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      let batchTable = await screen.findByRole('table')

      userEvent.click(screen.getByRole('button', { name: /Edit Tallies/ }))

      batchTable = await screen.findByRole('table')
      let rows = within(batchTable).getAllByRole('row')
      let row1 = within(rows[2]).getAllByRole('cell')
      let row2 = within(rows[3]).getAllByRole('cell')
      const choice1VotesInput = within(row1[1]).getByRole('spinbutton')
      const choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      userEvent.type(choice1VotesInput, '1')
      userEvent.type(choice2VotesInput, '2')

      const discardChangesButton = await screen.findByRole('button', {
        name: /Discard Changes/,
      })
      userEvent.click(discardChangesButton)
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Discard Changes/ })
        ).not.toBeInTheDocument()
      )

      batchTable = await screen.findByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[2]).getAllByRole('cell')
      row2 = within(rows[3]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('')
      expect(row2[1]).toHaveTextContent('')
    })
  })

  it('edits the results for a batch with multiple tally sheets', async () => {
    const tallySheet1BeforeEdit = {
      name: 'Sheet 1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 1,
      },
    }
    const tallySheet1AfterEdit = {
      name: 'Sheet 1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
      },
    }
    const tallySheet2 = {
      name: 'Sheet 2',
      results: {
        'choice-id-1': 0,
        'choice-id-2': 0,
      },
    }
    const tallySheet3 = {
      name: 'Sheet Three',
      results: {
        'choice-id-1': 3,
        'choice-id-2': 4,
      },
    }
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.one }),
      apiCalls.putBatchResults('batch-1', [tallySheet1BeforeEdit, tallySheet2]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1BeforeEdit, tallySheet2]),
      }),
      apiCalls.putBatchResults('batch-1', [tallySheet1AfterEdit, tallySheet2]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1AfterEdit, tallySheet2]),
      }),
      apiCalls.putBatchResults('batch-1', [
        tallySheet1AfterEdit,
        tallySheet2,
        tallySheet3,
      ]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([
          tallySheet1AfterEdit,
          tallySheet2,
          tallySheet3,
        ]),
      }),
      apiCalls.putBatchResults('batch-1', [tallySheet2, tallySheet3]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet2, tallySheet3]),
      }),
      apiCalls.putBatchResults('batch-1', [
        { ...tallySheet3, name: 'Sheet 1' },
      ]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([{ ...tallySheet3, name: 'Sheet 1' }]),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      let batchTable = await screen.findByRole('table')

      userEvent.click(
        screen.getByRole('button', { name: /Additional Actions/ })
      )
      userEvent.click(screen.getByText('Use Multiple Tally Sheets'))

      batchTable = await screen.findByRole('table')
      const headers = within(batchTable).getAllByRole('columnheader')
      expect(headers).toHaveLength(3)
      expect(headers[0]).toHaveTextContent('Contest 1')
      expect(headers[1]).toHaveTextContent('Choice')
      expect(headers[2]).toHaveTextContent('Votes')
      let rows = within(batchTable).getAllByRole('row')
      expect(rows).toHaveLength(4)
      let row1 = within(rows[2]).getAllByRole('cell')
      let row2 = within(rows[3]).getAllByRole('cell')
      expect(row1).toHaveLength(2)
      expect(row2).toHaveLength(2)
      let choice1VotesInput = within(row1[1]).getByRole('spinbutton')
      let choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      expect(choice1VotesInput).toHaveFocus()
      expect(choice1VotesInput).toHaveTextContent('')
      expect(choice2VotesInput).toHaveTextContent('')

      // Fill out one choice validly and the other invalidly
      userEvent.type(choice1VotesInput, '1')
      userEvent.type(choice2VotesInput, '-1')

      // Should get a validation error
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(choice2VotesInput).toHaveClass(Classes.INTENT_DANGER)
      )
      expect(choice2VotesInput).toHaveFocus()

      // Correct the error
      userEvent.clear(choice2VotesInput)
      userEvent.type(choice2VotesInput, '1')
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Sheet/ })
        ).not.toBeInTheDocument()
      )

      let voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      let sheet1Tab = screen.getByRole('tab', { name: 'Sheet 1' })
      let sheet2Tab = screen.getByRole('tab', { name: 'Sheet 2' })
      expect(sheet1Tab).toHaveAttribute('aria-selected', 'true')

      // Edit the sheet
      userEvent.click(screen.getByRole('button', { name: /Edit Sheet/ }))
      batchTable = await screen.findByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row2 = within(rows[3]).getAllByRole('cell')
      choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      userEvent.clear(choice2VotesInput)
      userEvent.type(choice2VotesInput, '2')
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Sheet/ })
        ).not.toBeInTheDocument()
      )

      // Add another tally sheet, rename it, but then discard it
      userEvent.click(screen.getByRole('button', { name: /Add Sheet/ }))
      let sheetNameInput = await screen.findByRole('textbox', {
        name: 'Sheet Name',
      })
      userEvent.clear(sheetNameInput)
      userEvent.type(sheetNameInput, 'Sheet Three')
      userEvent.click(screen.getByRole('button', { name: /Discard Changes/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Discard Changes/ })
        ).not.toBeInTheDocument()
      )

      voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      sheet1Tab = screen.getByRole('tab', { name: 'Sheet 1' })
      sheet2Tab = screen.getByRole('tab', { name: 'Sheet 2' })
      expect(sheet2Tab).toHaveAttribute('aria-selected', 'true')

      // Add another tally sheet, rename it, and save it
      userEvent.click(screen.getByRole('button', { name: /Add Sheet/ }))
      sheetNameInput = await screen.findByRole('textbox', {
        name: 'Sheet Name',
      })
      userEvent.clear(sheetNameInput)
      userEvent.type(sheetNameInput, 'Sheet Three')
      batchTable = screen.getByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[2]).getAllByRole('cell')
      row2 = within(rows[3]).getAllByRole('cell')
      choice1VotesInput = within(row1[1]).getByRole('spinbutton')
      choice2VotesInput = within(row2[1]).getByRole('spinbutton')
      userEvent.type(choice1VotesInput, '3')
      userEvent.type(choice2VotesInput, '4')
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Sheet/ })
        ).not.toBeInTheDocument()
      )
      screen.getByRole('tab', { name: 'Sheet Three' })

      // Check that the vote totals tab displays sums after saving
      voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      userEvent.click(voteTotalsTab)
      expect(voteTotalsTab).toHaveAttribute('aria-selected', 'true')
      batchTable = await screen.findByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[2]).getAllByRole('cell')
      row2 = within(rows[3]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent(`${1 + 3}`)
      expect(row2[1]).toHaveTextContent(`${2 + 4}`)

      // Delete the first tally sheet
      sheet1Tab = screen.getByRole('tab', { name: 'Sheet 1' })
      userEvent.click(sheet1Tab)
      userEvent.click(
        screen.getByRole('button', { name: 'Additional Actions' })
      )
      userEvent.click(await screen.findByText('Remove Sheet'))
      await waitFor(() =>
        expect(
          screen.queryByRole('tab', { name: 'Sheet 1' })
        ).not.toBeInTheDocument()
      )

      // Check that vote totals are updated as expected
      voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      userEvent.click(voteTotalsTab)
      expect(voteTotalsTab).toHaveAttribute('aria-selected', 'true')
      batchTable = await screen.findByRole('table')
      rows = within(batchTable).getAllByRole('row')
      row1 = within(rows[2]).getAllByRole('cell')
      row2 = within(rows[3]).getAllByRole('cell')
      expect(row1[1]).toHaveTextContent('3')
      expect(row2[1]).toHaveTextContent('4')

      // Delete the second tally sheet
      sheet1Tab = screen.getByRole('tab', { name: 'Sheet 2' })
      userEvent.click(sheet1Tab)
      userEvent.click(
        screen.getByRole('button', { name: 'Additional Actions' })
      )
      userEvent.click(await screen.findByText('Remove Sheet'))
      await waitFor(() =>
        expect(
          screen.queryByRole('tab', { name: 'Sheet 2' })
        ).not.toBeInTheDocument()
      )

      // Check that we return to the single tally sheet UI
      await waitFor(() =>
        expect(
          screen.queryByRole('tab', { name: 'Sheet Three' })
        ).not.toBeInTheDocument()
      )
      voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      expect(voteTotalsTab).toHaveAttribute('aria-selected', 'true')
    })
  })

  it('edits the results for a batch with multiple contests', async () => {
    const tallySheet1 = {
      name: 'Sheet 1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
        'choice-id-3': 3,
        'choice-id-4': 4,
      },
    }
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.two }),
      apiCalls.putBatchResults('batch-1', [tallySheet1]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1]),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      let batchTables = await screen.findAllByRole('table')

      userEvent.click(screen.getByRole('button', { name: /Edit Tallies/ }))

      const table1Headers = within(batchTables[0]).getAllByRole('columnheader')
      expect(table1Headers).toHaveLength(3)
      expect(table1Headers[0]).toHaveTextContent('Contest 1')
      expect(table1Headers[1]).toHaveTextContent('Choice')
      expect(table1Headers[2]).toHaveTextContent('Votes')
      let table1Rows = within(batchTables[0]).getAllByRole('row')
      let table1Row1 = within(table1Rows[2]).getAllByRole('cell')
      let table1Row2 = within(table1Rows[3]).getAllByRole('cell')
      const choice1VotesInput = within(table1Row1[1]).getByRole('spinbutton')
      const choice2VotesInput = within(table1Row2[1]).getByRole('spinbutton')
      expect(choice1VotesInput).toHaveFocus()
      userEvent.type(choice1VotesInput, '1')
      userEvent.type(choice2VotesInput, '2')

      // Try saving before filling out choices for all contests
      const saveButton = screen.getByRole('button', { name: /Save Tallies/ })
      userEvent.click(saveButton)

      // Should get a validation error
      const table2Headers = within(batchTables[1]).getAllByRole('columnheader')
      expect(table2Headers).toHaveLength(3)
      expect(table2Headers[0]).toHaveTextContent('Contest 2')
      expect(table2Headers[1]).toHaveTextContent('Choice')
      expect(table2Headers[2]).toHaveTextContent('Votes')
      let table2Rows = within(batchTables[1]).getAllByRole('row')
      let table2Row1 = within(table2Rows[2]).getAllByRole('cell')
      let table2Row2 = within(table2Rows[3]).getAllByRole('cell')
      const choice3VotesInput = within(table2Row1[1]).getByRole('spinbutton')
      const choice4VotesInput = within(table2Row2[1]).getByRole('spinbutton')
      await waitFor(() => {
        expect(choice3VotesInput).toHaveClass(Classes.INTENT_DANGER)
        expect(choice4VotesInput).toHaveClass(Classes.INTENT_DANGER)
      })
      expect(choice3VotesInput).toHaveFocus()

      // Fill out the rest of the choices
      userEvent.type(choice3VotesInput, '3')
      userEvent.type(choice4VotesInput, '4')
      userEvent.click(saveButton)
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Tallies/ })
        ).not.toBeInTheDocument()
      )

      batchTables = screen.getAllByRole('table')
      table1Rows = within(batchTables[0]).getAllByRole('row')
      table2Rows = within(batchTables[1]).getAllByRole('row')
      table1Row1 = within(table1Rows[2]).getAllByRole('cell')
      table1Row2 = within(table1Rows[3]).getAllByRole('cell')
      table2Row1 = within(table2Rows[2]).getAllByRole('cell')
      table2Row2 = within(table2Rows[3]).getAllByRole('cell')
      expect(table1Row1[1]).toHaveTextContent('1')
      expect(table1Row2[1]).toHaveTextContent('2')
      expect(table2Row1[1]).toHaveTextContent('3')
      expect(table2Row2[1]).toHaveTextContent('4')
      screen.getByText('Last edited by: ja@example.com')
    })
  })

  it('edits the results for a batch with multiple contests and multiple tally sheets', async () => {
    const tallySheet1 = {
      name: 'Sheet 1',
      results: {
        'choice-id-1': 1,
        'choice-id-2': 2,
        'choice-id-3': 3,
        'choice-id-4': 4,
      },
    }
    const tallySheet2BeforeEdit = {
      name: 'Sheet 2',
      results: {
        'choice-id-1': 0,
        'choice-id-2': 0,
        'choice-id-3': 0,
        'choice-id-4': 0,
      },
    }
    const tallySheet2AfterEdit = {
      name: 'Sheet 2',
      results: {
        'choice-id-1': 5,
        'choice-id-2': 6,
        'choice-id-3': 7,
        'choice-id-4': 8,
      },
    }
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.two }),
      apiCalls.putBatchResults('batch-1', [tallySheet1, tallySheet2BeforeEdit]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1, tallySheet2BeforeEdit]),
      }),
      apiCalls.putBatchResults('batch-1', [tallySheet1, tallySheet2AfterEdit]),
      apiCalls.getBatches({
        ...batchesMocks.emptyInitial,
        batches: batchesWithResults([tallySheet1, tallySheet2AfterEdit]),
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      let batchTables = await screen.findAllByRole('table')

      userEvent.click(
        screen.getByRole('button', { name: /Additional Actions/ })
      )
      userEvent.click(screen.getByText('Use Multiple Tally Sheets'))

      batchTables = await screen.findAllByRole('table')
      let table1Rows = within(batchTables[0]).getAllByRole('row')
      let table2Rows = within(batchTables[1]).getAllByRole('row')
      let table1Row1 = within(table1Rows[2]).getAllByRole('cell')
      let table1Row2 = within(table1Rows[3]).getAllByRole('cell')
      let table2Row1 = within(table2Rows[2]).getAllByRole('cell')
      let table2Row2 = within(table2Rows[3]).getAllByRole('cell')
      let choice1VotesInput = within(table1Row1[1]).getByRole('spinbutton')
      let choice2VotesInput = within(table1Row2[1]).getByRole('spinbutton')
      let choice3VotesInput = within(table2Row1[1]).getByRole('spinbutton')
      let choice4VotesInput = within(table2Row2[1]).getByRole('spinbutton')
      expect(choice1VotesInput).toHaveFocus()
      expect(choice1VotesInput).toHaveTextContent('')
      expect(choice2VotesInput).toHaveTextContent('')
      expect(choice3VotesInput).toHaveTextContent('')
      expect(choice4VotesInput).toHaveTextContent('')

      userEvent.type(choice1VotesInput, '1')
      userEvent.type(choice2VotesInput, '2')
      userEvent.type(choice3VotesInput, '3')
      userEvent.type(choice4VotesInput, '4')
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Sheet/ })
        ).not.toBeInTheDocument()
      )

      let voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      const sheet1Tab = screen.getByRole('tab', { name: 'Sheet 1' })
      const sheet2Tab = screen.getByRole('tab', { name: 'Sheet 2' })
      expect(sheet1Tab).toHaveAttribute('aria-selected', 'true')
      userEvent.click(sheet2Tab)
      await waitFor(() =>
        expect(sheet2Tab).toHaveAttribute('aria-selected', 'true')
      )
      userEvent.click(screen.getByRole('button', { name: /Edit Sheet/ }))

      batchTables = await screen.findAllByRole('table')
      table1Rows = within(batchTables[0]).getAllByRole('row')
      table2Rows = within(batchTables[1]).getAllByRole('row')
      table1Row1 = within(table1Rows[2]).getAllByRole('cell')
      table1Row2 = within(table1Rows[3]).getAllByRole('cell')
      table2Row1 = within(table2Rows[2]).getAllByRole('cell')
      table2Row2 = within(table2Rows[3]).getAllByRole('cell')
      choice1VotesInput = within(table1Row1[1]).getByRole('spinbutton')
      choice2VotesInput = within(table1Row2[1]).getByRole('spinbutton')
      choice3VotesInput = within(table2Row1[1]).getByRole('spinbutton')
      choice4VotesInput = within(table2Row2[1]).getByRole('spinbutton')
      expect(choice1VotesInput).toHaveTextContent('')
      expect(choice2VotesInput).toHaveTextContent('')
      expect(choice3VotesInput).toHaveTextContent('')
      expect(choice4VotesInput).toHaveTextContent('')

      userEvent.type(choice1VotesInput, '5')
      userEvent.type(choice2VotesInput, '6')
      userEvent.type(choice3VotesInput, '7')
      userEvent.type(choice4VotesInput, '8')
      userEvent.click(screen.getByRole('button', { name: /Save Sheet/ }))
      await waitFor(() =>
        expect(
          screen.queryByRole('button', { name: /Save Sheet/ })
        ).not.toBeInTheDocument()
      )

      voteTotalsTab = screen.getByRole('tab', { name: 'Vote Totals' })
      userEvent.click(voteTotalsTab)
      expect(voteTotalsTab).toHaveAttribute('aria-selected', 'true')
      batchTables = await screen.findAllByRole('table')
      table1Rows = within(batchTables[0]).getAllByRole('row')
      table2Rows = within(batchTables[1]).getAllByRole('row')
      table1Row1 = within(table1Rows[2]).getAllByRole('cell')
      table1Row2 = within(table1Rows[3]).getAllByRole('cell')
      table2Row1 = within(table2Rows[2]).getAllByRole('cell')
      table2Row2 = within(table2Rows[3]).getAllByRole('cell')
      expect(table1Row1[1]).toHaveTextContent('6')
      expect(table1Row2[1]).toHaveTextContent('8')
      expect(table2Row1[1]).toHaveTextContent('10')
      expect(table2Row2[1]).toHaveTextContent('12')
    })
  })

  it('handles errors on save', async () => {
    const expectedCalls = [
      apiCalls.getBatches(batchesMocks.emptyInitial),
      apiCalls.getJAContests({ contests: contestMocks.one }),
      serverError(
        'putBatchResults',
        apiCalls.putBatchResults('batch-1', [
          {
            name: 'Sheet 1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ])
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      const batchTable = await screen.findByRole('table')
      userEvent.click(screen.getByRole('button', { name: /Edit Tallies/ }))

      const rows = within(batchTable).getAllByRole('row')
      const row1 = within(rows[2]).getAllByRole('cell')
      const row2 = within(rows[3]).getAllByRole('cell')
      const choice1Input = within(row1[1]).getByRole('spinbutton')
      const choice2Input = within(row2[1]).getByRole('spinbutton')
      userEvent.type(choice1Input, '1')
      userEvent.type(choice2Input, '2')

      const saveButton = await screen.findByRole('button', {
        name: /Save/,
      })
      userEvent.click(saveButton)

      await findAndCloseToast('something went wrong: putBatchResults')
      expect(saveButton).toBeInTheDocument()
    })
  })
})
