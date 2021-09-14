import React from 'react'
import { waitFor, screen, within } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { renderWithRouter, withMockFetch } from '../testUtilities'
import DataEntry from './index'
import {
  dummyBoards,
  dummyBallots,
  doneDummyBallots,
  dummyBallotsNotAudited,
} from './_mocks'
import { contestMocks } from '../MultiJurisdictionAudit/useSetupMenuItems/_mocks'
import AuthDataProvider, { useAuthDataContext } from '../UserContext'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  auditBoardId: 'audit-board-1',
})

afterEach(() => {
  paramsMock.mockReturnValue({
    electionId: '1',
    auditBoardId: 'audit-board-1',
  })
})

window.scrollTo = jest.fn()

const DataEntryWithAuth: React.FC = () => {
  const auth = useAuthDataContext()
  return auth ? <DataEntry /> : null
}

const renderDataEntry = () =>
  renderWithRouter(
    <AuthDataProvider>
      <DataEntryWithAuth />
    </AuthDataProvider>,
    {
      route: '/election/1/audit-board/audit-board-1',
    }
  )

const renderBallot = () =>
  renderWithRouter(
    <AuthDataProvider>
      <DataEntryWithAuth />
    </AuthDataProvider>,
    {
      route:
        '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/2112',
    }
  )

const apiCalls = {
  getAuditBoard: {
    url: '/api/me',
    response: {
      user: { ...dummyBoards()[0] },
      supportUser: null,
    },
  },
  getAuditBoardInitial: {
    url: '/api/me',
    response: {
      user: { ...dummyBoards()[1] },
      supportUser: null,
    },
  },
  putAuditBoardMembers: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/members',
    options: {
      method: 'PUT',
      body: JSON.stringify([
        { name: 'John Doe', affiliation: null },
        { name: 'Jane Doe', affiliation: null },
      ]),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  },
  getContests: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/contest',
    response: { contests: contestMocks.oneTargeted },
  },
  getBallotsInitial: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots',
    response: dummyBallots,
  },
  getBallotsNotAudited: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots',
    response: dummyBallotsNotAudited,
  },
  putAuditBallot: (ballotId: string, body: object) => ({
    url: `/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots/${ballotId}`,
    options: {
      method: 'PUT',
      body: JSON.stringify(body),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  }),
  getBallotsOneAudited: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots',
    response: {
      ballots: [
        dummyBallots.ballots[0],
        doneDummyBallots.ballots[1],
        ...dummyBallots.ballots.slice(2),
      ],
    },
  },
}

describe('DataEntry', () => {
  describe('member form', () => {
    it('submits, goes to ballot table, and header shows member names', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoardInitial,
        apiCalls.getAuditBoardInitial,
        apiCalls.putAuditBoardMembers,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByRole('link', {
          name: 'Arlo, by VotingWorks',
        })

        // Audit board name
        expect(screen.getAllByText(/Audit Board #1/).length).toBe(3)

        // should show log out link
        const logOutButton = screen.getByRole('link', { name: 'Log out' })
        expect(logOutButton).toHaveAttribute('href', '/auth/logout')

        await screen.findByText('Audit Board #1: Member Sign-in')
        const nameInputs = screen.getAllByLabelText('Full Name')
        expect(nameInputs).toHaveLength(2)

        userEvent.type(nameInputs[0], `John Doe`)
        userEvent.type(nameInputs[1], `Jane Doe`)
        userEvent.click(screen.getByRole('button', { name: 'Next' }))

        await screen.findByText('Ballots for Audit Board #1')
        await screen.findByText(/John Doe, Jane Doe/) // member names shows up in header now

        expect(container).toMatchSnapshot()
      })
    })
  })

  describe('ballot interaction', () => {
    it('renders board table with no ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        {
          ...apiCalls.getBallotsInitial,
          response: { ballots: [] },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Ballots for Audit Board #1')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with no audited ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsNotAudited,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Ballots for Audit Board #1')
        expect(screen.getByRole('button', { name: 'Audit First Ballot' }))
        await screen.findByText('0 of 27 ballots have been audited.')
        expect(
          screen.getByRole('button', {
            name: 'Submit Audited Ballots',
          })
        ).toBeDisabled()
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Ballots for Audit Board #1')
        expect(
          screen.getByRole('button', { name: 'Audit Next Ballot' })
        ).toBeEnabled()
        await screen.findByText('18 of 27 ballots have been audited.')
        expect(
          screen.getByRole('button', {
            name: 'Submit Audited Ballots',
          })
        ).toBeDisabled()
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ballot route', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderBallot()
        await screen.findByText('Audit Ballot Selections')
        expect(container).toMatchSnapshot()
      })
    })

    it('advances ballot forward', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
        apiCalls.putAuditBallot('ballot-id-2', {
          status: 'NOT_FOUND',
          interpretations: [],
        }),
        apiCalls.getBallotsOneAudited,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderBallot()

        const pushSpy = jest.spyOn(history, 'push').mockImplementation()

        userEvent.click(
          await screen.findByRole('button', {
            name: 'Ballot Not Found',
          })
        )
        const dialog = (await screen.findByRole('heading', {
          name: /Confirm the Ballot Selections/,
        })).closest('.bp3-dialog')! as HTMLElement
        expect(within(dialog).getAllByText('Ballot Not Found').length).toBe(1)
        userEvent.click(
          within(dialog).getByRole('button', { name: 'Confirm Selections' })
        )

        await waitFor(() => {
          expect(dialog).not.toBeInTheDocument()
          expect(pushSpy).toBeCalledTimes(1)
        })

        expect(pushSpy.mock.calls[0][0]).toBe(
          '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
        )
      })
    })

    it('submits ballot', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
        apiCalls.putAuditBallot('ballot-id-2', {
          status: 'AUDITED',
          interpretations: [
            {
              contestId: 'contest-id-1',
              interpretation: 'VOTE',
              choiceIds: ['choice-id-1'],
              comment: null,
            },
          ],
        }),
        apiCalls.getBallotsOneAudited,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { history } = renderBallot()

        userEvent.click(
          await screen.findByRole('checkbox', { name: 'Choice One' })
        )
        userEvent.click(
          await screen.findByRole('button', { name: 'Submit Selections' })
        )

        const dialog = (await screen.findByRole('heading', {
          name: /Confirm the Ballot Selections/,
        })).closest('.bp3-dialog')! as HTMLElement
        within(dialog).getByText('Contest 1')
        within(dialog).getByText('Choice One')
        userEvent.click(
          within(dialog).getByRole('button', { name: 'Confirm Selections' })
        )

        await waitFor(() => {
          expect(dialog).not.toBeInTheDocument()
          expect(history.location.pathname).toBe(
            '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
          )
        })
      })
    })

    it('audits ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
        apiCalls.putAuditBallot('ballot-id-2', {
          status: 'AUDITED',
          interpretations: [
            {
              contestId: 'contest-id-1',
              interpretation: 'VOTE',
              choiceIds: ['choice-id-1'],
              comment: null,
            },
            {
              contestId: 'contest-id-2',
              interpretation: 'CONTEST_NOT_ON_BALLOT',
              choiceIds: [],
              comment: null,
            },
          ],
        }),
        apiCalls.getBallotsOneAudited,
      ]
      await withMockFetch(expectedCalls, async () => {
        renderDataEntry()

        await screen.findByRole('heading', {
          name: 'Ballots for Audit Board #1',
        })

        // Go to the first ballot
        userEvent.click(
          await screen.findByRole('button', { name: 'Audit Next Ballot' })
        )
        screen.getByRole('heading', {
          name: 'Audit Ballot Selections',
        })

        // Select some choices for each contest
        screen.getByRole('heading', { name: 'Contest 1' })
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))
        screen.getByRole('heading', { name: 'Contest 2' })
        userEvent.click(
          screen.getAllByRole('checkbox', {
            name: 'Not on Ballot',
          })[1]
        )

        // Review the choices
        userEvent.click(
          screen.getByRole('button', { name: 'Submit Selections' })
        )

        const dialog = (await screen.findByRole('heading', {
          name: /Confirm the Ballot Selections/,
        })).closest('.bp3-dialog')! as HTMLElement
        within(dialog).getByText('Contest 1')
        within(dialog).getByText('Choice One')
        within(dialog).getByText('Not on Ballot')
        userEvent.click(
          within(dialog).getByRole('button', { name: 'Confirm Selections' })
        )

        await waitFor(() => {
          expect(dialog).not.toBeInTheDocument()
        })

        await screen.findByText('Audit Ballot Selections')
      })
    })

    it('deselects choices', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
        apiCalls.putAuditBallot('ballot-id-2', {
          status: 'AUDITED',
          interpretations: [
            {
              contestId: 'contest-id-2',
              interpretation: 'VOTE',
              choiceIds: ['choice-id-3'],
              comment: null,
            },
          ],
        }),
        apiCalls.getBallotsOneAudited,
      ]
      await withMockFetch(expectedCalls, async () => {
        renderDataEntry()

        userEvent.click(
          await screen.findByRole('button', { name: 'Audit Next Ballot' })
        )

        // Try selecting and then deselecting some choices
        // (we had a bug where this didn't work correctly)
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))

        userEvent.click(screen.getByRole('checkbox', { name: 'Choice Three' }))

        // Review and submit (with no choice selected for Contest 1)
        userEvent.click(
          screen.getByRole('button', { name: 'Submit Selections' })
        )

        const dialog = (await screen.findByRole('heading', {
          name: /Confirm the Ballot Selections/,
        })).closest('.bp3-dialog')! as HTMLElement
        within(dialog).getByText('Contest 1')
        within(dialog).getByText('Choice Three')
        userEvent.click(
          within(dialog).getByRole('button', { name: 'Confirm Selections' })
        )

        await waitFor(() => {
          expect(dialog).not.toBeInTheDocument()
        })

        await screen.findByText('Audit Ballot Selections')
      })
    })
  })
})
