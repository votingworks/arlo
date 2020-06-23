import React from 'react'
import { render, waitFor } from '@testing-library/react'
import { BrowserRouter as Router } from 'react-router-dom'
import Header from './Header'
import * as utilities from './utilities'
import AuthDataProvider from './UserContext'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: () => ({
    url: '/election/1',
    params: {
      electionId: '1',
    },
  }),
}))

checkAndToastMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
})

describe('Header', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Router>
        <Header />
      </Router>
    )
    expect(container).toMatchSnapshot()
  })

  it('shows the logout button when authenticated', async () => {
    apiMock.mockImplementation(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [],
    }))
    const { findByText } = render(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    await findByText('Log out')
    expect(apiMock).toHaveBeenCalledTimes(1)
    expect(apiMock).toHaveBeenCalledWith('/me')
  })

  it('does not show logout button if not authenticated', async () => {
    apiMock.mockRejectedValue(async () => ({}))
    const { queryByText } = render(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    const loginButton = queryByText('Log out')
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/me')
      expect(loginButton).toBeFalsy()
    })
  })

  it('does not show logout button if the authentication verification has a server error', async () => {
    checkAndToastMock.mockReturnValue(true)
    apiMock.mockRejectedValue(async () => ({}))
    const { queryByText } = render(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )

    const loginButton = queryByText('Log out')
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock).toHaveBeenCalledWith('/me')
      expect(loginButton).toBeFalsy()
    })
  })

  it('shows the nav bar when authenticated and there is an electionId', async () => {
    checkAndToastMock.mockReturnValue(false)
    apiMock.mockImplementation(async () => ({
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [],
    }))
    const { container, getByText } = render(
      <Router>
        <AuthDataProvider>
          <Header />
        </AuthDataProvider>
      </Router>
    )
    await waitFor(() => {
      expect(getByText('Audit Setup')).toBeTruthy()
      expect(getByText('Audit Progress')).toBeTruthy()
      expect(getByText('View Audits')).toBeTruthy()
      expect(getByText('New Audit')).toBeTruthy()
      expect(container).toMatchSnapshot()
    })
  })
})
