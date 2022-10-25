import React from 'react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { ToastContainer } from 'react-toastify'

import AuditPlanner from './AuditPlanner'
import {
  renderWithRouter,
  serverError,
  withMockFetch,
  createQueryClient,
} from '../../testUtilities'

function renderAuditPlanner() {
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <AuditPlanner />
      <ToastContainer />
    </QueryClientProvider>,
    { route: '/planner' }
  )
}

async function areExpectedErrorMessagesDisplayed({
  displayed,
  notDisplayed = [],
}: {
  displayed: string[]
  notDisplayed?: string[]
}) {
  const counts: { [message: string]: number } = {}
  for (const message of displayed) {
    counts[message] = counts[message] ? counts[message] + 1 : 1
  }
  for (const message of displayed) {
    // eslint-disable-next-line no-await-in-loop
    await waitFor(() =>
      expect(screen.getAllByText(message)).toHaveLength(counts[message])
    )
  }

  for (const message of notDisplayed) {
    // eslint-disable-next-line no-await-in-loop
    await waitFor(() =>
      expect(screen.queryByText(message)).not.toBeInTheDocument()
    )
  }
}

async function checkThatElectionResultsCardIsInInitialState() {
  screen.getByRole('heading', { name: 'Election Results' })

  expect(screen.getAllByRole('row')).toHaveLength(
    // 1 header row + 2 candidate rows + 1 row for 'Add Candidate' button + 1 row for additional
    // inputs
    5
  )
  screen.getByRole('columnheader', { name: 'Candidate' })
  screen.getByRole('columnheader', { name: 'Votes' })
  const candidate1NameInput = screen.getByRole('textbox', {
    name: 'Candidate 1 Name',
  })
  const candidate1VotesInput = screen.getByRole('spinbutton', {
    name: 'Candidate 1 Votes',
  })
  const candidate1RemoveButton = screen.getByRole('button', {
    name: 'Remove Candidate 1',
  })
  const candidate2NameInput = screen.getByRole('textbox', {
    name: 'Candidate 2 Name',
  })
  const candidate2VotesInput = screen.getByRole('spinbutton', {
    name: 'Candidate 2 Votes',
  })
  const candidate2RemoveButton = screen.getByRole('button', {
    name: 'Remove Candidate 2',
  })
  expect(candidate1NameInput).toHaveValue('Candidate 1')
  expect(candidate1VotesInput).toHaveValue(null)
  expect(candidate1RemoveButton).toBeDisabled()
  expect(candidate2NameInput).toHaveValue('Candidate 2')
  expect(candidate2VotesInput).toHaveValue(null)
  expect(candidate2RemoveButton).toBeDisabled()
  const addCandidateButton = screen.getByRole('button', {
    name: /Add Candidate/,
  })
  const numberOfWinnersInput = screen.getByRole('spinbutton', {
    name: 'Number of Winners',
  })
  const totalBallotsCastInput = screen.getByRole('spinbutton', {
    name: 'Total Ballots Cast',
  })
  expect(numberOfWinnersInput).toHaveValue(1)
  expect(totalBallotsCastInput).toHaveValue(null)

  const clearButton = screen.getByRole('button', { name: 'Clear' })
  const planAuditButton = screen.getByRole('button', { name: 'Plan Audit' })

  return {
    candidate1NameInput,
    candidate1VotesInput,
    candidate1RemoveButton,
    candidate2NameInput,
    candidate2VotesInput,
    candidate2RemoveButton,
    addCandidateButton,
    numberOfWinnersInput,
    totalBallotsCastInput,
    clearButton,
    planAuditButton,
  }
}

function moveSlider(
  sliderHandle: HTMLElement,
  direction: 'left' | 'right',
  positions = 1
) {
  for (let i = 0; i < positions; i += 1) {
    switch (direction) {
      case 'left': {
        fireEvent.keyDown(sliderHandle, { key: 'ArrowLeft', keyCode: 37 })
        fireEvent.keyUp(sliderHandle, { key: 'ArrowLeft', keyCode: 37 })
        break
      }
      case 'right': {
        fireEvent.keyDown(sliderHandle, { key: 'ArrowRight', keyCode: 39 })
        fireEvent.keyUp(sliderHandle, { key: 'ArrowRight', keyCode: 39 })
        break
      }
      default: {
        const exhaustiveCheck: never = direction
        throw new Error(`Unhandled direction: ${exhaustiveCheck}`)
      }
    }
  }
}

const body1 = JSON.stringify({
  electionResults: {
    candidates: [
      { name: 'Helga Hippo', votes: 1000 },
      { name: 'Bobby Bear', votes: 900 },
    ],
    numWinners: 1,
    totalBallotsCast: 2000,
  },
})

const body2 = JSON.stringify({
  electionResults: {
    candidates: [
      { name: 'Helga Hippopotamus', votes: 1000 },
      { name: 'Bobby Bear', votes: 901 },
    ],
    numWinners: 1,
    totalBallotsCast: 2001,
  },
})

const apiMocks = {
  publicComputeSampleSizes1: {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body1,
      headers: { 'Content-Type': 'application/json' },
    },
    response: {
      ballotComparison: { '0': 2000, '5': 1000, '6': 1006 },
      ballotPolling: { '0': 2000, '5': 1001, '6': 1007 },
      batchComparison: { '0': 2000, '5': 1002, '6': 1008 },
    },
  },
  publicComputeSampleSizes2: {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body2,
      headers: { 'Content-Type': 'application/json' },
    },
    response: {
      ballotComparison: { '5': 1003 },
      ballotPolling: { '5': 1004 },
      batchComparison: { '5': 1005 },
    },
  },
  publicComputeSampleSizesError: serverError('publicComputeSampleSizes', {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body1,
      headers: { 'Content-Type': 'application/json' },
    },
  }),
}

jest.mock(
  '../../../utils/responsiveness',
  (): typeof import('../../../utils/responsiveness') => {
    return {
      ...jest.requireActual('../../../utils/responsiveness'),
      useCssBreakpoints: () => ({
        isMobileWidth: false,
        isTabletWidth: false,
        isDesktopWidth: true,
      }),
    }
  }
)
let mockScrollIntoView: jest.Mock

beforeEach(async () => {
  mockScrollIntoView = jest.fn()
  window.HTMLElement.prototype.scrollIntoView = mockScrollIntoView
})

test('Entering election results - validation and submit', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizes1]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const {
      candidate1NameInput,
      candidate1VotesInput,
      candidate2NameInput,
      candidate2VotesInput,
      numberOfWinnersInput,
      totalBallotsCastInput,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    // Failed submissions
    userEvent.click(planAuditButton)
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required', 'Required', 'Required'],
    })
    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Helga Hippo')
    await areExpectedErrorMessagesDisplayed({
      displayed: [
        'Candidates must have unique names',
        'Required',
        'Required',
        'Required',
      ],
    })
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required', 'Required', 'Required'],
      notDisplayed: ['Candidates must have unique names'],
    })
    userEvent.type(candidate1VotesInput, '0')
    userEvent.type(candidate2VotesInput, '0')
    userEvent.type(totalBallotsCastInput, '1')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['At least 1 candidate must have greater than 0 votes'],
      notDisplayed: ['Required'],
    })
    userEvent.clear(candidate1VotesInput)
    userEvent.type(candidate1VotesInput, '-1')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be less than 0'],
      notDisplayed: ['At least 1 candidate must have greater than 0 votes'],
    })
    userEvent.clear(candidate1VotesInput)
    userEvent.type(candidate1VotesInput, '10000000000000000')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Too large'],
      notDisplayed: ['Cannot be less than 0'],
    })
    userEvent.clear(candidate1VotesInput)
    userEvent.type(candidate1VotesInput, '1000.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Too large'],
    })
    userEvent.clear(candidate1VotesInput)
    userEvent.type(candidate1VotesInput, '1000')
    await areExpectedErrorMessagesDisplayed({
      displayed: [],
      notDisplayed: ['Can only contain numeric characters'],
    })
    userEvent.clear(candidate2VotesInput)
    userEvent.type(candidate2VotesInput, '900')
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '0')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be less than 1'],
    })
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '10000000000000000')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Too large'],
      notDisplayed: ['Cannot be less than 1'],
    })
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '2000.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Too large'],
    })
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '2000')
    await areExpectedErrorMessagesDisplayed({
      displayed: [],
      notDisplayed: ['Can only contain numeric characters'],
    })
    userEvent.clear(numberOfWinnersInput)
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required'],
    })
    userEvent.type(numberOfWinnersInput, '0')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be less than 1'],
      notDisplayed: ['Required'],
    })
    userEvent.clear(numberOfWinnersInput)
    userEvent.type(numberOfWinnersInput, '2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Must be less than number of candidates'],
      notDisplayed: ['Cannot be less than 1'],
    })
    userEvent.clear(numberOfWinnersInput)
    userEvent.type(numberOfWinnersInput, '1.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Must be less than number of candidates'],
    })
    userEvent.clear(numberOfWinnersInput)
    userEvent.type(numberOfWinnersInput, '1')
    await areExpectedErrorMessagesDisplayed({
      displayed: [],
      notDisplayed: ['Can only contain numeric characters'],
    })

    // Successful submission
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )
    const electionResultsCard = screen.getByTestId('electionResultsCard')
    const textInputs = within(electionResultsCard).queryAllByRole('textbox')
    expect(textInputs).toHaveLength(6)
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    expect(textInputs[0]).toHaveValue('Helga Hippo') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('1,000') // Candidate 0 votes
    expect(textInputs[2]).toHaveValue('Bobby Bear') // Candidate 1 name
    expect(textInputs[3]).toHaveValue('900') // Candidate 1 votes
    expect(textInputs[4]).toHaveValue('1') // Number of winners
    expect(textInputs[5]).toHaveValue('2,000') // Total ballots cast
    screen.getByRole('button', { name: 'Clear' })
    screen.getByRole('button', { name: 'Edit' })
    await screen.findByText('1,001 ballots')
  })
})

test('Entering election results - adding and removing candidates', async () => {
  await withMockFetch([], async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const {
      addCandidateButton,
    } = await checkThatElectionResultsCardIsInInitialState()
    // 1 header row + 2 candidate rows + 1 row for 'Add Candidate' button + 1 row for additional
    // inputs
    const initialNumRows = 5

    // Add candidate
    userEvent.click(addCandidateButton)
    await waitFor(() =>
      expect(screen.getAllByRole('row')).toHaveLength(initialNumRows + 1)
    )
    expect(
      screen.getByRole('textbox', { name: 'Candidate 3 Name' })
    ).toHaveValue('Candidate 3')
    expect(
      screen.getByRole('spinbutton', { name: 'Candidate 3 Votes' })
    ).toHaveValue(null)
    const candidate3RemoveButton = screen.getByRole('button', {
      name: 'Remove Candidate 3',
    })

    // Remove candidate
    userEvent.click(candidate3RemoveButton)
    await waitFor(() =>
      expect(screen.getAllByRole('row')).toHaveLength(initialNumRows)
    )
    expect(
      screen.queryByRole('textbox', { name: 'Candidate 3 Name' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('spinbutton', { name: 'Candidate 3 Votes' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('textbox', { name: 'Remove Candidate 3' })
    ).not.toBeInTheDocument()
  })
})

test('Entering election results - clearing', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizes1]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    let {
      candidate1NameInput,
      candidate1VotesInput,
      candidate2NameInput,
      candidate2VotesInput,
      addCandidateButton,
      numberOfWinnersInput,
      totalBallotsCastInput,
      clearButton,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    // Enter election results but don't submit
    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.type(candidate1VotesInput, '1000')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    userEvent.type(candidate2VotesInput, '900')
    userEvent.click(addCandidateButton)
    userEvent.type(numberOfWinnersInput, '2')
    userEvent.type(totalBallotsCastInput, '2000')

    // Clearing before submission
    userEvent.click(clearButton)
    let confirmDialog = (
      await screen.findByRole('heading', { name: 'Confirm' })
    ).closest('.bp3-dialog')! as HTMLElement
    within(confirmDialog).getByText(
      'Are you sure you want to clear and start over?'
    )
    userEvent.click(
      within(confirmDialog).getByRole('button', { name: 'Clear' })
    )
    await waitFor(() => expect(confirmDialog).not.toBeInTheDocument())
    ;({
      candidate1NameInput,
      candidate1VotesInput,
      candidate2NameInput,
      candidate2VotesInput,
      addCandidateButton,
      numberOfWinnersInput,
      totalBallotsCastInput,
      clearButton,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState())

    // Enter election results and submit
    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.type(candidate1VotesInput, '1000')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    userEvent.type(candidate2VotesInput, '900')
    userEvent.type(totalBallotsCastInput, '2000')
    userEvent.click(planAuditButton)
    await screen.findByText('1,001 ballots')

    // Clearing after submission
    userEvent.click(clearButton)
    confirmDialog = (
      await screen.findByRole('heading', { name: 'Confirm' })
    ).closest('.bp3-dialog')! as HTMLElement
    within(confirmDialog).getByText(
      'Are you sure you want to clear and start over?'
    )
    userEvent.click(
      within(confirmDialog).getByRole('button', { name: 'Clear' })
    )
    await waitFor(() => expect(confirmDialog).not.toBeInTheDocument())
    ;({
      candidate1NameInput,
      candidate1VotesInput,
      candidate2NameInput,
      candidate2VotesInput,
      addCandidateButton,
      numberOfWinnersInput,
      totalBallotsCastInput,
      clearButton,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState())
  })
})

test('Entering election results - editing', async () => {
  const expectedCalls = [
    apiMocks.publicComputeSampleSizes1,
    apiMocks.publicComputeSampleSizes2,
  ]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const elements = await checkThatElectionResultsCardIsInInitialState()
    const { candidate1VotesInput, candidate2NameInput } = elements
    let {
      candidate1NameInput,
      candidate2VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = elements

    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.type(candidate1VotesInput, '1000')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    userEvent.type(candidate2VotesInput, '900')
    userEvent.type(totalBallotsCastInput, '2000')
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )
    let electionResultsCard = screen.getByTestId('electionResultsCard')
    let textInputs = within(electionResultsCard).queryAllByRole('textbox')
    expect(textInputs).toHaveLength(6)
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    expect(textInputs[0]).toHaveValue('Helga Hippo') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('1,000') // Candidate 0 votes
    expect(textInputs[2]).toHaveValue('Bobby Bear') // Candidate 1 name
    expect(textInputs[3]).toHaveValue('900') // Candidate 1 votes
    expect(textInputs[4]).toHaveValue('1') // Number of winners
    expect(textInputs[5]).toHaveValue('2,000') // Total ballots cast
    await screen.findByText('1,001 ballots')

    const editButton = screen.getByRole('button', { name: 'Edit' })
    userEvent.click(editButton)
    planAuditButton = await screen.findByRole('button', {
      name: 'Plan Audit',
    })
    candidate1NameInput = screen.getByRole('textbox', {
      name: 'Candidate 1 Name',
    })
    candidate2VotesInput = screen.getByRole('spinbutton', {
      name: 'Candidate 2 Votes',
    })
    totalBallotsCastInput = screen.getByRole('spinbutton', {
      name: 'Total Ballots Cast',
    })
    userEvent.type(candidate1NameInput, 'potamus')
    userEvent.clear(candidate2VotesInput)
    userEvent.type(candidate2VotesInput, '901')
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '2001')
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )
    electionResultsCard = screen.getByTestId('electionResultsCard')
    textInputs = within(electionResultsCard).queryAllByRole('textbox')
    expect(textInputs).toHaveLength(6)
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    expect(textInputs[0]).toHaveValue('Helga Hippopotamus') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('1,000') // Candidate 0 votes
    expect(textInputs[2]).toHaveValue('Bobby Bear') // Candidate 1 name
    expect(textInputs[3]).toHaveValue('901') // Candidate 1 votes
    expect(textInputs[4]).toHaveValue('1') // Number of winners
    expect(textInputs[5]).toHaveValue('2,001') // Total ballots cast
    await screen.findByText('1,004 ballots')
  })
})

test('Audit plan card interactions', async () => {
  const expectedCalls = [
    apiMocks.publicComputeSampleSizes1,
    apiMocks.publicComputeSampleSizes2,
  ]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const elements = await checkThatElectionResultsCardIsInInitialState()
    const { candidate1VotesInput, candidate2NameInput } = elements
    let {
      candidate1NameInput,
      candidate2VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = elements

    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.type(candidate1VotesInput, '1000')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    userEvent.type(candidate2VotesInput, '900')
    userEvent.type(totalBallotsCastInput, '2000')
    userEvent.click(planAuditButton)
    await screen.findByText('1,001 ballots')
    expect(mockScrollIntoView).toHaveBeenCalledTimes(1)

    // Toggle audit methods ----------

    let ballotPollingRadioInput = screen.getByRole('radio', {
      name: 'Ballot Polling',
    })
    let ballotComparisonRadioInput = screen.getByRole('radio', {
      name: 'Ballot Comparison',
    })
    let batchComparisonRadioInput = screen.getByRole('radio', {
      name: 'Batch Comparison',
    })
    expect(ballotPollingRadioInput).toBeChecked()
    expect(ballotComparisonRadioInput).not.toBeChecked()
    expect(batchComparisonRadioInput).not.toBeChecked()

    userEvent.click(ballotComparisonRadioInput)
    expect(ballotPollingRadioInput).not.toBeChecked()
    expect(ballotComparisonRadioInput).toBeChecked()
    expect(batchComparisonRadioInput).not.toBeChecked()
    await screen.findByText('1,000 ballots')

    userEvent.click(batchComparisonRadioInput)
    expect(ballotPollingRadioInput).not.toBeChecked()
    expect(ballotComparisonRadioInput).not.toBeChecked()
    expect(batchComparisonRadioInput).toBeChecked()
    await screen.findByText('1,002 batches')

    userEvent.click(ballotPollingRadioInput)
    expect(ballotPollingRadioInput).toBeChecked()
    expect(ballotComparisonRadioInput).not.toBeChecked()
    expect(batchComparisonRadioInput).not.toBeChecked()
    await screen.findByText('1,001 ballots')

    // Change risk limit percentage ----------

    let sliderHandle = document.querySelector(
      '.bp3-slider-handle'
    )! as HTMLElement
    expect(sliderHandle).toBeInTheDocument()
    expect(sliderHandle).toHaveTextContent('5%')
    moveSlider(sliderHandle, 'right', 1)
    expect(sliderHandle).toHaveTextContent('6%')
    await screen.findByText('1,007 ballots')
    moveSlider(sliderHandle, 'left', 6)
    expect(sliderHandle).toHaveTextContent('0%')
    await screen.findByText('Full hand tally')
    moveSlider(sliderHandle, 'right', 5)
    expect(sliderHandle).toHaveTextContent('5%')
    await screen.findByText('1,001 ballots')

    // Edit election results ----------

    const editButton = screen.getByRole('button', { name: 'Edit' })
    userEvent.click(editButton)
    planAuditButton = await screen.findByRole('button', {
      name: 'Plan Audit',
    })

    // Verify that audit plan card is disabled during election results editing
    ballotPollingRadioInput = screen.getByRole('radio', {
      name: 'Ballot Polling',
    })
    ballotComparisonRadioInput = screen.getByRole('radio', {
      name: 'Ballot Comparison',
    })
    batchComparisonRadioInput = screen.getByRole('radio', {
      name: 'Batch Comparison',
    })
    expect(ballotPollingRadioInput).toBeDisabled()
    expect(ballotComparisonRadioInput).toBeDisabled()
    expect(batchComparisonRadioInput).toBeDisabled()
    sliderHandle = document.querySelector('.bp3-slider-handle')! as HTMLElement
    expect(sliderHandle.classList.contains('.bp3-disabled'))
    screen.getByText('—')

    candidate1NameInput = screen.getByRole('textbox', {
      name: 'Candidate 1 Name',
    })
    candidate2VotesInput = screen.getByRole('spinbutton', {
      name: 'Candidate 2 Votes',
    })
    totalBallotsCastInput = screen.getByRole('spinbutton', {
      name: 'Total Ballots Cast',
    })
    userEvent.type(candidate1NameInput, 'potamus')
    userEvent.clear(candidate2VotesInput)
    userEvent.type(candidate2VotesInput, '901')
    userEvent.clear(totalBallotsCastInput)
    userEvent.type(totalBallotsCastInput, '2001')
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )

    // Verify that audit plan card is re-enabled after election results editing
    ballotPollingRadioInput = screen.getByRole('radio', {
      name: 'Ballot Polling',
    })
    ballotComparisonRadioInput = screen.getByRole('radio', {
      name: 'Ballot Comparison',
    })
    batchComparisonRadioInput = screen.getByRole('radio', {
      name: 'Batch Comparison',
    })
    expect(ballotPollingRadioInput).toBeEnabled()
    expect(ballotComparisonRadioInput).toBeEnabled()
    expect(batchComparisonRadioInput).toBeEnabled()
    sliderHandle = document.querySelector('.bp3-slider-handle')! as HTMLElement
    expect(!sliderHandle.classList.contains('.bp3-disabled'))
    await screen.findByText('1,004 ballots')
  })
})

test('Sample size computation error handling', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizesError]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const {
      candidate1NameInput,
      candidate1VotesInput,
      candidate2NameInput,
      candidate2VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    userEvent.clear(candidate1NameInput)
    userEvent.type(candidate1NameInput, 'Helga Hippo')
    userEvent.type(candidate1VotesInput, '1000')
    userEvent.clear(candidate2NameInput)
    userEvent.type(candidate2NameInput, 'Bobby Bear')
    userEvent.type(candidate2VotesInput, '900')
    userEvent.type(totalBallotsCastInput, '2000')
    userEvent.click(planAuditButton)
    await screen.findByText('Error computing sample size')
  })
})
