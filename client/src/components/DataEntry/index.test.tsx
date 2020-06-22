import React from 'react'
import { render, waitFor, fireEvent } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import DataEntry from './index'
import { dummyBoards, dummyBallots, contest } from './_mocks'
import * as utilities from '../utilities'

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
      return { contests: [contest] }
    case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots':
      return dummyBallots
    case '/election/1/jurisdiction/jurisdiction-1/round/round-1/audit-board/audit-board-1/ballots/ballot-id-1':
      return { status: 'ok' }
    default:
      return null
  }
}

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

const routeProps = routerTestProps(
  '/election/:electionId/audit-board/:auditBoardId',
  {
    electionId: '1',
    auditBoardId: 'audit-board-1',
  }
)

const { history: staticHistory, ...staticRouteProps } = routeProps // eslint-disable-line @typescript-eslint/no-unused-vars

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

      const { container, findByText } = render(
        <StaticRouter {...staticRouteProps}>
          <DataEntry {...routeProps} />
        </StaticRouter>
      )
      await findByText('Audit Board #2: Member Sign-in')
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
      const { container, getByText, findAllByLabelText } = render(
        <StaticRouter {...staticRouteProps}>
          <DataEntry {...routeProps} />
        </StaticRouter>
      )

      const nameInputs = await findAllByLabelText('Full Name')
      expect(apiMock).toBeCalledTimes(1)
      expect(nameInputs).toHaveLength(2)

      nameInputs.forEach((nameInput, i) =>
        fireEvent.change(nameInput, { target: { value: `Name ${i}` } })
      )
      fireEvent.click(getByText('Next'), { bubbles: true })

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(1 + 4)
        expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
        expect(container).toMatchSnapshot()
      })
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
      const { container } = render(
        <StaticRouter {...staticRouteProps}>
          <DataEntry {...routeProps} />
        </StaticRouter>
      )
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with ballots', async () => {
      const { container, getByText } = render(
        <StaticRouter {...staticRouteProps}>
          <DataEntry {...routeProps} />
        </StaticRouter>
      )
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
        expect(getByText('Start Auditing').closest('a')).toBeEnabled()
        expect(
          getByText('Auditing Complete - Submit Results').closest('a')
        ).toHaveAttribute('disabled') // eslint-disable-line jest-dom/prefer-enabled-disabled
        expect(container).toMatchSnapshot()
      })
    })

    it('renders board table with large container size', async () => {
      jest
        .spyOn(window.document, 'getElementsByClassName')
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .mockReturnValue([{ clientWidth: 2000 }] as any)
      const { container } = render(
        <StaticRouter {...staticRouteProps}>
          <DataEntry {...routeProps} />
        </StaticRouter>
      )
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(container).toMatchSnapshot()
      })
    })

    it('renders ballot route', async () => {
      const ballotRouteProps = routerTestProps(
        '/election/:electionId/audit-board/:auditBoardId/batch/:batchId/ballot/:ballotPosition',
        {
          electionId: '1',
          auditBoardId: 'audit-board-1',
          batchId: 'batch-id-1',
          ballotPosition: '2112',
        }
      )
      const { history, ...staticBallotRouteProps } = ballotRouteProps // eslint-disable-line @typescript-eslint/no-unused-vars
      ballotRouteProps.match.url = '/election/1/audit-board/audit-board-1'
      const { container, getByText } = render(
        <StaticRouter {...staticBallotRouteProps}>
          <DataEntry {...ballotRouteProps} />
        </StaticRouter>
      )
      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(3)
        expect(getByText('Enter Ballot Information')).toBeTruthy()
        expect(container).toMatchSnapshot()
      })
    })

    it('advances ballot forward and backward', async () => {
      const ballotRouteProps = routerTestProps(
        '/election/:electionId/audit-board/:auditBoardId/batch/:batchId/ballot/:ballotPosition',
        {
          electionId: '1',
          auditBoardId: 'audit-board-1',
          batchId: 'batch-id-1',
          ballotPosition: '2112',
        }
      )
      const { history, ...staticBallotRouteProps } = ballotRouteProps // eslint-disable-line @typescript-eslint/no-unused-vars
      const pushSpy = jest
        .spyOn(ballotRouteProps.history, 'push')
        .mockImplementation()
      ballotRouteProps.match.url = '/election/1/audit-board/audit-board-1'
      const { findByText, getByText } = render(
        <StaticRouter {...staticBallotRouteProps}>
          <DataEntry {...ballotRouteProps} />
        </StaticRouter>
      )

      fireEvent.click(
        await findByText('Ballot 2112 not found - move to next ballot'),
        {
          bubbles: true,
        }
      )
      await waitFor(() => {
        expect(pushSpy).toBeCalledTimes(1)
      })

      fireEvent.click(getByText('Back'), { bubbles: true })
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
      const ballotRouteProps = routerTestProps(
        '/election/:electionId/audit-board/:auditBoardId/batch/:batchId/ballot/:ballotPosition',
        {
          electionId: '1',
          auditBoardId: 'audit-board-1',
          batchId: 'batch-id-1',
          ballotPosition: '2112',
        }
      )
      const { history, ...staticBallotRouteProps } = ballotRouteProps // eslint-disable-line @typescript-eslint/no-unused-vars
      ballotRouteProps.match.url = '/election/1/audit-board/audit-board-1'
      const { getByText, findByTestId, getByTestId } = render(
        <StaticRouter {...staticBallotRouteProps}>
          <DataEntry {...ballotRouteProps} />
        </StaticRouter>
      )

      fireEvent.click(await findByTestId('choice-id-1'), { bubbles: true })
      await waitFor(() =>
        fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
      )
      await waitFor(() => {
        fireEvent.click(getByText('Submit & Next Ballot'), { bubbles: true })
      })

      await waitFor(() => {
        expect(apiMock).toBeCalledTimes(5)
        expect(history.location.pathname).toBe(
          '/election/1/audit-board/audit-board-1/batch/batch-id-1/ballot/1789'
        )
      })
    })
  })
})
