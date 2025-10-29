import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from 'vitest'
import React from 'react'
import { screen, waitFor, within } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router-dom'
import copy from 'copy-to-clipboard'
import { Classes } from '@blueprintjs/core'
import * as Sentry from '@sentry/react'
import { ToastContainer } from 'react-toastify'
import { http, HttpResponse } from 'msw'
import {
  renderWithRouter,
  findAndCloseToast,
  createQueryClient,
  typeCode,
} from '../../testUtilities'
import BatchRoundSteps from './BatchRoundSteps'
import { jaApiCalls, contestMocks } from '../../_mocks'
import { roundMocks, batchesMocks } from '../_mocks'
import { server } from '../../../MockServer'

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
  beforeAll(() => {
    server.listen()
  })

  afterEach(() => {
    server.resetHandlers()
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Ensure timers are reset after each test, in case fake timers were used
    vi.useRealTimers()
  })

  it('navigates between steps using buttons or links', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [],
      })
      .addContest(contestMocks.one[0])

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

  it('defaults to Enter Tallies step if any tallies have been entered', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ],
      })
      .addContest(contestMocks.one[0])

    renderComponent()
    await screen.findByRole('heading', {
      name: 'Enter Tallies',
      current: 'step',
    })
  })

  it('shows Step 1: Prepare Batches', async () => {
    const mockDownloadWindow: { onbeforeunload?: () => void } = {}
    window.open = vi.fn().mockReturnValue(mockDownloadWindow)

    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [],
      })
      .addContest(contestMocks.one[0])

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

  it('handles failures to generate batch tally sheets PDF', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [],
      })
      .addContest(contestMocks.one[0])

    mockSavePDF.mockImplementationOnce(() => Promise.reject(new Error('Whoa!')))
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

  it('handles failures to generate stack labels PDF', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [],
      })
      .addContest(contestMocks.one[0])

    mockSavePDF.mockImplementationOnce(() => Promise.reject(new Error('Whoa!')))
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

  it('shows Step 2: Set Up Tally Entry Accounts', async () => {
    server.addBatch({
      id: 'batch-1',
      lastEditedBy: null,
      name: 'Batch One',
      numBallots: 100,
      resultTallySheets: [],
    })

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
    const expectedLoginLink = `${window.location.origin
      }/tallyentry/${server.getTallyAccountPassphrase()}`
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

  it('on Step 2, polls for login requests and can confirm/reject a request with MSW', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: null,
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [],
      })
      .setTallyAccountPassphrase('fake-passphrase-four-words')

    renderComponent('/tally-entry-accounts')
    await screen.findByRole('heading', {
      name: 'Set Up Tally Entry Accounts',
      current: 'step',
    })

    // On first poll, no requests
    screen.getByText('No tally entry accounts have logged in yet')

    // Transition from no login requests to multiple unconfirmed requests
    server
      .addLoginRequest({
        tallyEntryUserId: 'tally-entry-user-id-1',
        members: [
          { name: 'John Doe', affiliation: 'DEM' },
          { name: 'Jane Smith', affiliation: null },
        ],
        loginConfirmedAt: null,
        pin: '123',
      })
      .addLoginRequest({
        tallyEntryUserId: 'tally-entry-user-id-2',
        members: [{ name: 'Kevin Jones', affiliation: 'IND' }],
        loginConfirmedAt: null,
        pin: '123',
      })

    // On next poll, two login requests
    // vi.advanceTimersByTime(1000)
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
    typeCode(loginCodeInput, '456')
    const digitInputs = within(loginCodeInput).getAllByRole('textbox')
    expect(digitInputs[0]).toHaveValue('4')
    expect(digitInputs[1]).toHaveValue('5')
    expect(digitInputs[2]).toHaveValue('6')
    userEvent.click(confirmButton)
    await within(dialog).findByText('Invalid code, please try again.')

    // Code should be cleared
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')

    // Confirm successfully
    typeCode(loginCodeInput, '123')
    userEvent.click(confirmButton)
    await screen.findByText('Login Confirmed')
    screen.getAllByRole('button', { name: 'Close' })

    // The dialog auto-closes after a bit
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
  })

  it('shows Step 3: Enter Tallies', async () => {
    server
      .addBatch(batchesMocks.emptyInitial.batches[0])
      .addContest(contestMocks.one[0])

    renderComponent('/enter-tallies')
    await screen.findByRole('heading', {
      name: 'Enter Tallies',
      current: 'step',
    })

    expect(screen.getAllByText('Batch One')).toHaveLength(2)
    // Comprehensive tests are in BatchRoundTallyEntry.test.tsx
  })

  it('on Step 3, confirms finalizing tallies', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: 'ja@example.com',
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ],
      })
      .addContest(contestMocks.one[0])

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

  it('handles errors on finalize', async () => {
    server
      .addBatch({
        id: 'batch-1',
        lastEditedBy: 'ja@example.com',
        name: 'Batch One',
        numBallots: 100,
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ],
      })
      .addContest(contestMocks.one[0])
      // override the default `MockServer` behavior
      .use(
        http.post(jaApiCalls.finalizeBatchResults.url, () =>
          HttpResponse.json(
            {
              errors: [
                {
                  errorType: 'Server Error',
                  message: `something went wrong: finalizeBatchResults`,
                },
              ],
            },
            { status: 500 }
          )
        )
      )

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
