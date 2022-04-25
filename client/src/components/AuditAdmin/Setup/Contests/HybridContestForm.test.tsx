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
import Contests from './Contests'
import { IContestNumbered } from '../../../useContests'
import { aaApiCalls } from '../../../_mocks'

const hybridContestsInputMocks = {
  inputs: [
    { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
    { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
    { key: 'Votes for Candidate/Choice 1', value: '10' },
    { key: 'Votes for Candidate/Choice 2', value: '20' },
  ],
  errorInputs: [
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
  getContests: (contests: Omit<IContestNumbered, 'totalBallotsCast'>[]) => ({
    url: '/api/election/1/contest',
    response: { contests },
  }),
  putContests: (contests: Omit<IContestNumbered, 'totalBallotsCast'>[]) => ({
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

function typeInto(input: Element, value: string): void {
  // TODO: do more, like `focusIn`, `focusOut`, `input`, etc?
  fireEvent.focus(input)
  fireEvent.change(input, { target: { value } })
  fireEvent.blur(input)
}

const mockUuid = jest.fn()
jest.mock('uuidv4', () => () => mockUuid())

describe('Audit Setup > Contests (Hybrid)', () => {
  let getID: () => string
  beforeEach(() => {
    // uuidMock and getID should be in sync so we can generate test data that
    // matches the UUIDs assigned when making new contests
    mockUuid.mockImplementation(
      (() => {
        let id = 0
        return () => {
          id += 1
          return id.toString()
        }
      })()
    )
    getID = (() => {
      let id = 0
      return () => {
        id += 1
        return id.toString()
      }
    })()
  })

  const newContest = () => ({
    id: getID(),
    name: 'Contest 1.\'"',
    isTargeted: true,
    numWinners: 1,
    votesAllowed: 1,
    jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
    choices: [
      {
        id: getID(),
        name: 'Choice One',
        numVotes: 10,
      },
      {
        id: getID(),
        name: 'Choice Two',
        numVotes: 20,
      },
    ],
  })

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
    const contests = [newContest()]
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
      apiCalls.submitContests(contests),
      apiCalls.getContests(contests),
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
      expect(
        screen.queryByText('Total Ballot Cards Cast')
      ).not.toBeInTheDocument()
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('removes a contest', async () => {
    const contests = [
      newContest(),
      {
        ...newContest(),
        name: 'Contest 2',
        jurisdictionIds: ['jurisdiction-id-1'],
      },
      { ...newContest(), name: 'Contest 3', isTargeted: false },
    ]
    const expectedCalls = [
      apiCalls.getContests(contests),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
      apiCalls.submitContests(contests.slice(1)),
      apiCalls.getContests(contests.slice(1)),
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.click(screen.getByRole('button', { name: 'Remove Contest 1' }))
      await waitFor(() =>
        expect(
          screen.queryByRole('heading', { name: 'Contest 1' })
        ).not.toBeInTheDocument()
      )
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('hides jurisdiction selection for hybrid', async () => {
    const contests = [newContest()]
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
      apiCalls.submitContests(contests),
      apiCalls.getContests(contests),
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
      expect(screen.queryByText('Contest Universe')).not.toBeInTheDocument()
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('it should not skip to next stage when targeted contest form is clean and not touched', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      render()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => {
        expect(screen.queryAllByText('Required').length).toBe(5)
      })
    })
  })

  it('it should skip to next stage when opportunistic contest form is clean and not touched', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      render(false)

      await screen.findByRole('heading', { name: 'Opportunistic Contests' })
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(nextStage.activate).toHaveBeenCalled())
    })
  })

  it('it should not skip to next stage when opportunistic contest form is touched', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { getByLabelText } = render(false)

      await screen.findByRole('heading', { name: 'Opportunistic Contests' })

      typeInto(
        getByLabelText('Votes Allowed', {
          selector: 'input',
        }),
        '2'
      )

      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))

      await waitFor(() => {
        expect(screen.queryAllByText('Required').length).toBe(5)
      })
    })
  })
})
