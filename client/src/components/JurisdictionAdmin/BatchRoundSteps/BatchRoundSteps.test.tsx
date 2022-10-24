import React from 'react'
import { screen, waitFor, within } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router-dom'
import copy from 'copy-to-clipboard'
import { Classes } from '@blueprintjs/core'
import * as Sentry from '@sentry/react'
import { ToastContainer } from 'react-toastify'
import {
  renderWithRouter,
  withMockFetch,
  findAndCloseToast,
  serverError,
  createQueryClient,
} from '../../testUtilities'
import BatchRoundSteps from './BatchRoundSteps'
import { jaApiCalls } from '../../_mocks'
import {
  roundMocks,
  batchesMocks,
  tallyEntryAccountStatusMocks,
} from '../_mocks'
import { contestMocks } from '../../AuditAdmin/useSetupMenuItems/_mocks'

jest.mock('copy-to-clipboard', () => jest.fn(() => true))

const mockSavePDF = jest.fn()
jest.mock('jspdf', () => {
  const { jsPDF } = jest.requireActual('jspdf')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function mockJsPDF(options?: any) {
    return {
      ...new jsPDF(options),
      addImage: jest.fn(),
      save: mockSavePDF,
    }
  }
})

jest.mock('@sentry/react', () => ({
  captureException: jest.fn(),
}))

const renderComponent = (stepPath = '') => {
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <Route path="/election/:electionId/jurisdiction/:jurisdictionId/round/:roundId">
        <BatchRoundSteps
          jurisdiction={jaApiCalls.getUser.response.user.jurisdictions[0]}
          round={roundMocks.incomplete}
        />
      </Route>
      <ToastContainer />
    </QueryClientProvider>,
    {
      route: `/election/1/jurisdiction/jurisdiction-id-1/round/round-1${stepPath}`,
    }
  )
}

describe('BatchRoundSteps', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('navigates between steps using buttons or links', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.turnedOff
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()

      // Continue buttons
      await screen.findByRole('heading', {
        name: 'Prepare Batches',
        current: 'step',
      })
      userEvent.click(screen.getByRole('button', { name: /Continue/ }))
      await screen.findByRole('heading', {
        name: 'Set Up Tally Entry Accounts',
        current: 'step',
      })
      userEvent.click(screen.getByRole('button', { name: /Continue/ }))
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })
      expect(
        screen.queryByRole('button', { name: /Continue/ })
      ).not.toBeInTheDocument()

      // Back buttons
      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', {
        name: 'Set Up Tally Entry Accounts',
        current: 'step',
      })
      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', {
        name: 'Prepare Batches',
        current: 'step',
      })
      expect(
        screen.queryByRole('button', { name: /Back/ })
      ).not.toBeInTheDocument()

      // Step title links
      userEvent.click(screen.getByRole('link', { name: 'Enter Tallies' }))
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })
      userEvent.click(
        screen.getByRole('link', { name: 'Set Up Tally Entry Accounts' })
      )
      await screen.findByRole('heading', {
        name: 'Set Up Tally Entry Accounts',
        current: 'step',
      })
      userEvent.click(screen.getByRole('link', { name: 'Prepare Batches' }))
      await screen.findByRole('heading', {
        name: 'Prepare Batches',
        current: 'step',
      })
    })
  })

  it('shows Step 1: Prepare Batches', async () => {
    const mockDownloadWindow: { onbeforeunload?: () => void } = {}
    window.open = jest.fn().mockReturnValue(mockDownloadWindow)

    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/prepare-batches')
      await screen.findByRole('heading', {
        name: 'Prepare Batches',
        current: 'step',
      })

      // Download batch retrieval list
      screen.getByRole('heading', { name: 'Retrieve Batches from Storage' })
      const batchRetrievalListButton = screen.getByRole('button', {
        name: /Download Batch Retrieval List/,
      })
      userEvent.click(batchRetrievalListButton)
      expect(batchRetrievalListButton).toBeDisabled()
      await waitFor(() => expect(window.open).toHaveBeenCalledTimes(1))
      expect(window.open).toBeCalledWith(
        '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/retrieval-list'
      )
      mockDownloadWindow.onbeforeunload!()
      await waitFor(() => expect(batchRetrievalListButton).toBeEnabled())

      // Download batch tally sheets
      screen.getByRole('heading', { name: 'Print Batch Tally Sheets' })
      const batchTallySheetButton = screen.getByRole('button', {
        name: /Download Batch Tally Sheets/,
      })
      userEvent.click(batchTallySheetButton)
      expect(batchTallySheetButton).toBeDisabled()
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Batch Tally Sheets - Jurisdiction One - audit one.pdf',
          {
            returnPromise: true,
          }
        )
      )
      expect(batchTallySheetButton).toBeEnabled()
    })
  })

  it('handles failures to generate batch tally sheets PDF', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
    ]
    mockSavePDF.mockImplementationOnce(() => Promise.reject(new Error('Whoa!')))
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/prepare-batches')

      userEvent.click(
        await screen.findByRole('button', {
          name: /Download Batch Tally Sheets/,
        })
      )
      await findAndCloseToast('Error preparing batch tally sheets for download')
      await waitFor(() =>
        expect(Sentry.captureException).toHaveBeenCalledTimes(1)
      )
    })
  })

  it('shows Step 2: Set Up Tally Entry Accounts', async () => {
    const expectedCalls = [
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.turnedOff
      ),
      jaApiCalls.postTurnOnTallyEntryAccounts,
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.noLoginRequests
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/tally-entry-accounts')
      await screen.findByRole('heading', {
        name: 'Set Up Tally Entry Accounts',
        current: 'step',
      })

      // When tally entry accounts turned off, prompt to turn them on
      screen.getByText('Do you want to set up tally entry accounts?')
      const skipButton = screen.getByRole('button', { name: /Skip/ })
      expect(skipButton).toHaveAttribute(
        'href',
        '/election/1/jurisdiction/jurisdiction-id-1/round/round-1/enter-tallies'
      )
      const yesButton = await screen.findByRole('button', {
        name: /Set Up Tally Entry Accounts/,
      })
      userEvent.click(yesButton)

      // Once they are turned on, show login link
      await screen.findByRole('heading', {
        name: 'Share Tally Entry Login Link',
      })
      const loginLinkInput = screen.getByRole('textbox')
      const expectedLoginLink = `${window.location.origin}/tallyentry/${tallyEntryAccountStatusMocks.noLoginRequests.passphrase}`
      expect(loginLinkInput).toHaveValue(expectedLoginLink)
      expect(loginLinkInput).toHaveAttribute('readonly')

      const copyLinkButton = screen.getByRole('button', { name: /Copy Link/ })
      userEvent.click(copyLinkButton)
      expect(copy).toHaveBeenCalledWith(expectedLoginLink, {
        format: 'text/plain',
      })

      const downloadPrintoutButton = screen.getByRole('button', {
        name: /Download Printout/,
      })
      userEvent.click(downloadPrintoutButton)
      expect(downloadPrintoutButton).toBeDisabled()
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Tally Entry Login Link - Jurisdiction One - audit one.pdf',
          {
            returnPromise: true,
          }
        )
      )
      expect(downloadPrintoutButton).toBeEnabled()

      // And show login requests
      screen.getByRole('heading', { name: 'Confirm Tally Entry Accounts' })
      screen.getByText('No tally entry accounts have logged in yet')
    })
  })

  it('on Step 2, polls for login requests and can confirm a request', async () => {
    jest.useFakeTimers()
    const expectedCalls = [
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.noLoginRequests
      ),
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsUnconfirmed
      ),
      {
        ...jaApiCalls.postConfirmTallyEntryLoginCode,
        response: {
          errors: [
            {
              errorType: 'Bad Request',
              message: 'Invalid code, please try again.',
            },
          ],
        },
        error: { status: 400, statusText: 'Bad Request' },
      },
      jaApiCalls.postConfirmTallyEntryLoginCode,
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
      ),
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/tally-entry-accounts')
      await screen.findByRole('heading', {
        name: 'Set Up Tally Entry Accounts',
        current: 'step',
      })

      // On first poll, no requests
      screen.getByText('No tally entry accounts have logged in yet')

      // On next poll, two login requests
      jest.advanceTimersByTime(1000)
      let loginRequest1 = (await screen.findByText('John Doe')).closest(
        `.${Classes.CARD}`
      ) as HTMLElement
      within(loginRequest1).getByText('Jane Smith')

      const loginRequest2 = (await screen.findByText('Kevin Jones')).closest(
        `.${Classes.CARD}`
      ) as HTMLElement

      // Confirm the first request
      const enterCodeButton = within(loginRequest1).getByRole('button', {
        name: /Enter Login Code/,
      })
      userEvent.click(enterCodeButton)

      let dialog = screen
        .getByRole('heading', { name: 'Confirm Login: John Doe, Jane Smith' })
        .closest(`.${Classes.DIALOG}`) as HTMLElement
      const loginCodeInput = within(dialog).getByLabelText(
        'Enter the login code shown on their screen:'
      )
      const confirmButton = within(dialog).getByRole('button', {
        name: /Confirm/,
      })

      // Try to confirm without a code
      userEvent.click(confirmButton)
      await within(dialog).findByText('Enter a 3-digit login code')

      // Try an invalid code
      userEvent.type(loginCodeInput, '123')
      userEvent.click(confirmButton)
      await within(dialog).findByText('Invalid code, please try again.')

      // Confirm successfully
      // (we use the same code, but the request mock is set up to succeed this time)
      userEvent.click(confirmButton)
      await screen.findByText('Login Confirmed')
      screen.getAllByRole('button', { name: 'Close' })

      // The dialog auto-closes after a bit
      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(
          screen.queryByText('Confirm Login: John Doe, Jane Smith')
        ).not.toBeInTheDocument()
      })

      loginRequest1 = (await screen.findByText('John Doe')).closest(
        `.${Classes.CARD}`
      ) as HTMLElement
      within(loginRequest1).getByText('Logged In')

      // Open and close the second request's dialog
      userEvent.click(
        within(loginRequest2).getByRole('button', { name: /Enter Login Code/ })
      )
      dialog = (await screen.findByText('Confirm Login: Kevin Jones')).closest(
        `.${Classes.DIALOG}`
      ) as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: /Cancel/ }))
      await waitFor(() => {
        expect(
          screen.queryByText('Confirm Login: Kevin Jones')
        ).not.toBeInTheDocument()
      })

      jest.useRealTimers()
    })
  })

  it('shows Step 3: Enter Tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/enter-tallies')
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })

      screen.getByText(
        'For each batch, enter the number of votes tallied for each candidate/choice.'
      )
      screen.getByText('Batch One')
      // TODO fill in comprehensive tests once the tally entry interface is finalized

      const finalizeButton = screen.getByRole('button', {
        name: /Finalize Tallies/,
      })
      userEvent.click(finalizeButton)
      await findAndCloseToast(
        'Please enter tallies for all batches before finalizing.'
      )
    })
  })

  it('on Step 3, confirms finalizing tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
      jaApiCalls.finalizeBatchResults,
      jaApiCalls.getBatches(batchesMocks.complete),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/enter-tallies')
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })
      await screen.findByRole('table')

      const finalizeButton = screen.getByRole('button', {
        name: /Finalize Tallies/,
      })
      userEvent.click(finalizeButton)

      const dialog = (
        await screen.findByRole('heading', {
          name: 'Are you sure you want to finalize your tallies?',
        })
      ).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: 'Confirm' }))

      await screen.findByText('Tallies finalized')
      expect(finalizeButton).toBeDisabled()
    })
  })

  it('handles errors on finalize', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      jaApiCalls.getJurisdictionContests(contestMocks.oneTargeted),
      serverError('finalizeBatchResults', jaApiCalls.finalizeBatchResults),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/enter-tallies')
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })

      const finalizeButton = screen.getByRole('button', {
        name: /Finalize Tallies/,
      })
      userEvent.click(finalizeButton)

      const dialog = (
        await screen.findByRole('heading', {
          name: 'Are you sure you want to finalize your tallies?',
        })
      ).closest('.bp3-dialog')! as HTMLElement
      userEvent.click(within(dialog).getByRole('button', { name: 'Confirm' }))
      await findAndCloseToast('something went wrong: finalizeBatchResults')
    })
  })
})
