import React from 'react'
import { screen, within, waitFor } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import BatchInventory from './BatchInventory'
import {
  withMockFetch,
  renderWithRouter,
  createQueryClient,
} from '../testUtilities'
import { IFileInfo } from '../useCSV'
import { fileInfoMocks } from '../_mocks'

jest.mock('axios')

const testCvrFile = new File([''], 'test-cvr.csv', {
  type: 'text/csv',
})
const cvrFormData = new FormData()
cvrFormData.append('cvr', testCvrFile, testCvrFile.name)

const testTabulatorStatusFile = new File([''], 'test-tabulator-status.xml', {
  type: 'application/xml',
})
const tabulatorStatusFormData = new FormData()
tabulatorStatusFormData.append(
  'tabulatorStatus',
  testTabulatorStatusFile,
  testTabulatorStatusFile.name
)

const cvrProcessed: IFileInfo = {
  file: { ...fileInfoMocks.processed.file!, name: testCvrFile.name },
  processing: fileInfoMocks.processed.processing,
}
const tabulatorStatusProcessed: IFileInfo = {
  file: {
    ...fileInfoMocks.processed.file!,
    name: testTabulatorStatusFile.name,
  },
  processing: fileInfoMocks.processed.processing,
}

const apiCalls = {
  getCvr: (fileInfo: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/cvr',
    response: fileInfo,
  }),
  getTabulatorStatus: (fileInfo: IFileInfo) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/tabulator-status',
    response: fileInfo,
  }),
  getSignOff: (signedOffAt: string | null) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/sign-off',
    response: { signedOffAt },
  }),
  putCvr: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/cvr',
    options: {
      method: 'PUT',
      body: cvrFormData,
    },
    response: { status: 'ok' },
  },
  putTabulatorStatus: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/tabulator-status',
    options: {
      method: 'PUT',
      body: tabulatorStatusFormData,
    },
    response: { status: 'ok' },
  },
  postSignOff: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/sign-off',
    options: {
      method: 'POST',
    },
    response: { status: 'ok' },
  },
  deleteSignOff: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/sign-off',
    options: {
      method: 'DELETE',
    },
    response: { status: 'ok' },
  },
}

const render = () =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <Route path="/election/:electionId/jurisdiction/:jurisdictionId/batch-inventory">
        <BatchInventory />
      </Route>
    </QueryClientProvider>,
    { route: '/election/1/jurisdiction/jurisdiction-id-1/batch-inventory' }
  )

const expectToBeOnStep = async (name: string) => {
  await screen.findByRole('heading', {
    name,
    current: 'step',
  })
}

// We test each step in a separate test case in order to ensure that if the user
// returns to the batch inventory flow after leaving on a certain step, they
// will be returned to that step based on the saved data from the previous step.
describe('BatchInventory', () => {
  it('starts with Upload Election Results step', async () => {
    const expectedCalls = [
      apiCalls.getCvr(fileInfoMocks.empty),
      apiCalls.getTabulatorStatus(fileInfoMocks.empty),
      apiCalls.getSignOff(null),
      apiCalls.putCvr,
      apiCalls.getCvr(cvrProcessed),
      apiCalls.getTabulatorStatus(fileInfoMocks.empty),
      apiCalls.putTabulatorStatus,
      apiCalls.getTabulatorStatus(tabulatorStatusProcessed),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await expectToBeOnStep('Upload Election Results')

      const continueButton = screen.getByRole('button', { name: /Continue/ })
      expect(continueButton).toBeDisabled()

      const cvrForm = screen
        .getByText('Cast Vote Records (CVR)')
        .closest('form')!
      const tabulatorStatusForm = screen
        .getByText('Tabulator Status')
        .closest('form')!
      expect(
        within(cvrForm).getByRole('button', { name: /Upload/ })
      ).toBeDisabled()
      expect(
        within(tabulatorStatusForm).getByRole('button', { name: /Upload/ })
      ).toBeDisabled()
      expect(
        within(tabulatorStatusForm).getByLabelText('Select a file...')
      ).toBeDisabled()

      // Upload CVR
      userEvent.upload(
        within(cvrForm).getByLabelText('Select a file...'),
        testCvrFile
      )
      await within(cvrForm).findByText('test-cvr.csv')
      userEvent.click(within(cvrForm).getByRole('button', { name: /Upload/ }))
      await within(cvrForm).findByText('Uploaded')

      expect(continueButton).toBeDisabled()

      // Upload Tabulator Status
      userEvent.upload(
        within(tabulatorStatusForm).getByLabelText('Select a file...'),
        testTabulatorStatusFile
      )
      await within(tabulatorStatusForm).findByText('test-tabulator-status.xml')
      userEvent.click(
        within(tabulatorStatusForm).getByRole('button', { name: /Upload/ })
      )
      await within(tabulatorStatusForm).findByText('Uploaded')

      // Go to the next step
      userEvent.click(continueButton)
      await expectToBeOnStep('Inventory Batches')
    })
  })

  it('continues to Inventory Batches step', async () => {
    const mockDownloadWindow: { onbeforeunload?: () => void } = {}
    window.open = jest.fn().mockReturnValue(mockDownloadWindow)

    const expectedCalls = [
      apiCalls.getCvr(cvrProcessed),
      apiCalls.getTabulatorStatus(tabulatorStatusProcessed),
      apiCalls.getSignOff(null),
      apiCalls.postSignOff,
      apiCalls.getSignOff(new Date().toISOString()),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await expectToBeOnStep('Inventory Batches')

      const backButton = screen.getByRole('button', { name: /Back$/ })
      expect(backButton).toBeEnabled()
      const continueButton = screen.getByRole('button', { name: /Continue/ })
      expect(continueButton).toBeDisabled()

      const signOffCheckbox = screen.getByLabelText(
        'I have completed the batch inventory worksheet.'
      )
      expect(signOffCheckbox).not.toBeChecked()

      // Download worksheet
      userEvent.click(
        screen.getByRole('button', {
          name: /Download Batch Inventory Worksheet/,
        })
      )
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/worksheet'
        )
      })

      // Sign off
      userEvent.click(signOffCheckbox)
      await waitFor(() => {
        expect(signOffCheckbox).toBeChecked()
      })

      // Go to the next step
      userEvent.click(continueButton)
      await expectToBeOnStep('Download Audit Files')
    })
  })

  it('ends with Download Audit Files step', async () => {
    const mockDownloadWindow: { onbeforeunload?: () => void } = {}
    window.open = jest.fn().mockReturnValue(mockDownloadWindow)

    const expectedCalls = [
      apiCalls.getCvr(cvrProcessed),
      apiCalls.getTabulatorStatus(tabulatorStatusProcessed),
      apiCalls.getSignOff(new Date().toISOString()),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByText('Download Audit Files')

      const returnButton = screen.getByRole('button', {
        name: /Return to Audit Setup/,
      })
      expect(returnButton).toBeEnabled()
      expect(returnButton).toHaveAttribute(
        'href',
        '/election/1/jurisdiction/jurisdiction-id-1'
      )

      userEvent.click(
        screen.getByRole('button', { name: /Download Ballot Manifest/ })
      )
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/ballot-manifest'
        )
      })

      userEvent.click(
        screen.getByRole('button', {
          name: /Download Candidate Totals by Batch/,
        })
      )
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          '/api/election/1/jurisdiction/jurisdiction-id-1/batch-inventory/batch-tallies'
        )
      })
    })
  })

  it('can navigate back from each step to the previous', async () => {
    const expectedCalls = [
      apiCalls.getCvr(cvrProcessed),
      apiCalls.getTabulatorStatus(tabulatorStatusProcessed),
      apiCalls.getSignOff(new Date().toISOString()),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await expectToBeOnStep('Download Audit Files')

      userEvent.click(screen.getByRole('button', { name: /Back$/ }))
      await expectToBeOnStep('Inventory Batches')

      userEvent.click(screen.getByRole('button', { name: /Back$/ }))
      await screen.findByText('Upload Election Results')
    })
  })

  it('can undo sign off', async () => {
    const expectedCalls = [
      apiCalls.getCvr(cvrProcessed),
      apiCalls.getTabulatorStatus(tabulatorStatusProcessed),
      apiCalls.getSignOff(new Date().toISOString()),
      apiCalls.deleteSignOff,
      apiCalls.getSignOff(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await expectToBeOnStep('Download Audit Files')

      userEvent.click(screen.getByRole('button', { name: /Back$/ }))
      await expectToBeOnStep('Inventory Batches')

      const signOffCheckbox = screen.getByLabelText(
        'I have completed the batch inventory worksheet.'
      )
      expect(signOffCheckbox).toBeChecked()

      userEvent.click(signOffCheckbox)
      await waitFor(() => {
        expect(signOffCheckbox).not.toBeChecked()
      })
    })
  })

  it('always has a link to go back to Audit Setup', async () => {
    const expectedCalls = [
      apiCalls.getCvr(fileInfoMocks.empty),
      apiCalls.getTabulatorStatus(fileInfoMocks.empty),
      apiCalls.getSignOff(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByText('Upload Election Results')

      const button = screen.getByRole('button', {
        name: /Back to Audit Setup/,
      })
      expect(button).toHaveAttribute(
        'href',
        '/election/1/jurisdiction/jurisdiction-id-1'
      )
    })
  })
})
