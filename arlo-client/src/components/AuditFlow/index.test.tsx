import React from 'react'
import { render, wait, fireEvent } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'
import { dummyBoard, dummyBallots } from './_mocks'
import statusStates from '../AuditForms/_mocks'
import { api } from '../utilities'

const dummy = statusStates[3]
dummy.jurisdictions[0].auditBoards = [dummyBoard[0]]

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

apiMock
  .mockImplementationOnce(async () => dummy)
  .mockImplementationOnce(async () => dummyBallots)

afterEach(() => {
  apiMock.mockClear()
})

const routeProps = routerTestProps('/election/:electionId/board/:token', {
  electionId: '1',
  token: '123',
})

describe('AuditFlow', () => {
  it('renders correctly', () => {
    const { container } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    expect(container).toMatchSnapshot()
  })

  it('fetches initial state from api', async () => {
    const { container } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders member form', async () => {
    const { container, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(
        getByText('Member Sign in for Audit Board: Audit Board #1')
      ).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders board table with no ballots', async () => {
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    const { queryByText, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(queryByText('Start Auditing')).toBeFalsy()
    })
  })

  it('renders board table with ballots', async () => {
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    const { container, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(getByText('Start Auditing')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders board table with large container size', async () => {
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    ;(jest
      .spyOn(window.document, 'getElementsByClassName')
      .mockReturnValue([
        { clientWidth: 2000 },
      ] as any) as any) as jest.SpyInstance<[{ clientWidth: number }]>
    const { container } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(container).toMatchSnapshot()
    })
  })

  it('renders board table with completed ballots', async () => {
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    const { container, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow {...routeProps} />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(getByText('Review Complete - Finish Round')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders ballot route', async () => {
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    const ballotRouteProps = routerTestProps(
      '/election/:electionId/board/:token/round/:roundId/batch/:batchId/ballot/:ballotId',
      {
        electionId: '1',
        token: '123',
        roundId: '1',
        batchId: 'batch-id',
        ballotId: '313',
      }
    )
    ballotRouteProps.match.url = '/election/1/board/123'
    const { container, getByText } = render(
      <StaticRouter {...ballotRouteProps}>
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
    dummy.jurisdictions[0].auditBoards = [dummyBoard[1]]
    const ballotRouteProps = routerTestProps(
      '/election/:electionId/board/:token/round/:roundId/batch/:batchId/ballot/:ballotId',
      {
        electionId: '1',
        token: '123',
        roundId: '1',
        batchId: 'batch-id',
        ballotId: '313',
      }
    )
    const pushSpy = jest
      .spyOn(ballotRouteProps.history, 'push')
      .mockImplementation()
    ballotRouteProps.match.url = '/election/1/board/123'
    const { getByText } = render(
      <StaticRouter {...ballotRouteProps}>
        <AuditFlow {...ballotRouteProps} />
      </StaticRouter>
    )

    fireEvent.click(getByText('Ballot 313 not found - move to next ballot'), {
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
      '/election/1/board/123/round/1/batch/batch-id/ballot/2112'
    )
    expect(pushSpy.mock.calls[1][0]).toBe(
      '/election/1/board/123/round/1/batch/batch-id/ballot/313'
    )
  })
})
