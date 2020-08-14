import React from 'react'
import { waitFor, screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { renderWithRouter, withMockFetch } from '../testUtilities'
import DataEntry from './index'
import { dummyBoards, dummyBallots, doneDummyBallots } from './_mocks'
import { contestMocks } from '../MultiJurisdictionAudit/useSetupMenuItems/_mocks'

window.scrollTo = jest.fn()

const renderDataEntry = () =>
  renderWithRouter(
    <Route
      path="/election/:electionId/audit-board/:auditBoardId"
      component={DataEntry}
    />,
    {
      route: '/election/1/audit-board/audit-board-1',
    }
  )

const renderBallot = () =>
  renderWithRouter(
    <Route
      path="/election/:electionId/audit-board/:auditBoardId/batch/:batchId/ballot/:ballotPosition"
      component={DataEntry}
    />,
    {
      route:
        '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/2112',
    }
  )

const apiCalls = {
  getAuditBoard: {
    url: '/api/me',
    response: { type: 'AUDIT_BOARD', ...dummyBoards()[0] },
  },
  putAuditBoardMembers: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/members',
    options: {
      method: 'PUT',
      body: JSON.stringify([
        { name: 'Name 1', affiliation: null },
        { name: 'Name 2', affiliation: null },
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
    it('submits and goes to ballot table', async () => {
      const expectedCalls = [
        {
          ...apiCalls.getAuditBoard,
          response: { type: 'AUDIT_BOARD', ...dummyBoards()[1] }, // No members set
        },
        apiCalls.putAuditBoardMembers,
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Audit Board #2: Member Sign-in')
        const nameInputs = screen.getAllByLabelText('Full Name')
        expect(nameInputs).toHaveLength(2)

        await userEvent.type(nameInputs[0], `Name 1`)
        await userEvent.type(nameInputs[1], `Name 2`)
        userEvent.click(screen.getByRole('button', { name: 'Next' }))

        await screen.findByText('Audit Board #1: Ballot Cards to Audit')
        expect(container).toMatchSnapshot()
      })
    })
  })

  describe('ballot interaction', () => {
    it('renders board table with no ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        {
          ...apiCalls.getBallotsInitial,
          response: { ballots: [] },
        },
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Audit Board #1: Ballot Cards to Audit')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with ballots', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()

        await screen.findByText('Audit Board #1: Ballot Cards to Audit')
        expect(
          screen.getByRole('button', { name: 'Start Auditing' })
        ).toBeEnabled()
        expect(
          screen.getByRole('button', {
            name: 'Auditing Complete - Submit Results',
          })
        ).toBeDisabled()
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with large container size', async () => {
      jest
        .spyOn(window.document, 'getElementsByClassName')
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .mockReturnValue([{ clientWidth: 2000 }] as any)
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderDataEntry()
        await screen.findByText('Audit Board #1: Ballot Cards to Audit')
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ballot route', async () => {
      const expectedCalls = [
        apiCalls.getAuditBoard,
        apiCalls.getContests,
        apiCalls.getBallotsInitial,
      ]
      await withMockFetch(expectedCalls, async () => {
        const { container } = renderBallot()
        await screen.findByText('Enter Ballot Information')
        expect(container).toMatchSnapshot()
      })
    })

    it('advances ballot forward and backward', async () => {
      const expectedCalls = [
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
            name: 'Ballot 2112 not found - move to next ballot',
          })
        )
        await waitFor(() => {
          expect(pushSpy).toBeCalledTimes(1)
        })

        userEvent.click(screen.getByText('Back'))
        await waitFor(() => {
          expect(pushSpy).toBeCalledTimes(2)
        })

        expect(pushSpy.mock.calls[0][0]).toBe(
          '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
        )
        expect(pushSpy.mock.calls[1][0]).toBe(
          '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/313'
        )
      })
    })

    it('submits ballot', async () => {
      const expectedCalls = [
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
        userEvent.click(await screen.findByRole('button', { name: 'Review' }))
        userEvent.click(
          await screen.findByRole('button', { name: 'Submit & Next Ballot' })
        )

        await waitFor(() => {
          expect(history.location.pathname).toBe(
            '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
          )
        })
      })
    })

    it('audits ballots', async () => {
      jest.setTimeout(15000)
      const expectedCalls = [
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
              interpretation: 'CANT_AGREE',
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
          name: 'Audit Board #1: Ballot Cards to Audit',
        })

        // Go to the first ballot
        userEvent.click(
          await screen.findByRole('button', { name: 'Start Auditing' })
        )
        screen.getByRole('heading', {
          name: 'Audit Board #1: Ballot Card Data Entry',
        })
        screen.getByText('Auditing ballot 2 of 27')

        // Select some choices for each contest
        screen.getByRole('heading', { name: 'Contest 1' })
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))
        screen.getByRole('heading', { name: 'Contest 2' })
        userEvent.click(
          screen.getAllByRole('checkbox', {
            name: "Audit board can't agree",
          })[1]
        )

        // Review the choices
        userEvent.click(screen.getByRole('button', { name: 'Review' }))
        expect(
          await screen.findByRole('button', { name: 'Choice One' })
        ).toBeDisabled()
        expect(
          screen.getByRole('button', { name: "Audit board can't agree" })
        ).toBeDisabled()
        expect(screen.queryByText('Choice Two')).not.toBeInTheDocument()
        expect(screen.queryByText('Choice Three')).not.toBeInTheDocument()
        expect(screen.queryByText('Choice Four')).not.toBeInTheDocument()

        // Submit the ballot
        userEvent.click(
          screen.getByRole('button', { name: 'Submit & Next Ballot' })
        )
        await screen.findByText('Auditing ballot 3 of 27')
      })
    })

    it('deselects choices', async () => {
      jest.setTimeout(15000)
      const expectedCalls = [
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
          await screen.findByRole('button', { name: 'Start Auditing' })
        )

        // Try selecting and then deselecting some choices
        // (we had a bug where this didn't work correctly)
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))
        userEvent.click(screen.getByRole('checkbox', { name: 'Choice One' }))

        userEvent.click(screen.getByRole('checkbox', { name: 'Choice Three' }))

        // Review and submit (with no choice selected for Contest 1)
        userEvent.click(screen.getByRole('button', { name: 'Review' }))
        userEvent.click(
          await screen.findByRole('button', { name: 'Submit & Next Ballot' })
        )
        await screen.findByText('Auditing ballot 3 of 27')
      })
    })
  })
})
