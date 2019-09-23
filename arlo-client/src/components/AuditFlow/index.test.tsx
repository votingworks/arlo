import React from 'react'
import { render, wait } from '@testing-library/react'
import { StaticRouter } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'
import { dummyBoard } from './_mocks'
import statusStates from '../AuditForms/_mocks'
import api from '../utilities'

const dummy = (i: number) => {
  statusStates[3].jurisdictions[0].auditBoards = [dummyBoard[i]]
  return statusStates[3]
}

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

apiMock.mockImplementation(async () => dummy(0))

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
    apiMock.mockImplementationOnce(async () => dummy(0))
    const { container, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow
          {...routeProps}
          dummyID={0}
          testName="member form: dummy 0"
        />
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
    apiMock.mockImplementationOnce(async () => dummy(1))
    const { queryByText, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow
          {...routeProps}
          dummyID={1}
          testName="blank board table: dummy 1"
        />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(queryByText('Start Auditing')).toBeFalsy()
    })
  })

  it('renders board table with ballots', async () => {
    apiMock.mockImplementationOnce(async () => dummy(2))
    const { container, getByText } = render(
      <StaticRouter {...routeProps}>
        <AuditFlow
          {...routeProps}
          dummyID={2}
          testName="board table: dummy 1"
        />
      </StaticRouter>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(getByText('Audit Board #1: Ballot Cards to Audit')).toBeTruthy()
      expect(getByText('Start Auditing')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })
})
