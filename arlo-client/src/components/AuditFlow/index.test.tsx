import React from 'react'
import { render, wait, fireEvent } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'
import { dummyBoard, dummyBallots } from './_mocks'
import statusStates from '../AuditForms/_mocks'
import * as utilities from '../utilities'
import { IAudit, IBallot } from '../../types'

const memberDummy = statusStates[3]

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const ballotingMock = async (
  endpoint: string
): Promise<IAudit | { ballots: IBallot[] }> => {
  switch (endpoint) {
    case '/audit/status':
      memberDummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
      return memberDummy
    default:
      return dummyBallots
  }
}

afterEach(() => {
  apiMock.mockClear()
})

const routeProps = routerTestProps('/election/:electionId/board/:token', {
  electionId: '1',
  token: '123',
})

const { history, ...staticRouteProps } = routeProps

describe('AuditFlow ballot interaction', () => {
  beforeEach(() => {
    apiMock.mockImplementation(ballotingMock)
  })

  it('renders board table with no ballots', async () => {
    const { queryByText, container } = render(
      <StaticRouter {...staticRouteProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(container).toMatchSnapshot()
      expect(queryByText('Start Auditing')).toBeFalsy()
    })
  })

  it('renders board table with ballots', async () => {
    const { container, getByText } = render(
      <StaticRouter {...staticRouteProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalledTimes(2)
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(getByText('Start Auditing')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders board table with large container size', async () => {
    ;(jest
      .spyOn(window.document, 'getElementsByClassName')
      .mockReturnValue([
        { clientWidth: 2000 },
      ] as any) as any) as jest.SpyInstance<[{ clientWidth: number }]>
    const { container } = render(
      <StaticRouter {...staticRouteProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(container).toMatchSnapshot()
    })
  })

  it('renders ballot route', async () => {
    const ballotRouteProps = routerTestProps(
      '/election/:electionId/board/:token/round/:roundId/batch/:batchId/ballot/:ballotId',
      {
        electionId: '1',
        token: '123',
        roundId: '1',
        batchId: 'batch-id-1',
        ballotId: '313',
      }
    )
    const { history, ...staticBallotRouteProps } = ballotRouteProps
    ballotRouteProps.match.url = '/election/1/board/123'
    const { container, getByText } = render(
      <StaticRouter {...staticBallotRouteProps}>
        <AuditFlow {...ballotRouteProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Enter Ballot Information')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('advances ballot forward and backward', async () => {
    const ballotRouteProps = routerTestProps(
      '/election/:electionId/board/:token/round/:roundId/batch/:batchId/ballot/:ballotId',
      {
        electionId: '1',
        token: '123',
        roundId: '1',
        batchId: 'batch-id-1',
        ballotId: '2112',
      }
    )
    const { history, ...staticBallotRouteProps } = ballotRouteProps
    const pushSpy = jest
      .spyOn(ballotRouteProps.history, 'push')
      .mockImplementation()
    ballotRouteProps.match.url = '/election/1/board/123'
    const { getByText } = render(
      <StaticRouter {...staticBallotRouteProps}>
        <AuditFlow {...ballotRouteProps} />
      </StaticRouter>
    )

    fireEvent.click(getByText('Ballot 2112 not found - move to next ballot'), {
      bubbles: true,
    })
    await wait(() => {
      expect(pushSpy).toBeCalledTimes(1)
    })

    fireEvent.click(getByText('Back'), { bubbles: true })
    await wait(() => {
      expect(pushSpy).toBeCalledTimes(2)
    })

    expect(pushSpy.mock.calls[0][0]).toBe(
      '/election/1/board/123/round/1/batch/batch-id-1/ballot/1789'
    )
    expect(pushSpy.mock.calls[1][0]).toBe(
      '/election/1/board/123/round/1/batch/batch-id-1/ballot/313'
    )
  })

  it('submits ballot', async () => {
    const ballotRouteProps = routerTestProps(
      '/election/:electionId/board/:token/round/:roundId/batch/:batchId/ballot/:ballotId',
      {
        electionId: '1',
        token: '123',
        roundId: '1',
        batchId: 'batch-id-1',
        ballotId: '2112',
      }
    )
    const { history, ...staticBallotRouteProps } = ballotRouteProps
    ballotRouteProps.match.url = '/election/1/board/123'
    const { getByText, getByTestId } = render(
      <StaticRouter {...staticBallotRouteProps}>
        <AuditFlow {...ballotRouteProps} />
      </StaticRouter>
    )

    fireEvent.click(getByTestId('YES'), { bubbles: true })
    await wait(() =>
      fireEvent.click(getByTestId('enabled-review'), { bubbles: true })
    )
    await wait(() => {
      fireEvent.click(getByText('Submit & Next Ballot'), { bubbles: true })
    })

    await wait(() => {
      expect(apiMock).toBeCalledTimes(4)
    })
  })
})
