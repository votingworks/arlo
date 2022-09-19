import React from 'react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { ToastContainer } from 'react-toastify'

import AuditPlanner from './AuditPlanner'
import { queryClient } from '../../../App'
import {
  renderWithRouter,
  serverError,
  withMockFetch,
} from '../../testUtilities'

function renderAuditPlanner() {
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
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
  const candidate0NameInput = screen.getByRole('textbox', {
    name: 'Candidate 0 Name',
  })
  const candidate0VotesInput = screen.getByRole('spinbutton', {
    name: 'Candidate 0 Votes',
  })
  const candidate0RemoveButton = screen.getByRole('button', {
    name: 'Remove Candidate 0',
  })
  const candidate1NameInput = screen.getByRole('textbox', {
    name: 'Candidate 1 Name',
  })
  const candidate1VotesInput = screen.getByRole('spinbutton', {
    name: 'Candidate 1 Votes',
  })
  const candidate1RemoveButton = screen.getByRole('button', {
    name: 'Remove Candidate 1',
  })
  expect(candidate0NameInput).toHaveValue('')
  expect(candidate0VotesInput).toHaveValue(null)
  expect(candidate0RemoveButton).toBeDisabled()
  expect(candidate1NameInput).toHaveValue('')
  expect(candidate1VotesInput).toHaveValue(null)
  expect(candidate1RemoveButton).toBeDisabled()
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
    candidate0NameInput,
    candidate0VotesInput,
    candidate0RemoveButton,
    candidate1NameInput,
    candidate1VotesInput,
    candidate1RemoveButton,
    addCandidateButton,
    numberOfWinnersInput,
    totalBallotsCastInput,
    clearButton,
    planAuditButton,
  }
}

async function waitForSampleSizeComputation(expectedResult: string) {
  await screen.findByText(expectedResult, undefined, {
    timeout: 2000,
  })
}

const body1 = JSON.stringify({
  electionResults: {
    candidates: [
      { name: 'Helga Hippo', votes: 10 },
      { name: 'Bobby Bear', votes: 5 },
    ],
    numWinners: 1,
    totalBallotsCast: 20,
  },
  riskLimitPercentage: 5,
})

const body2 = JSON.stringify({
  electionResults: {
    candidates: [
      { name: 'Helga Hippopotamus', votes: 10 },
      { name: 'Bobby Bear', votes: 7 },
    ],
    numWinners: 1,
    totalBallotsCast: 22,
  },
  riskLimitPercentage: 5,
})

const body3 = JSON.stringify({
  electionResults: {
    candidates: [
      { name: 'Helga Hippo', votes: 10 },
      { name: 'Bobby Bear', votes: 5 },
    ],
    numWinners: 1,
    totalBallotsCast: 20,
  },
  riskLimitPercentage: 6,
})

const apiMocks = {
  publicComputeSampleSizes1: {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body1,
      headers: { 'Content-Type': 'application/json' },
    },
    response: { ballotComparison: 2, ballotPolling: 3, batchComparison: 4 },
  },
  publicComputeSampleSizes2: {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body2,
      headers: { 'Content-Type': 'application/json' },
    },
    response: { ballotComparison: 5, ballotPolling: 6, batchComparison: 7 },
  },
  publicComputeSampleSizes3: {
    url: '/api/public/sample-sizes',
    options: {
      method: 'POST',
      body: body3,
      headers: { 'Content-Type': 'application/json' },
    },
    response: { ballotComparison: 8, ballotPolling: 9, batchComparison: 10 },
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

beforeEach(async () => {
  window.scrollTo = jest.fn()
  await queryClient.invalidateQueries()
})

test('Entering election results - validation and submit', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizes1]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const {
      candidate0NameInput,
      candidate0VotesInput,
      candidate1NameInput,
      candidate1VotesInput,
      numberOfWinnersInput,
      totalBallotsCastInput,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    // Failed submissions
    userEvent.click(planAuditButton)
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required', 'Required', 'Required', 'Required', 'Required'],
    })
    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required', 'Required', 'Required'],
    })
    userEvent.type(candidate0VotesInput, '0')
    userEvent.type(candidate1VotesInput, '0')
    userEvent.type(totalBallotsCastInput, '0')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['At least 1 candidate must have greater than 0 votes'],
      notDisplayed: ['Required'],
    })
    userEvent.type(candidate0VotesInput, '{backspace}-1')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be less than 0'],
      notDisplayed: ['At least 1 candidate must have greater than 0 votes'],
    })
    userEvent.type(candidate0VotesInput, '{backspace}{backspace}10.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Cannot be less than 0'],
    })
    userEvent.type(
      candidate0VotesInput,
      '{backspace}{backspace}{backspace}{backspace}10'
    )
    await areExpectedErrorMessagesDisplayed({
      displayed: [],
      notDisplayed: ['Can only contain numeric characters'],
    })
    userEvent.type(candidate1VotesInput, '{backspace}5')
    userEvent.click(planAuditButton)
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be less than sum of candidate votes'],
    })
    userEvent.type(totalBallotsCastInput, '{backspace}20.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Cannot be less than sum of candidate votes'],
    })
    userEvent.type(
      totalBallotsCastInput,
      '{backspace}{backspace}{backspace}{backspace}20'
    )
    await areExpectedErrorMessagesDisplayed({
      displayed: [],
      notDisplayed: ['Can only contain numeric characters'],
    })
    userEvent.type(numberOfWinnersInput, '{backspace}')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Required'],
    })
    userEvent.type(numberOfWinnersInput, '3')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Cannot be greater than number of candidates'],
      notDisplayed: ['Required'],
    })
    userEvent.type(numberOfWinnersInput, '{backspace}1.2')
    await areExpectedErrorMessagesDisplayed({
      displayed: ['Can only contain numeric characters'],
      notDisplayed: ['Cannot be greater than number of candidates'],
    })
    userEvent.type(numberOfWinnersInput, '{backspace}{backspace}{backspace}1')
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
    expect(textInputs).toHaveLength(2)
    expect(textInputs[0]).toHaveValue('Helga Hippo') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('Bobby Bear') // Candidate 1 name
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    const numericInputs = within(electionResultsCard).queryAllByRole(
      'spinbutton'
    )
    expect(numericInputs).toHaveLength(4)
    expect(numericInputs[0]).toHaveValue(10) // Candidate 0 votes
    expect(numericInputs[1]).toHaveValue(5) // Candidate 1 votes
    expect(numericInputs[2]).toHaveValue(1) // Number of winners
    expect(numericInputs[3]).toHaveValue(20) // Total ballots cast
    for (const numericInput of numericInputs) {
      expect(numericInput).toHaveAttribute('readonly')
    }
    screen.getByRole('button', { name: 'Clear' })
    screen.getByRole('button', { name: 'Edit' })
    await waitForSampleSizeComputation('3 ballots')
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
      screen.getByRole('textbox', { name: 'Candidate 2 Name' })
    ).toHaveValue('')
    expect(
      screen.getByRole('spinbutton', { name: 'Candidate 2 Votes' })
    ).toHaveValue(null)
    const candidate2RemoveButton = screen.getByRole('button', {
      name: 'Remove Candidate 2',
    })

    // Remove candidate
    userEvent.click(candidate2RemoveButton)
    await waitFor(() =>
      expect(screen.getAllByRole('row')).toHaveLength(initialNumRows)
    )
    expect(
      screen.queryByRole('textbox', { name: 'Candidate 2 Name' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('spinbutton', { name: 'Candidate 2 Votes' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('textbox', { name: 'Remove Candidate 2' })
    ).not.toBeInTheDocument()
  })
})

test('Entering election results - clearing', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizes1]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    let {
      candidate0NameInput,
      candidate0VotesInput,
      candidate1NameInput,
      candidate1VotesInput,
      addCandidateButton,
      numberOfWinnersInput,
      totalBallotsCastInput,
      clearButton,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    // Enter election results but don't submit
    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate0VotesInput, '10')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    userEvent.type(candidate1VotesInput, '5')
    userEvent.click(addCandidateButton)
    userEvent.type(numberOfWinnersInput, '2')
    userEvent.type(totalBallotsCastInput, '20')

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
      candidate0NameInput,
      candidate0VotesInput,
      candidate1NameInput,
      candidate1VotesInput,
      addCandidateButton,
      numberOfWinnersInput,
      totalBallotsCastInput,
      clearButton,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState())

    // Enter election results and submit
    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate0VotesInput, '10')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    userEvent.type(candidate1VotesInput, '5')
    userEvent.type(totalBallotsCastInput, '20')
    userEvent.click(planAuditButton)
    await waitForSampleSizeComputation('3 ballots')

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
      candidate0NameInput,
      candidate0VotesInput,
      candidate1NameInput,
      candidate1VotesInput,
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
    const { candidate0VotesInput, candidate1NameInput } = elements
    let {
      candidate0NameInput,
      candidate1VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = elements

    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate0VotesInput, '10')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    userEvent.type(candidate1VotesInput, '5')
    userEvent.type(totalBallotsCastInput, '20')
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )
    let electionResultsCard = screen.getByTestId('electionResultsCard')
    let textInputs = within(electionResultsCard).queryAllByRole('textbox')
    expect(textInputs).toHaveLength(2)
    expect(textInputs[0]).toHaveValue('Helga Hippo') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('Bobby Bear') // Candidate 1 name
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    let numericInputs = within(electionResultsCard).queryAllByRole('spinbutton')
    expect(numericInputs).toHaveLength(4)
    expect(numericInputs[0]).toHaveValue(10) // Candidate 0 votes
    expect(numericInputs[1]).toHaveValue(5) // Candidate 1 votes
    expect(numericInputs[2]).toHaveValue(1) // Number of winners
    expect(numericInputs[3]).toHaveValue(20) // Total ballots cast
    for (const numericInput of numericInputs) {
      expect(numericInput).toHaveAttribute('readonly')
    }
    await waitForSampleSizeComputation('3 ballots')

    const editButton = screen.getByRole('button', { name: 'Edit' })
    userEvent.click(editButton)
    planAuditButton = await screen.findByRole('button', {
      name: 'Plan Audit',
    })
    candidate0NameInput = screen.getByRole('textbox', {
      name: 'Candidate 0 Name',
    })
    candidate1VotesInput = screen.getByRole('spinbutton', {
      name: 'Candidate 1 Votes',
    })
    totalBallotsCastInput = screen.getByRole('spinbutton', {
      name: 'Total Ballots Cast',
    })
    userEvent.type(candidate0NameInput, 'potamus')
    userEvent.type(candidate1VotesInput, '{backspace}7')
    userEvent.type(totalBallotsCastInput, '{backspace}2')
    userEvent.click(planAuditButton)
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: 'Plan Audit' })
      ).not.toBeInTheDocument()
    )
    electionResultsCard = screen.getByTestId('electionResultsCard')
    textInputs = within(electionResultsCard).queryAllByRole('textbox')
    expect(textInputs).toHaveLength(2)
    expect(textInputs[0]).toHaveValue('Helga Hippopotamus') // Candidate 0 name
    expect(textInputs[1]).toHaveValue('Bobby Bear') // Candidate 1 name
    for (const textInput of textInputs) {
      expect(textInput).toHaveAttribute('readonly')
    }
    numericInputs = within(electionResultsCard).queryAllByRole('spinbutton')
    expect(numericInputs).toHaveLength(4)
    expect(numericInputs[0]).toHaveValue(10) // Candidate 0 votes
    expect(numericInputs[1]).toHaveValue(7) // Candidate 1 votes
    expect(numericInputs[2]).toHaveValue(1) // Number of winners
    expect(numericInputs[3]).toHaveValue(22) // Total ballots cast
    for (const numericInput of numericInputs) {
      expect(numericInput).toHaveAttribute('readonly')
    }
    await waitForSampleSizeComputation('6 ballots')
  })
})

test('Audit plan card interactions', async () => {
  const expectedCalls = [
    apiMocks.publicComputeSampleSizes1,
    apiMocks.publicComputeSampleSizes3,
    apiMocks.publicComputeSampleSizes2,
  ]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const elements = await checkThatElectionResultsCardIsInInitialState()
    const { candidate0VotesInput, candidate1NameInput } = elements
    let {
      candidate0NameInput,
      candidate1VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = elements

    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate0VotesInput, '10')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    userEvent.type(candidate1VotesInput, '5')
    userEvent.type(totalBallotsCastInput, '20')
    userEvent.click(planAuditButton)
    await waitForSampleSizeComputation('3 ballots')

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
    screen.getByText('2 ballots')

    userEvent.click(batchComparisonRadioInput)
    expect(ballotPollingRadioInput).not.toBeChecked()
    expect(ballotComparisonRadioInput).not.toBeChecked()
    expect(batchComparisonRadioInput).toBeChecked()
    screen.getByText('4 batches')

    userEvent.click(ballotPollingRadioInput)
    expect(ballotPollingRadioInput).toBeChecked()
    expect(ballotComparisonRadioInput).not.toBeChecked()
    expect(batchComparisonRadioInput).not.toBeChecked()
    screen.getByText('3 ballots')

    // Change risk limit percentage ----------

    let sliderHandle = document.querySelector(
      '.bp3-slider-handle'
    )! as HTMLElement
    expect(sliderHandle).toBeInTheDocument()
    expect(sliderHandle).toHaveTextContent('5%')
    fireEvent.keyDown(sliderHandle, { key: 'ArrowRight', keyCode: 39 })
    expect(sliderHandle).toHaveTextContent('6%')
    await waitForSampleSizeComputation('9 ballots')
    fireEvent.keyDown(sliderHandle, { key: 'ArrowLeft', keyCode: 37 })
    expect(sliderHandle).toHaveTextContent('5%')
    await waitForSampleSizeComputation('3 ballots')

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

    candidate0NameInput = screen.getByRole('textbox', {
      name: 'Candidate 0 Name',
    })
    candidate1VotesInput = screen.getByRole('spinbutton', {
      name: 'Candidate 1 Votes',
    })
    totalBallotsCastInput = screen.getByRole('spinbutton', {
      name: 'Total Ballots Cast',
    })
    userEvent.type(candidate0NameInput, 'potamus')
    userEvent.type(candidate1VotesInput, '{backspace}7')
    userEvent.type(totalBallotsCastInput, '{backspace}2')
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
    await waitForSampleSizeComputation('6 ballots')
  })
})

test('Sample size computation error handling', async () => {
  const expectedCalls = [apiMocks.publicComputeSampleSizesError]
  await withMockFetch(expectedCalls, async () => {
    renderAuditPlanner()
    await screen.findByRole('heading', { name: 'Audit Planner' })
    const {
      candidate0NameInput,
      candidate0VotesInput,
      candidate1NameInput,
      candidate1VotesInput,
      totalBallotsCastInput,
      planAuditButton,
    } = await checkThatElectionResultsCardIsInInitialState()

    userEvent.type(candidate0NameInput, 'Helga Hippo')
    userEvent.type(candidate0VotesInput, '10')
    userEvent.type(candidate1NameInput, 'Bobby Bear')
    userEvent.type(candidate1VotesInput, '5')
    userEvent.type(totalBallotsCastInput, '20')
    userEvent.click(planAuditButton)
    await waitForSampleSizeComputation('Error computing sample size')
  })
})
