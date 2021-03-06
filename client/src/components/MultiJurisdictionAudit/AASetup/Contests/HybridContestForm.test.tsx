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
import { hybridContestsInputMocks } from './_mocks'

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
      jurisdictionIds: [],
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
