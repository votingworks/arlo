import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
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
  typeCode,
} from '../../testUtilities'
import BatchRoundSteps from './BatchRoundSteps'
import { jaApiCalls, contestMocks } from '../../_mocks'
import {
  roundMocks,
  batchesMocks,
  tallyEntryAccountStatusMocks,
} from '../_mocks'

vi.mock(import('copy-to-clipboard'), async importActual => ({
  ...(await importActual()),
  default: vi.fn(() => true),
}))

const mockSavePDF = vi.fn()
vi.mock('jspdf', async () => {
  const { jsPDF } = (await vi.importActual('jspdf')) as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function mockJsPDF(options?: any) {
    return {
      ...new jsPDF(options),
      addImage: vi.fn(),
      save: mockSavePDF,
    }
  }
  return { default: mockJsPDF, jsPDF: mockJsPDF }
})

vi.mock('@sentry/react', () => ({
  captureException: vi.fn(),
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
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Ensure timers are reset after each test, in case fake timers were used
    vi.useRealTimers()
  })

  it('navigates between steps using buttons or links', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.turnedOff
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()

      // Defaults to Prepare Batches
      await screen.findByRole('heading', {
        name: 'Prepare Batches',
        current: 'step',
      })

      // Continue buttons
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

  it('defaults to Enter Tallies step if any tallies have been entered', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.complete),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent()
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })
    })
  })

  it('shows Step 1: Prepare Batches', async () => {
    const mockDownloadWindow: { onbeforeunload?: () => void } = {}
    window.open = vi.fn().mockReturnValue(mockDownloadWindow)

    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
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

      // Download stack labels
      screen.getByRole('heading', { name: 'Print Stack Labels' })
      const StackLabelsButton = screen.getByRole('button', {
        name: /Download Stack Labels/,
      })
      userEvent.click(StackLabelsButton)
      expect(StackLabelsButton).toBeDisabled()
      await waitFor(() =>
        expect(mockSavePDF).toHaveBeenCalledWith(
          'Stack Labels - Jurisdiction One - audit one.pdf',
          {
            returnPromise: true,
          }
        )
      )
      expect(StackLabelsButton).toBeEnabled()
    })
  })

  it('handles failures to generate batch tally sheets PDF', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
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

  it('handles failures to generate stack labels PDF', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
    ]
    mockSavePDF.mockImplementationOnce(() => Promise.reject(new Error('Whoa!')))
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/prepare-batches')

      userEvent.click(
        await screen.findByRole('button', {
          name: /Download Stack Labels/,
        })
      )
      await findAndCloseToast('Error preparing stack labels for download')
      await waitFor(() =>
        expect(Sentry.captureException).toHaveBeenCalledTimes(1)
      )
    })
  })

  // FIXME: Unskip this in CI once we have more flexible fetch mocking.
  // This test runs the app in such a way that the order of requests
  // is not deterministic, so our inflexible `fetch` mocking can't properly
  // mock requests for this test in a non-flaky way.
  ;(process.env.CI ? it.skip : it)(
    'shows Step 2: Set Up Tally Entry Accounts',
    async () => {
      const expectedCalls = [
        jaApiCalls.getBatches(batchesMocks.emptyInitial),
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
    }
  )

  it('on Step 2, polls for login requests and can confirm/reject a request', async () => {
    vi.useFakeTimers()

    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
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
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsUnconfirmed
      ),
      jaApiCalls.postConfirmTallyEntryLoginCode,
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
      ),
      jaApiCalls.getTallyEntryAccountStatus(
        tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
      ),
      jaApiCalls.postRejectTallyEntryLoginRequest,
      jaApiCalls.getTallyEntryAccountStatus({
        ...tallyEntryAccountStatusMocks.loginRequestsOneConfirmed,
        loginRequests: [
          tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
            .loginRequests[0],
        ],
      }),
      jaApiCalls.getTallyEntryAccountStatus({
        ...tallyEntryAccountStatusMocks.loginRequestsOneConfirmed,
        loginRequests: [
          tallyEntryAccountStatusMocks.loginRequestsOneConfirmed
            .loginRequests[0],
        ],
      }),
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
      vi.advanceTimersByTime(1000)
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
      typeCode(loginCodeInput, '123')
      const digitInputs = within(loginCodeInput).getAllByRole('textbox')
      expect(digitInputs[0]).toHaveValue('1')
      expect(digitInputs[1]).toHaveValue('2')
      expect(digitInputs[2]).toHaveValue('3')
      userEvent.click(confirmButton)
      await within(dialog).findByText('Invalid code, please try again.')

      // Code should be cleared
      expect(digitInputs[0]).toHaveValue('')
      expect(digitInputs[1]).toHaveValue('')
      expect(digitInputs[2]).toHaveValue('')

      // Confirm successfully
      // (we use the same code, but the request mock is set up to succeed this time)
      typeCode(loginCodeInput, '123')
      userEvent.click(confirmButton)
      await screen.findByText('Login Confirmed')
      screen.getAllByRole('button', { name: 'Close' })

      // The dialog auto-closes after a bit
      vi.advanceTimersByTime(1000)
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

      // Reject the request
      const rejectButton = screen.getByRole('button', {
        name: 'Reject login request',
      })
      userEvent.click(rejectButton)
      await waitFor(() => {
        expect(loginRequest2).not.toBeInTheDocument()
      })

      vi.useRealTimers()
    })
  })

  it('shows Step 3: Enter Tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches(batchesMocks.emptyInitial),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderComponent('/enter-tallies')
      await screen.findByRole('heading', {
        name: 'Enter Tallies',
        current: 'step',
      })

      expect(screen.getAllByText('Batch One')).toHaveLength(2)
      // Comprehensive tests are in BatchRoundTallyEntry.test.tsx
    })
  })

  it('on Step 3, confirms finalizing tallies', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
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

      screen.getByText('All batches audited')
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
      expect(finalizeButton).not.toBeInTheDocument()
    })
  })

  it('handles errors on finalize', async () => {
    const expectedCalls = [
      jaApiCalls.getBatches({
        ...batchesMocks.complete,
        resultsFinalizedAt: null,
      }),
      jaApiCalls.getJurisdictionContests(contestMocks.one),
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
