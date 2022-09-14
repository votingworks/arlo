import React from 'react'
import userEvent from '@testing-library/user-event'
import { screen, waitFor, within } from '@testing-library/react'
import { ToastContainer } from 'react-toastify'

import AuditPlanner from './AuditPlanner'
import { renderWithRouter } from '../../testUtilities'

function renderAuditPlanner() {
  renderWithRouter(
    <>
      <AuditPlanner />
      <ToastContainer />
    </>,
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
    expect(await screen.findAllByText(message)).toHaveLength(counts[message])
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
  const candidate1NameInput = screen.getByRole('textbox', {
    name: 'Candidate 1 Name',
  })
  const candidate1VotesInput = screen.getByRole('spinbutton', {
    name: 'Candidate 1 Votes',
  })
  expect(candidate0NameInput).toHaveValue('')
  expect(candidate0VotesInput).toHaveValue(0)
  expect(candidate1NameInput).toHaveValue('')
  expect(candidate1VotesInput).toHaveValue(0)
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
  expect(totalBallotsCastInput).toHaveValue(0)

  const clearButton = screen.getByRole('button', { name: 'Clear' })
  const planAuditButton = screen.getByRole('button', { name: 'Plan Audit' })

  return {
    candidate0NameInput,
    candidate0VotesInput,
    candidate1NameInput,
    candidate1VotesInput,
    addCandidateButton,
    numberOfWinnersInput,
    totalBallotsCastInput,
    clearButton,
    planAuditButton,
  }
}

test('Entering election results - validation and submit', async () => {
  renderAuditPlanner()
  await screen.findByRole('heading', { name: 'Audit Planner' })
  const {
    candidate0NameInput,
    candidate0VotesInput,
    candidate1NameInput,
    numberOfWinnersInput,
    totalBallotsCastInput,
    planAuditButton,
  } = await checkThatElectionResultsCardIsInInitialState()

  // Failed submissions
  userEvent.click(planAuditButton)
  await areExpectedErrorMessagesDisplayed({
    displayed: [
      'Required',
      'Required',
      'At least 1 candidate must have greater than 0 votes',
      'At least 1 candidate must have greater than 0 votes',
    ],
  })
  userEvent.type(candidate0NameInput, 'Helga Hippo')
  userEvent.type(candidate1NameInput, 'Bobby Bear')
  await areExpectedErrorMessagesDisplayed({
    displayed: [
      'At least 1 candidate must have greater than 0 votes',
      'At least 1 candidate must have greater than 0 votes',
    ],
    notDisplayed: ['Required'],
  })
  userEvent.type(candidate0VotesInput, '{backspace}')
  await areExpectedErrorMessagesDisplayed({
    displayed: [
      'Required',
      'At least 1 candidate must have greater than 0 votes',
    ],
  })
  userEvent.type(candidate0VotesInput, '-1')
  await areExpectedErrorMessagesDisplayed({
    displayed: [
      'Cannot be less than 0',
      'At least 1 candidate must have greater than 0 votes',
    ],
    notDisplayed: ['Required'],
  })
  userEvent.type(candidate0VotesInput, '{backspace}10')
  await areExpectedErrorMessagesDisplayed({
    displayed: [],
    notDisplayed: [
      'Cannot be less than 0',
      'At least 1 candidate must have greater than 0 votes',
    ],
  })
  userEvent.click(planAuditButton)
  await areExpectedErrorMessagesDisplayed({
    displayed: ['Cannot be less than sum of candidate votes'],
  })
  userEvent.type(totalBallotsCastInput, '{backspace}')
  await areExpectedErrorMessagesDisplayed({
    displayed: ['Required'],
    notDisplayed: ['Cannot be less than sum of candidate votes'],
  })
  userEvent.type(totalBallotsCastInput, '15')
  await areExpectedErrorMessagesDisplayed({
    displayed: [],
    notDisplayed: ['Required'],
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
  userEvent.type(numberOfWinnersInput, '{backspace}1')
  await areExpectedErrorMessagesDisplayed({
    displayed: [],
    notDisplayed: ['Cannot be greater than number of candidates'],
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
  const numericInputs = within(electionResultsCard).queryAllByRole('spinbutton')
  expect(numericInputs).toHaveLength(4)
  expect(numericInputs[0]).toHaveValue(10) // Candidate 0 votes
  expect(numericInputs[1]).toHaveValue(0) // Candidate 1 votes
  expect(numericInputs[2]).toHaveValue(1) // Number of winners
  expect(numericInputs[3]).toHaveValue(15) // Total ballots cast
  for (const numericInput of numericInputs) {
    expect(numericInput).toHaveAttribute('readonly')
  }
  screen.getByRole('button', { name: 'Clear' })
  screen.getByRole('button', { name: 'Edit' })
})

test('Entering election results - adding and removing candidates', async () => {
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
  expect(screen.getByRole('textbox', { name: 'Candidate 2 Name' })).toHaveValue(
    ''
  )
  expect(
    screen.getByRole('spinbutton', { name: 'Candidate 2 Votes' })
  ).toHaveValue(0)
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

test('Entering election results - clearing', async () => {
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
  userEvent.click(within(confirmDialog).getByRole('button', { name: 'Clear' }))
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

  userEvent.type(candidate0NameInput, 'Helga Hippo')
  userEvent.type(candidate0VotesInput, '10')
  userEvent.type(candidate1NameInput, 'Bobby Bear')
  userEvent.type(candidate1VotesInput, '5')
  userEvent.type(totalBallotsCastInput, '20')
  userEvent.click(planAuditButton)

  // Clearing after submission
  userEvent.click(clearButton)
  confirmDialog = (
    await screen.findByRole('heading', { name: 'Confirm' })
  ).closest('.bp3-dialog')! as HTMLElement
  within(confirmDialog).getByText(
    'Are you sure you want to clear and start over?'
  )
  userEvent.click(within(confirmDialog).getByRole('button', { name: 'Clear' }))
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

test('Entering election results - editing', async () => {
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

  userEvent.click(screen.getByRole('button', { name: 'Edit' }))
  planAuditButton = await screen.findByRole('button', { name: 'Plan Audit' })
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
})
