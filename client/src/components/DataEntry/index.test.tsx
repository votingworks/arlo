import React from 'react'
import { waitFor, fireEvent, screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { renderWithRouter, withMockApi } from '../testUtilities'
import DataEntry from './index'
import { dummyBoards, dummyBallots, doneDummyBallots } from './_mocks'
import * as utilities from '../utilities'
import { contestMocks } from '../MultiJurisdictionAudit/_mocks'

window.scrollTo = jest.fn()

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

const ballotingMock = async (endpoint: string) => {
  switch (endpoint) {
    case '/me':
      return {
        type: 'AUDIT_BOARD',
        ...dummyBoards()[0],
      }
    case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/contest':
      return { contests: contestMocks.oneTargeted }
    case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots':
      return dummyBallots
    case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots/ballot-id-1':
      return { status: 'ok' }
    default:
      return null
  }
}

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
    endpoint: '/me',
    response: { type: 'AUDIT_BOARD', ...dummyBoards()[0] },
  },
  getContests: {
    endpoint:
      '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/contest',
    response: { contests: contestMocks.oneTargeted },
  },
  getBallotsInitial: {
    endpoint:
      '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots',
    response: dummyBallots,
  },
  putAuditBallot: (ballotId: string, body: object) => ({
    endpoint: `/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots/${ballotId}`,
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
    endpoint:
      '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots',
    response: {
      ballots: [
        dummyBallots.ballots[0],
        doneDummyBallots.ballots[1],
        ...dummyBallots.ballots.slice(2),
      ],
    },
  },
}

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('DataEntry', () => {
  beforeEach(() => {
    apiMock.mockImplementation(ballotingMock)
  })

  describe('member form', () => {
    it('renders if no audit board members set', async () => {
      apiMock.mockImplementation(async endpoint => {
        switch (endpoint) {
          case '/me':
            return dummyBoards()[1] // No members set
          default:
            return ballotingMock(endpoint)
        }
      })
      const { container } = renderDataEntry()

      await screen.findByText('Audit Board #2: Member Sign-in')
      expect(apiMock).toBeCalledTimes(1)
      expect(container).toMatchSnapshot()
    })

    it('submits and goes to ballot table', async () => {
      let posted = false
      apiMock.mockImplementation(async endpoint => {
        switch (endpoint) {
          case '/me':
            return posted ? dummyBoards()[0] : dummyBoards()[1]
          case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/members':
            posted = true
            return { status: 'ok' }
          default:
            return ballotingMock(endpoint)
        }
      })
      const { container } = renderDataEntry()

      const nameInputs = await screen.findAllByLabelText('Full Name')
      expect(nameInputs).toHaveLength(2)
      expect(apiMock).toBeCalledTimes(1)

      nameInputs.forEach((nameInput, i) =>
        fireEvent.change(nameInput, { target: { value: `Name ${i}` } })
      )
      fireEvent.click(screen.getByText('Next'), { bubbles: true })

      await screen.findByText('Audit Board #1: Ballot Cards to Audit')
      expect(apiMock).toBeCalledTimes(1 + 4)
      expect(container).toMatchSnapshot()
    })
  })

  describe('ballot interaction', () => {
    it('renders board table with no ballots', async () => {
      apiMock.mockImplementation(async (endpoint: string) => {
        switch (endpoint) {
          case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots':
            return { ballots: [] }
          default:
            return ballotingMock(endpoint)
        }
      })
      const { container } = renderDataEntry()

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with ballots', async () => {
      const { container } = renderDataEntry()
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        screen.getByText('Audit Board #1: Ballot Cards to Audit')
        expect(screen.getByText('Start Auditing')).toBeEnabled()
        expect(
          screen.getByText('Auditing Complete - Submit Results')
        ).toBeDisabled()
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with large container size', async () => {
      jest
        .spyOn(window.document, 'getElementsByClassName')
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .mockReturnValue([{ clientWidth: 2000 }] as any)
      const { container } = renderDataEntry()
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ballot route', async () => {
      const { container } = renderBallot()
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        screen.getByText('Enter Ballot Information')
        expect(container).toMatchSnapshot()
      })
    })

    it('advances ballot forward and backward', async () => {
      const { history } = renderBallot()
      const pushSpy = jest.spyOn(history, 'push').mockImplementation()

      fireEvent.click(
        await screen.findByText('Ballot 2112 not found - move to next ballot'),
        {
          bubbles: true,
        }
      )
      await waitFor(() => {
        expect(pushSpy).toBeCalledTimes(1)
      })

      fireEvent.click(screen.getByText('Back'), { bubbles: true })
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

    it('submits ballot', async () => {
      const { history } = renderBallot()

      fireEvent.click(await screen.findByTestId('choice-id-1'), {
        bubbles: true,
      })
      await waitFor(() =>
        fireEvent.click(screen.getByTestId('enabled-review'), { bubbles: true })
      )
      await waitFor(() => {
        fireEvent.click(screen.getByText('Submit & Next Ballot'), {
          bubbles: true,
        })
      })

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(5)
        expect(history.location.pathname).toBe(
          '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
        )
      })
    })

    it('audits ballots', async () => {
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
      await withMockApi(expectedCalls, async () => {
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
      await withMockApi(expectedCalls, async () => {
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
