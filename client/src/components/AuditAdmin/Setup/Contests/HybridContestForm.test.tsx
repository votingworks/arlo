import React from 'react'
import { screen, waitFor, render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import {
  withMockFetch,
  regexpEscape,
  createQueryClient,
} from '../../../testUtilities'
import Contests, { IContestsProps } from './Contests'
import { aaApiCalls } from '../../../_mocks'
import { IContest } from '../../../../types'

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

const renderContests = (props: Partial<IContestsProps> = {}) => {
  const goToNextStage = jest.fn()
  const goToPrevStage = jest.fn()
  return {
    goToNextStage,
    goToPrevStage,
    ...render(
      <QueryClientProvider client={createQueryClient()}>
        <Contests
          electionId="1"
          auditType="HYBRID"
          isTargeted
          goToNextStage={goToNextStage}
          goToPrevStage={goToPrevStage}
          {...props}
        />
      </QueryClientProvider>
    ),
  }
}

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
  getContests: (contests: Omit<IContest, 'totalBallotsCast'>[]) => ({
    url: '/api/election/1/contest',
    response: { contests },
  }),
  putContests: (contests: Omit<IContest, 'totalBallotsCast'>[]) => ({
    url: '/api/election/1/contest',
    options: {
      method: 'PUT',
      body: JSON.stringify(contests),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
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
      const { container } = renderContests()
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
      apiCalls.putContests(contests),
      apiCalls.getContests(contests),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.selectOptions(
        screen.getByLabelText(/Contest Name/),
        'Contest 1.\'"'
      )
      hybridContestsInputMocks.inputs.forEach(inputData => {
        const input = screen.getByLabelText(
          new RegExp(regexpEscape(inputData.key)),
          { selector: 'input' }
        )
        userEvent.type(input, inputData.value)
      })
      expect(
        screen.queryByText('Total Ballot Cards Cast')
      ).not.toBeInTheDocument()
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(goToNextStage).toHaveBeenCalled())
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
      apiCalls.putContests(contests.slice(1)),
      apiCalls.getContests(contests.slice(1)),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.click(screen.getByRole('button', { name: 'Remove Contest 1' }))
      await waitFor(() =>
        expect(
          screen.queryByRole('heading', { name: 'Contest 1' })
        ).not.toBeInTheDocument()
      )
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(goToNextStage).toHaveBeenCalled())
    })
  })

  it('hides jurisdiction selection for hybrid', async () => {
    const contests = [newContest()]
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
      apiCalls.putContests(contests),
      apiCalls.getContests(contests),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()
      await screen.findByRole('heading', { name: 'Target Contests' })
      userEvent.selectOptions(
        screen.getByLabelText(/Contest Name/),
        'Contest 1.\'"'
      )
      hybridContestsInputMocks.inputs.forEach(inputData => {
        const input = screen.getByLabelText(
          new RegExp(regexpEscape(inputData.key)),
          {
            selector: 'input',
          }
        )
        userEvent.type(input, inputData.value)
      })
      expect(screen.queryByText('Contest Universe')).not.toBeInTheDocument()
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(goToNextStage).toHaveBeenCalled())
    })
  })

  it('it should not skip to next stage when targeted contest form is clean and not touched', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests()
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
      const { goToNextStage } = renderContests({ isTargeted: false })
      await screen.findByRole('heading', { name: 'Opportunistic Contests' })
      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))
      await waitFor(() => expect(goToNextStage).toHaveBeenCalled())
    })
  })

  it('it should not skip to next stage when opportunistic contest form is touched', async () => {
    const expectedCalls = [
      apiCalls.getContests([]),
      aaApiCalls.getJurisdictions,
      apiCalls.getStandardizedContests,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests({ isTargeted: false })

      await screen.findByRole('heading', { name: 'Opportunistic Contests' })

      userEvent.type(
        screen.getByLabelText('Votes Allowed', { selector: 'input' }),
        '2'
      )

      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))

      await waitFor(() => {
        expect(screen.queryAllByText('Required').length).toBe(5)
      })
    })
  })
})
