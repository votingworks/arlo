import React from 'react'
import { Route } from 'react-router-dom'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  renderWithRouter,
  withMockFetch,
  regexpEscape,
} from '../../../testUtilities'
import relativeStages from '../_mocks'
import Contests from '.'
import { aaApiCalls } from '../../_mocks'
import { IContest, INewContest } from '../../useContestsBallotComparison'

const hybridContestsInputMocks = {
  inputs: [
    { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
    { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
    { key: 'Votes for Candidate/Choice 1', value: '10' },
    { key: 'Votes for Candidate/Choice 2', value: '20' },
    { key: 'Total Ballots for Contest', value: '30' },
  ],
  errorInputs: [
    {
      key: 'Total Ballots for Contest',
      value: '',
      error:
        'Must be greater than or equal to the sum of votes for each candidate/choice',
    },
    {
      key: 'Total Ballots for Contest',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Total Ballots for Contest',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Total Ballots for Contest',
      value: '0.5',
      error: 'Must be an integer',
    },
    { key: 'Name of Candidate/Choice 1', value: '', error: 'Required' },
    { key: 'Name of Candidate/Choice 2', value: '', error: 'Required' },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '',
      error: 'Required',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '',
      error: 'Required',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '0.5',
      error: 'Must be an integer',
    },
  ],
}

const { nextStage, prevStage } = relativeStages('target-contests')

const render = (isTargeted: boolean = true) =>
  renderWithRouter(
    <Route path="/election/:electionId/setup">
      <Contests
        auditType="HYBRID"
        locked={false}
        isTargeted={isTargeted}
        nextStage={nextStage}
        prevStage={prevStage}
      />
    </Route>,
    { route: '/election/1/setup' }
  )

const apiCalls = {
  getStandardizedContests: {
    url: '/api/election/1/standardized-contests',
    response: [
      {
        name: 'Contest 1.\'"', // Make sure dots and quotes in the name work
        jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      },
      {
        name: 'Contest 2',
        jurisdictionIds: ['jurisdiction-id-1'],
      },
      { name: 'Contest 3', jurisdictionIds: ['jurisdiction-id-2'] },
    ],
  },
  getContests: (contests: IContest[]) => ({
    url: '/api/election/1/contest',
    response: { contests },
  }),
  putContests: (contests: INewContest[]) => ({
    url: '/api/election/1/contest',
    options: {
      method: 'PUT',
      body: JSON.stringify(contests),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
  submitContests: (mockContest: object) => ({
    url: '/api/election/1/contest',
    options: {
      method: 'PUT',
      body: JSON.stringify(mockContest),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
}

jest.mock('uuidv4', () => {
  let id = 0
  return () => {
    id += 1
    return id.toString()
  }
})

function typeInto(input: Element, value: string): void {
  // TODO: do more, like `focusIn`, `focusOut`, `input`, etc?
  fireEvent.focus(input)
  fireEvent.change(input, { target: { value } })
  fireEvent.blur(input)
}

describe('Audit Setup > Contests (Hybrid)', () => {
  const newContest = [
    {
      id: '1',
      name: 'Contest 1.\'"',
      isTargeted: true,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'], // adding these makes the test fail, hence the functionality needs to be changed?
      choices: [
        {
          id: '2',
          name: 'Choice One',
          numVotes: 10,
        },
        {
          id: '3',
          name: 'Choice Two',
          numVotes: 20,
        },
      ],
    },
  ]

  it('Audit Setup > Contests', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = render()
      await screen.findByRole('heading', { name: 'Target Contests' })
      expect(container).toMatchSnapshot()
    })
  })

  it('is able to submit form successfully', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
      apiCalls.submitContests(newContest),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { getByLabelText } = render()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.selectOptions(
        screen.getByLabelText(/Contest Name/),
        'Contest 1.\'"'
      )
      hybridContestsInputMocks.inputs.forEach(inputData => {
        const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
          selector: 'input',
        }) as HTMLInputElement
        typeInto(input, inputData.value)
        expect(input.value).toBe(inputData.value)
      })
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('displays no error when the total votes are greater than the ballot count, but less than the total allowed votes for a contest', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { findByLabelText, getByLabelText, queryByTestId } = render()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.selectOptions(
        screen.getByLabelText(/Contest Name/),
        'Contest 1.\'"'
      )
      typeInto(
        await findByLabelText('Votes Allowed', {
          selector: 'input',
        }),
        '2'
      )

      typeInto(
        getByLabelText('Votes for Candidate/Choice 1', {
          selector: 'input',
        }),
        '20'
      )

      typeInto(
        getByLabelText('Votes for Candidate/Choice 2', {
          selector: 'input',
        }),
        '40'
      )

      const totalBallotInput = getByLabelText('Total Ballots for Contest', {
        selector: 'input',
      }) as HTMLInputElement
      typeInto(totalBallotInput, '30')

      await waitFor(() => {
        // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
        // 20 actual votes in choice #1 + 40 actual votes in choice #2 = 60 actual votes
        expect(queryByTestId(`${totalBallotInput.name}-error`)).toBeNull()
      })
    })
  })
})
