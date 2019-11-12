import React from 'react'
import { render, wait } from '@testing-library/react'
import { Router } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'
import { dummyBoard, dummyBallots } from './_mocks'
import statusStates from '../AuditForms/_mocks'
import { api } from '../utilities'
import { IAudit, IBallot } from '../../types'

const memberlessDummy = statusStates[3]

const apiMock = api as jest.Mock<ReturnType<typeof api>, Parameters<typeof api>>

jest.mock('../utilities')

const memberingMock = async (
  endpoint: string
): Promise<IAudit | { ballots: IBallot[] }> => {
  switch (endpoint) {
    case '/audit/status':
      memberlessDummy.jurisdictions[0].auditBoards = [dummyBoard[0]]
      return memberlessDummy
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

describe('AuditFlow initial load', () => {
  beforeEach(() => {
    apiMock.mockImplementation(memberingMock)
  })

  it('renders correctly', () => {
    const { container } = render(
      <Router {...routeProps}>
        <AuditFlow {...routeProps} />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('fetches initial state from api', async () => {
    const { container } = render(
      <Router {...routeProps}>
        <AuditFlow {...routeProps} />
      </Router>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(container).toMatchSnapshot()
    })
  })

  it('renders member form', async () => {
    const { container, getByText } = render(
      <Router {...routeProps}>
        <AuditFlow {...routeProps} />
      </Router>
    )
    await wait(() => {
      expect(apiMock).toBeCalled()
      expect(
        getByText('Member Sign in for Audit Board: Audit Board #1')
      ).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })
})
